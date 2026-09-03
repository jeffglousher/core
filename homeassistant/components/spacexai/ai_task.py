"""AI Task support for SpaceXAI."""

from json import JSONDecodeError
from typing import Any, override

from probatio import to_openapi
from spacexai_subscription_client import (
    Attachment,
    AuthenticationError,
    InvalidResponseError,
    ResponseFormat,
    SpaceXAISubscriptionError,
)

from homeassistant.components import ai_task, conversation
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, llm
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import slugify
from homeassistant.util.json import json_loads

from .const import DOMAIN, LOGGER, RECOMMENDED_IMAGE_MODEL
from .conversation import _async_convert_content, _prepare_attachments
from .entity import async_access_token
from .models import SpaceXAIConfigEntry

PARALLEL_UPDATES = 0
MAX_EDIT_IMAGES = 5
IMAGE_MEDIA_TYPES = ("image/jpeg", "image/png")


def _adjust_schema(schema: dict[str, Any]) -> None:
    """Make a JSON schema compatible with strict structured output."""
    if schema["type"] == "object":
        schema.setdefault("additionalProperties", False)
        properties = schema.get("properties")
        if not properties:
            return
        required = schema.setdefault("required", [])
        for name, prop_info in properties.items():
            _adjust_schema(prop_info)
            if name not in required:
                prop_info["type"] = [prop_info["type"], "null"]
                required.append(name)
    elif schema["type"] == "array" and "items" in schema:
        _adjust_schema(schema["items"])


def _format_response_format(
    task: ai_task.GenDataTask, chat_log: conversation.ChatLog
) -> ResponseFormat | None:
    """Convert an optional Home Assistant result structure."""
    if task.structure is None:
        return None
    schema: dict[str, Any] = to_openapi(
        task.structure,
        custom_serializer=(
            chat_log.llm_api.custom_serializer
            if chat_log.llm_api
            else llm.selector_serializer
        ),
    )
    _adjust_schema(schema)
    return ResponseFormat(slugify(task.name) or "task", schema)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SpaceXAIConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpaceXAI AI Task entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "ai_task_data":
            continue
        async_add_entities(
            [SpaceXAIAITaskEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class SpaceXAIAITaskEntity(ai_task.AITaskEntity):
    """SpaceXAI AI Task entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_supported_features = (
        ai_task.AITaskEntityFeature.GENERATE_DATA
        | ai_task.AITaskEntityFeature.GENERATE_IMAGE
        | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
    )

    def __init__(self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the AI Task entity."""
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = subentry.subentry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="SpaceXAI",
            model=subentry.data[CONF_MODEL],
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @override
    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Generate unstructured or structured data."""
        try:
            response = await self.entry.runtime_data.client.async_create_response(
                await async_access_token(self.hass, self.entry),
                model=self.subentry.data[CONF_MODEL],
                input_data=await _async_convert_content(self.hass, chat_log.content),
                tools=[],
                response_format=_format_response_format(task, chat_log),
            )
        except AuthenticationError as err:
            self.entry.async_start_reauth(self.hass)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
            ) from err
        except InvalidResponseError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_response",
            ) from err
        except SpaceXAISubscriptionError as err:
            LOGGER.error("Error communicating with SpaceXAI: %s", type(err).__name__)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
            ) from err

        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=self.entity_id,
                content=response.text,
            )
        )
        data: Any = response.text
        if task.structure is not None:
            try:
                data = json_loads(response.text)
            except JSONDecodeError as err:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_structured_response",
                ) from err
        return ai_task.GenDataTaskResult(chat_log.conversation_id, data)

    @override
    async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Generate or edit an image."""
        attachments = await self._async_prepare_image_attachments(task)
        access_token = await async_access_token(self.hass, self.entry)
        try:
            if attachments:
                image = await self.entry.runtime_data.client.async_edit_image(
                    access_token,
                    model=RECOMMENDED_IMAGE_MODEL,
                    prompt=task.instructions,
                    images=attachments,
                )
            else:
                image = await self.entry.runtime_data.client.async_generate_image(
                    access_token,
                    model=RECOMMENDED_IMAGE_MODEL,
                    prompt=task.instructions,
                )
        except AuthenticationError as err:
            self.entry.async_start_reauth(self.hass)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
            ) from err
        except InvalidResponseError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_response",
            ) from err
        except SpaceXAISubscriptionError as err:
            LOGGER.error("Error communicating with SpaceXAI: %s", type(err).__name__)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
            ) from err

        return ai_task.GenImageTaskResult(
            image_data=image.data,
            conversation_id=chat_log.conversation_id,
            mime_type=image.media_type,
            model=image.model,
            revised_prompt=image.revised_prompt,
        )

    async def _async_prepare_image_attachments(
        self, task: ai_task.GenImageTask
    ) -> tuple[Attachment, ...]:
        """Load and validate image-edit attachments."""
        if not task.attachments:
            return ()
        if len(task.attachments) > MAX_EDIT_IMAGES:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="too_many_image_attachments",
            )
        attachments = await self.hass.async_add_executor_job(
            _prepare_attachments,
            [(item.path, item.mime_type) for item in task.attachments],
        )
        if any(item.media_type not in IMAGE_MEDIA_TYPES for item in attachments):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_image_attachment",
            )
        return attachments
