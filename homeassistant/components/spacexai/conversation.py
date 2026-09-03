"""Conversation support for SpaceXAI."""

from collections.abc import AsyncGenerator, Callable, Iterable
from pathlib import Path
from typing import Any, Literal, override

from probatio import to_openapi
from spacexai_subscription_client import (
    Attachment,
    AuthenticationError,
    BuiltinTool,
    Completion,
    InputItem,
    InvalidResponseError,
    Message,
    ResponseTool,
    SpaceXAISubscriptionError,
    Tool,
    ToolCall,
    ToolResult,
)

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_LLM_HASS_API, CONF_MODEL, CONF_PROMPT, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, llm
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.json import json_dumps

from .const import (
    CONF_CODE_INTERPRETER,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    DOMAIN,
    LOGGER,
    MAX_ATTACHMENT_SIZE,
    MAX_TOOL_ITERATIONS,
)
from .entity import async_access_token
from .models import SpaceXAIConfigEntry

PARALLEL_UPDATES = 0


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> Tool:
    """Convert a Home Assistant tool to a client tool."""
    return Tool(
        tool.name,
        tool.description,
        to_openapi(
            tool.parameters,
            custom_serializer=custom_serializer,
        ),
    )


def _convert_content(
    chat_content: Iterable[conversation.Content],
) -> list[InputItem]:
    """Convert Home Assistant chat content to client input."""
    messages: list[InputItem] = []
    for content in chat_content:
        if isinstance(content, conversation.ToolResultContent):
            messages.append(
                ToolResult(
                    content.tool_call_id,
                    json_dumps(content.tool_result),
                )
            )
            continue
        if content.content or (
            isinstance(content, conversation.UserContent) and content.attachments
        ):
            role: Literal["user", "assistant", "system", "developer"] = content.role
            if role == "system":
                role = "developer"
            messages.append(Message(role, content.content or ""))
        if isinstance(content, conversation.AssistantContent):
            messages.extend(
                ToolCall(
                    tool_call.id,
                    tool_call.tool_name,
                    tool_call.tool_args,
                )
                for tool_call in content.tool_calls or ()
            )
    return messages


async def _async_convert_content(
    hass: HomeAssistant, chat_content: Iterable[conversation.Content]
) -> list[InputItem]:
    """Convert chat content and load attachments from the latest user message."""
    contents = list(chat_content)
    messages = _convert_content(contents)
    if not contents:
        return messages

    last_content = contents[-1]
    if not isinstance(last_content, conversation.UserContent) or not (
        attachments := last_content.attachments
    ):
        return messages

    if not messages or not isinstance(messages[-1], Message):
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="user_message_not_found",
        )
    last_message = messages[-1]
    if last_message.role != "user":
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="user_message_not_found",
        )

    prepared = await hass.async_add_executor_job(
        _prepare_attachments,
        [(item.path, item.mime_type) for item in attachments],
    )
    messages[-1] = Message(last_message.role, last_message.content, prepared)
    return messages


def _prepare_attachments(files: list[tuple[Path, str]]) -> tuple[Attachment, ...]:
    """Read and validate attachments."""
    attachments: list[Attachment] = []
    total_size = 0
    for path, media_type in files:
        if media_type == "image/jpg":
            media_type = "image/jpeg"
        if media_type not in ("image/jpeg", "image/png", "application/pdf"):
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_attachment",
                translation_placeholders={"filename": path.name},
            )
        try:
            size = path.stat().st_size
            if size == 0:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="attachment_empty",
                    translation_placeholders={"filename": path.name},
                )
            if total_size + size > MAX_ATTACHMENT_SIZE:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="attachment_too_large",
                    translation_placeholders={"filename": path.name},
                )
            data = path.read_bytes()
        except OSError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="attachment_unavailable",
                translation_placeholders={"filename": path.name},
            ) from err
        if not data:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="attachment_empty",
                translation_placeholders={"filename": path.name},
            )
        total_size += len(data)
        if total_size > MAX_ATTACHMENT_SIZE:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="attachment_too_large",
                translation_placeholders={"filename": path.name},
            )
        attachments.append(Attachment(path.name, media_type, data))
    return tuple(attachments)


def _tool_input(tool_call: ToolCall) -> llm.ToolInput:
    """Convert a client tool call to Home Assistant input."""
    return llm.ToolInput(
        id=tool_call.id,
        tool_name=tool_call.name,
        tool_args=dict(tool_call.arguments),
    )


async def _transform_response(
    response: Completion,
) -> AsyncGenerator[conversation.AssistantContentDeltaDict]:
    """Transform a client response to Home Assistant content."""
    tool_calls = [_tool_input(item) for item in response.tool_calls]
    yield {
        "role": "assistant",
        "content": response.text or None,
        "tool_calls": tool_calls or None,
    }


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SpaceXAIConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpaceXAI conversation entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "conversation":
            continue
        async_add_entities(
            [SpaceXAIConversationEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class SpaceXAIConversationEntity(
    conversation.ConversationEntity,
    conversation.AbstractConversationAgent,
):
    """SpaceXAI conversation agent."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the conversation agent."""
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
        if subentry.data.get(CONF_LLM_HASS_API):
            self._attr_supported_features = (
                conversation.ConversationEntityFeature.CONTROL
            )

    @property
    @override
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return supported languages."""
        return MATCH_ALL

    @override
    async def _async_handle_message(
        self,
        user_input: conversation.ConversationInput,
        chat_log: conversation.ChatLog,
    ) -> conversation.ConversationResult:
        """Process a conversation message."""
        try:
            await chat_log.async_provide_llm_data(
                user_input.as_llm_context(DOMAIN),
                self.subentry.data.get(CONF_LLM_HASS_API),
                self.subentry.data.get(CONF_PROMPT),
                user_input.extra_system_prompt,
            )
        except conversation.ConverseError as err:
            return err.as_conversation_result()

        await self._async_handle_chat_log(chat_log)
        return conversation.async_get_result_from_chat_log(user_input, chat_log)

    async def _async_handle_chat_log(self, chat_log: conversation.ChatLog) -> None:
        """Send the chat log to SpaceXAI and execute Home Assistant tools."""
        tools: list[ResponseTool] = []
        if chat_log.llm_api:
            tools = [
                _format_tool(tool, chat_log.llm_api.custom_serializer)
                for tool in chat_log.llm_api.tools
            ]
        if self.subentry.data.get(CONF_WEB_SEARCH):
            tools.append(BuiltinTool("web_search"))
        if self.subentry.data.get(CONF_X_SEARCH):
            tools.append(BuiltinTool("x_search"))
        if self.subentry.data.get(CONF_CODE_INTERPRETER):
            tools.append(BuiltinTool("code_interpreter"))

        for _iteration in range(MAX_TOOL_ITERATIONS):
            try:
                response = await self.entry.runtime_data.client.async_create_response(
                    await async_access_token(self.entry),
                    model=self.subentry.data[CONF_MODEL],
                    input_data=await _async_convert_content(
                        self.hass, chat_log.content
                    ),
                    tools=tools,
                )
            except AuthenticationError as err:
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
                LOGGER.error(
                    "Error communicating with SpaceXAI: %s", type(err).__name__
                )
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="api_error",
                ) from err

            async for _content in chat_log.async_add_delta_content_stream(
                self.entity_id, _transform_response(response)
            ):
                pass
            if not chat_log.unresponded_tool_results:
                return

        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="tool_iteration_limit",
        )
