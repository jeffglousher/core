"""AI Task platform for SpaceXAI."""

import base64
from json import JSONDecodeError
from pathlib import Path
from typing import override

from homeassistant.components import ai_task, conversation
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util.json import json_loads

from . import SpaceXAIConfigEntry
from .const import (
    CONF_IMAGE_ASPECT_RATIO,
    CONF_IMAGE_MODEL,
    CONF_IMAGE_RESOLUTION,
    DEFAULT_IMAGE_ASPECT_RATIO,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_IMAGE_RESOLUTION,
    DOMAIN,
    LOGGER,
    MAX_AI_TASK_TOOL_ITERATIONS,
    MAX_IMAGE_BYTES,
)
from .entity import SpaceXAIBaseLLMEntity
from .errors import ErrorContext, ModelNotEntitledError, Operation, SpaceXAIError

PARALLEL_UPDATES = 0


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
            [SpaceXAITaskEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class SpaceXAITaskEntity(ai_task.AITaskEntity, SpaceXAIBaseLLMEntity):
    """SpaceXAI AI Task entity."""

    _attr_supported_features = (
        ai_task.AITaskEntityFeature.GENERATE_DATA
        | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
        | ai_task.AITaskEntityFeature.GENERATE_IMAGE
    )
    _attr_translation_key = "ai_task_data"

    @override
    async def _async_generate_data(
        self,
        task: ai_task.GenDataTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenDataTaskResult:
        """Handle a generate data task."""
        availability_epoch, availability_epochs, subscription_epoch = (
            self._capture_availability_context()
        )
        try:
            await self._async_handle_chat_log(
                chat_log,
                task.name,
                task.structure,
                max_iterations=MAX_AI_TASK_TOOL_ITERATIONS,
            )
        except SpaceXAIError as err:
            self._raise_provider_home_assistant_error(err)
        except HomeAssistantError:
            # Already carries a translated, actionable message.
            raise
        except Exception as err:  # noqa: BLE001
            self._raise_unexpected_provider_failure(err)

        self._recover_after_success(
            availability_epoch, availability_epochs, subscription_epoch
        )

        if not isinstance(chat_log.content[-1], conversation.AssistantContent):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="response_not_found",
            )

        text = chat_log.content[-1].content or ""
        if not task.structure:
            return ai_task.GenDataTaskResult(
                conversation_id=chat_log.conversation_id,
                data=text,
            )

        try:
            data = json_loads(text)
        except JSONDecodeError as err:
            LOGGER.error("Failed to parse JSON response: %s. Response: %s", err, text)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="json_parse_error",
            ) from err

        return ai_task.GenDataTaskResult(
            conversation_id=chat_log.conversation_id,
            data=data,
        )

    @override
    async def _async_generate_image(
        self,
        task: ai_task.GenImageTask,
        chat_log: conversation.ChatLog,
    ) -> ai_task.GenImageTaskResult:
        """Handle a generate or edit image task via the Imagine API."""
        user_message = chat_log.content[-1]
        assert isinstance(user_message, conversation.UserContent)
        image_model = self.subentry.data.get(CONF_IMAGE_MODEL, DEFAULT_IMAGE_MODEL)
        snapshot = self.entry.runtime_data.snapshot
        if not snapshot.has_image_model(image_model):
            self._raise_provider_home_assistant_error(
                ModelNotEntitledError(
                    "The account is not entitled to the configured image model",
                    context=ErrorContext(operation=Operation.IMAGE, model=image_model),
                )
            )

        aspect_ratio = self.subentry.data.get(
            CONF_IMAGE_ASPECT_RATIO, DEFAULT_IMAGE_ASPECT_RATIO
        )
        resolution = self.subentry.data.get(
            CONF_IMAGE_RESOLUTION, DEFAULT_IMAGE_RESOLUTION
        )
        image_attachments = [
            attachment
            for attachment in (user_message.attachments or ())
            if attachment.mime_type and attachment.mime_type.startswith("image/")
        ]
        reference_uris = [
            await self.hass.async_add_executor_job(
                _attachment_data_uri, attachment.path, attachment.mime_type
            )
            for attachment in image_attachments[:3]
        ]

        availability_epoch, availability_epochs, subscription_epoch = (
            self._capture_availability_context()
        )
        try:
            if reference_uris:
                generated = await self.entry.runtime_data.client.async_edit_image(
                    model=image_model,
                    prompt=user_message.content,
                    images=reference_uris[:3],
                )
            else:
                generated = await self.entry.runtime_data.client.async_generate_image(
                    model=image_model,
                    prompt=user_message.content,
                    aspect_ratio=aspect_ratio,
                    resolution=resolution,
                )
        except SpaceXAIError as err:
            self._raise_provider_home_assistant_error(err)
        except HomeAssistantError:
            # Already carries a translated, actionable message.
            raise
        except Exception as err:  # noqa: BLE001
            self._raise_unexpected_provider_failure(err)

        self._recover_after_success(
            availability_epoch, availability_epochs, subscription_epoch
        )
        chat_log.async_add_assistant_content_without_tools(
            conversation.AssistantContent(
                agent_id=self.entity_id,
                content=generated.revised_prompt or "",
            )
        )
        return ai_task.GenImageTaskResult(
            image_data=generated.image_data,
            conversation_id=chat_log.conversation_id,
            mime_type=generated.mime_type,
            model=generated.model,
            revised_prompt=generated.revised_prompt,
        )


def _attachment_data_uri(path: Path, mime_type: str) -> str:
    """Encode a local image attachment as a data URI."""
    size = path.stat().st_size
    if size > MAX_IMAGE_BYTES:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="attachment_too_large",
            translation_placeholders={
                "path": path.name,
                "max_mb": str(MAX_IMAGE_BYTES // (1024 * 1024)),
            },
        )
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime_type};base64,{encoded}"
