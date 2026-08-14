"""Shared SpaceXAI LLM entity helpers."""

from collections.abc import Callable, Iterable, Mapping
import traceback
from typing import Any, Literal, NoReturn, cast

import openai
from openai.types.responses import (
    EasyInputMessageParam,
    FunctionToolParam,
    ResponseFunctionToolCallParam,
    ResponseInputParam,
    ResponseReasoningItem,
    ResponseReasoningItemParam,
)
from openai.types.responses.response_code_interpreter_tool_call_param import (
    ResponseCodeInterpreterToolCallParam,
)
from openai.types.responses.response_function_web_search_param import (
    ResponseFunctionWebSearchParam,
)
from openai.types.responses.response_input_param import (
    FunctionCallOutput,
    ImageGenerationCall as ImageGenerationCallParam,
)
from openai.types.responses.response_output_item import ImageGenerationCall
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from pydantic import ValidationError
import voluptuous as vol
from voluptuous_openapi import convert

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_MODEL
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, issue_registry as ir, llm
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.json import json_dumps
from homeassistant.util import slugify

from . import ISSUE_MODEL_NOT_ENTITLED, SpaceXAIConfigEntry
from .const import (
    CONF_CODE_INTERPRETER,
    CONF_IMAGE_GENERATION,
    CONF_IMAGE_GENERATION_ACTION,
    CONF_MAX_OUTPUT_TOKENS,
    CONF_SERVICE_TIER,
    CONF_STORE_RESPONSES,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    CONF_WEB_SEARCH,
    CONF_WEB_SEARCH_ALLOWED_DOMAINS,
    CONF_WEB_SEARCH_EXCLUDED_DOMAINS,
    CONF_WEB_SEARCH_IMAGE_SEARCH,
    CONF_WEB_SEARCH_IMAGE_UNDERSTANDING,
    CONF_X_SEARCH,
    CONF_X_SEARCH_ALLOWED_HANDLES,
    CONF_X_SEARCH_EXCLUDED_HANDLES,
    CONF_X_SEARCH_FROM_DATE,
    CONF_X_SEARCH_IMAGE_UNDERSTANDING,
    CONF_X_SEARCH_TO_DATE,
    CONF_X_SEARCH_VIDEO_UNDERSTANDING,
    DEFAULT_AI_TASK_SERVICE_TIER,
    DEFAULT_CODE_INTERPRETER,
    DEFAULT_IMAGE_GENERATION,
    DEFAULT_IMAGE_GENERATION_ACTION,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL_PLACEHOLDER,
    DEFAULT_SERVICE_TIER,
    DEFAULT_STORE_RESPONSES,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_WEB_SEARCH,
    DEFAULT_X_SEARCH,
    DOMAIN,
    LOGGER,
    MAX_TOOL_ITERATIONS,
    PROVIDER_CODE_INTERPRETER_TOOL,
    PROVIDER_SEARCH_TOOLS,
)
from .errors import (
    ErrorCategory,
    ErrorContext,
    Operation,
    RateLimitedError,
    RequestTimeoutError,
    SpaceXAIError,
    ToolLoopLimitError,
)
from .files import async_prepare_files_for_prompt
from .stream import _transform_stream


def _adjust_schema(schema: dict[str, Any]) -> None:
    """Adjust a JSON schema for Responses API structured output."""
    if schema["type"] == "object":
        schema.setdefault("strict", True)
        schema.setdefault("additionalProperties", False)
        if "properties" not in schema:
            return

        if "required" not in schema:
            schema["required"] = []

        for prop, prop_info in schema["properties"].items():
            _adjust_schema(prop_info)
            if prop not in schema["required"]:
                prop_info["type"] = [prop_info["type"], "null"]
                schema["required"].append(prop)

    elif schema["type"] == "array":
        if "items" not in schema:
            return
        _adjust_schema(schema["items"])


def _format_structured_output(
    schema: vol.Schema, llm_api: llm.APIInstance | None
) -> dict[str, Any]:
    """Convert a Voluptuous schema into Responses API JSON schema."""
    result: dict[str, Any] = convert(
        schema,
        custom_serializer=(
            llm_api.custom_serializer if llm_api else llm.selector_serializer
        ),
    )
    _adjust_schema(result)
    return result


def _format_tool(
    tool: llm.Tool, custom_serializer: Callable[[Any], Any] | None
) -> FunctionToolParam:
    """Convert a Home Assistant LLM tool to a Responses API tool."""
    schema = convert(tool.parameters, custom_serializer=custom_serializer)
    return FunctionToolParam(
        type="function",
        name=tool.name,
        description=tool.description,
        parameters=schema,
        strict=False,
    )


def _provider_tools_from_subentry(data: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Build server-side provider tools from conversation subentry options."""
    tools: list[dict[str, Any]] = []

    if data.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH):
        web_search: dict[str, Any] = {"type": "web_search"}
        allowed_domains = list(data.get(CONF_WEB_SEARCH_ALLOWED_DOMAINS) or [])[:5]
        excluded_domains = list(data.get(CONF_WEB_SEARCH_EXCLUDED_DOMAINS) or [])[:5]
        if allowed_domains:
            web_search["filters"] = {"allowed_domains": allowed_domains}
        elif excluded_domains:
            web_search["filters"] = {"excluded_domains": excluded_domains}
        if data.get(CONF_WEB_SEARCH_IMAGE_UNDERSTANDING):
            web_search["enable_image_understanding"] = True
        if data.get(CONF_WEB_SEARCH_IMAGE_SEARCH):
            web_search["enable_image_search"] = True
        tools.append(web_search)

    if data.get(CONF_X_SEARCH, DEFAULT_X_SEARCH):
        x_search: dict[str, Any] = {"type": "x_search"}
        allowed_handles = list(data.get(CONF_X_SEARCH_ALLOWED_HANDLES) or [])[:20]
        excluded_handles = list(data.get(CONF_X_SEARCH_EXCLUDED_HANDLES) or [])[:20]
        if allowed_handles:
            x_search["allowed_x_handles"] = allowed_handles
        elif excluded_handles:
            x_search["excluded_x_handles"] = excluded_handles
        if from_date := data.get(CONF_X_SEARCH_FROM_DATE):
            x_search["from_date"] = from_date
        if to_date := data.get(CONF_X_SEARCH_TO_DATE):
            x_search["to_date"] = to_date
        if data.get(CONF_X_SEARCH_IMAGE_UNDERSTANDING):
            x_search["enable_image_understanding"] = True
        if data.get(CONF_X_SEARCH_VIDEO_UNDERSTANDING):
            x_search["enable_video_understanding"] = True
        tools.append(x_search)

    if data.get(CONF_CODE_INTERPRETER, DEFAULT_CODE_INTERPRETER):
        tools.append({"type": "code_interpreter"})

    if data.get(CONF_IMAGE_GENERATION, DEFAULT_IMAGE_GENERATION):
        tools.append(
            {
                "type": "image_generation",
                "action": data.get(
                    CONF_IMAGE_GENERATION_ACTION, DEFAULT_IMAGE_GENERATION_ACTION
                ),
            }
        )

    return tools


def _convert_content(
    chat_content: Iterable[conversation.Content],
) -> ResponseInputParam:
    """Convert Home Assistant-owned history to Responses API input."""
    messages: ResponseInputParam = []
    search_calls: dict[str, ResponseFunctionWebSearchParam] = {}
    code_calls: dict[str, ResponseCodeInterpreterToolCallParam] = {}
    for content in chat_content:
        if isinstance(content, conversation.ToolResultContent):
            if (
                content.tool_name in PROVIDER_SEARCH_TOOLS
                and content.tool_call_id in search_calls
            ):
                search_call = search_calls.pop(content.tool_call_id)
                search_call["status"] = content.tool_result.get(  # type: ignore[typeddict-item]
                    "status", "completed"
                )
                messages.append(search_call)
            elif (
                content.tool_name == PROVIDER_CODE_INTERPRETER_TOOL
                and content.tool_call_id in code_calls
            ):
                code_call = code_calls.pop(content.tool_call_id)
                code_call["outputs"] = content.tool_result.get("output")  # type: ignore[typeddict-item]
                messages.append(code_call)
            else:
                messages.append(
                    FunctionCallOutput(
                        type="function_call_output",
                        call_id=content.tool_call_id,
                        output=json_dumps(content.tool_result),
                    )
                )
            continue

        if isinstance(content, conversation.AssistantContent):
            if isinstance(content.native, ResponseReasoningItem):
                messages.append(
                    cast(ResponseReasoningItemParam, content.native.to_dict())
                )
            elif isinstance(content.native, ImageGenerationCall) or (
                content.native is not None
                and getattr(content.native, "type", None) == "image_generation_call"
            ):
                messages.append(
                    cast(ImageGenerationCallParam, content.native.to_dict())
                )
            if content.content:
                messages.append(
                    EasyInputMessageParam(
                        type="message",
                        role="assistant",
                        content=content.content,
                    )
                )
            for tool_call in content.tool_calls or ():
                if tool_call.tool_name in PROVIDER_SEARCH_TOOLS:
                    search_calls[tool_call.id] = cast(
                        ResponseFunctionWebSearchParam,
                        {
                            "type": tool_call.tool_name,
                            "id": tool_call.id,
                            "status": "completed",
                            "action": tool_call.tool_args.get("action"),
                        },
                    )
                elif tool_call.tool_name == PROVIDER_CODE_INTERPRETER_TOOL:
                    code_calls[tool_call.id] = ResponseCodeInterpreterToolCallParam(
                        type="code_interpreter_call",
                        id=tool_call.id,
                        code=tool_call.tool_args.get("code"),
                        container_id=str(tool_call.tool_args.get("container") or ""),
                        outputs=None,
                        status="completed",
                    )
                else:
                    messages.append(
                        ResponseFunctionToolCallParam(
                            type="function_call",
                            call_id=tool_call.id,
                            name=tool_call.tool_name,
                            arguments=json_dumps(tool_call.tool_args),
                        )
                    )
            continue

        role: Literal["system", "user"] = content.role
        messages.append(
            EasyInputMessageParam(
                type="message",
                role=role,
                content=content.content,
            )
        )
    return messages


class SpaceXAIBaseLLMEntity(Entity):
    """Shared SpaceXAI LLM entity behavior."""

    _attr_has_entity_name = True
    _attr_name: str | None = None

    def __init__(self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the shared LLM entity."""
        self.entry = entry
        self.subentry = subentry
        self._unavailable_logged = False
        # Speech entities are not backed by a language model.
        configured_model = CONF_MODEL in subentry.data
        model = cast(str, subentry.data.get(CONF_MODEL, DEFAULT_MODEL_PLACEHOLDER))
        self._attr_available = (
            entry.runtime_data.snapshot.has_model(model) if configured_model else True
        )
        self._attr_unique_id = subentry.subentry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="SpaceXAI",
            model=model,
            model_id=model if configured_model else None,
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def _model(self) -> str:
        """Return the configured model, or the brand name for speech entities."""
        return cast(str, self.subentry.data.get(CONF_MODEL, DEFAULT_MODEL_PLACEHOLDER))

    @property
    def _max_output_tokens(self) -> int:
        """Return the configured model output limit."""
        return cast(
            int,
            self.subentry.data.get(CONF_MAX_OUTPUT_TOKENS, DEFAULT_MAX_OUTPUT_TOKENS),
        )

    @property
    def _temperature(self) -> float:
        """Return the configured sampling temperature."""
        return float(self.subentry.data.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))

    @property
    def _top_p(self) -> float:
        """Return the configured nucleus sampling threshold."""
        return float(self.subentry.data.get(CONF_TOP_P, DEFAULT_TOP_P))

    @property
    def _store_responses(self) -> bool:
        """Return whether provider-side response storage is enabled."""
        return bool(
            self.subentry.data.get(CONF_STORE_RESPONSES, DEFAULT_STORE_RESPONSES)
        )

    @property
    def _service_tier(self) -> str:
        """Return the configured xAI service tier (default or priority)."""
        default = (
            DEFAULT_AI_TASK_SERVICE_TIER
            if self.subentry.subentry_type == "ai_task_data"
            else DEFAULT_SERVICE_TIER
        )
        return cast(str, self.subentry.data.get(CONF_SERVICE_TIER, default))

    def _raise_provider_home_assistant_error(self, err: SpaceXAIError) -> NoReturn:
        """Apply runtime side effects and raise a translated Home Assistant error."""
        self._handle_provider_error(err)
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key=err.category.value,
            translation_placeholders={"model": err.context.model or self._model},
        ) from err

    def _raise_unexpected_provider_failure(self, err: Exception) -> NoReturn:
        """Log and raise for unexpected provider-path failures."""
        LOGGER.error(
            "Unexpected SpaceXAI failure: operation=%s model=%s\n%s",
            Operation.RESPONSE,
            self._model,
            "".join(traceback.format_tb(err.__traceback__)),
        )
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="unexpected_provider_failure",
            translation_placeholders={"model": self._model},
        ) from err

    async def _async_handle_chat_log(
        self,
        chat_log: conversation.ChatLog,
        structure_name: str | None = None,
        structure: vol.Schema | None = None,
        *,
        max_iterations: int = MAX_TOOL_ITERATIONS,
    ) -> None:
        """Run the bounded provider/tool loop."""
        model = self._model
        messages = _convert_content(chat_log.content)
        tools: list[dict[str, Any]] = []
        if chat_log.llm_api:
            tools = [
                dict(_format_tool(tool, chat_log.llm_api.custom_serializer))
                for tool in chat_log.llm_api.tools
            ]
        tools.extend(_provider_tools_from_subentry(self.subentry.data))
        include = ["reasoning.encrypted_content"]
        if self.subentry.data.get(CONF_CODE_INTERPRETER, DEFAULT_CODE_INTERPRETER):
            include.append("code_interpreter_call.outputs")
        text: ResponseTextConfigParam | None = None
        if structure and structure_name:
            text = {
                "format": {
                    "type": "json_schema",
                    "name": slugify(structure_name),
                    "schema": _format_structured_output(structure, chat_log.llm_api),
                }
            }

        last_content = chat_log.content[-1]
        if (
            isinstance(last_content, conversation.UserContent)
            and last_content.attachments
        ):
            files = await async_prepare_files_for_prompt(
                self.hass,
                [(a.path, a.mime_type) for a in last_content.attachments],
            )
            last_message = messages[-1]
            assert (
                last_message["type"] == "message"
                and last_message["role"] == "user"
                and isinstance(last_message["content"], str)
            )
            last_message["content"] = [
                {"type": "input_text", "text": last_message["content"]},
                *files,
            ]

        for _iteration in range(max_iterations):
            try:
                stream = await self.entry.runtime_data.client.async_stream_response(
                    model=model,
                    input=messages,
                    tools=tools,
                    max_output_tokens=self._max_output_tokens,
                    prompt_cache_key=chat_log.conversation_id,
                    text=text,
                    include=include,
                    temperature=self._temperature,
                    top_p=self._top_p,
                    store=self._store_responses,
                    service_tier=self._service_tier,
                )
            except TimeoutError as err:
                raise RequestTimeoutError(
                    "Provider response timed out",
                    context=ErrorContext(
                        operation=Operation.RESPONSE,
                        model=model,
                    ),
                ) from err
            except (openai.OpenAIError, ValidationError) as err:
                raise self.entry.runtime_data.client.translate_sdk_error(
                    err,
                    ErrorContext(operation=Operation.RESPONSE, model=model),
                ) from err

            try:
                async with stream:
                    new_content = [
                        content
                        async for content in chat_log.async_add_delta_content_stream(
                            self.entity_id,
                            _transform_stream(chat_log, stream, model=model),
                        )
                    ]
            except TimeoutError as err:
                raise RequestTimeoutError(
                    "Provider response timed out",
                    context=ErrorContext(
                        operation=Operation.RESPONSE,
                        model=model,
                    ),
                ) from err
            except (openai.OpenAIError, ValidationError) as err:
                raise self.entry.runtime_data.client.translate_sdk_error(
                    err,
                    ErrorContext(operation=Operation.RESPONSE, model=model),
                ) from err

            for content in new_content:
                if (
                    isinstance(content, conversation.ToolResultContent)
                    and "error" in content.tool_result
                ):
                    LOGGER.warning(
                        "SpaceXAI tool failure: category=%s operation=%s model=%s "
                        "tool=%s call_id=%s retryable=%s",
                        ErrorCategory.HOME_ASSISTANT_TOOL_FAILURE,
                        Operation.TOOL,
                        model,
                        content.tool_name,
                        content.tool_call_id,
                        False,
                    )

            messages.extend(_convert_content(new_content))
            if not chat_log.unresponded_tool_results:
                return

        raise ToolLoopLimitError(
            f"Model exceeded the {max_iterations}-iteration tool limit",
            context=ErrorContext(operation=Operation.TOOL, model=model),
        )

    def _handle_provider_error(self, err: SpaceXAIError) -> None:
        """Map an expected provider failure to runtime and logging behavior."""
        if err.category in (
            ErrorCategory.AUTHENTICATION_REJECTED,
            ErrorCategory.REFRESH_REJECTED,
            ErrorCategory.REAUTHENTICATION_REQUIRED,
            ErrorCategory.ACCOUNT_MISMATCH,
        ):
            self.entry.async_start_reauth(self.hass)
            self._mark_unavailable(err)
            return

        if err.category is ErrorCategory.MODEL_NOT_ENTITLED:
            model = err.context.model or self._model
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"{ISSUE_MODEL_NOT_ENTITLED}_{self.subentry.subentry_id}",
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=ISSUE_MODEL_NOT_ENTITLED,
                translation_placeholders={"model": model},
            )
            self._mark_unavailable(err)
            return

        if err.category in (
            ErrorCategory.SUBSCRIPTION_NOT_ENTITLED,
            ErrorCategory.QUOTA_LIMITED,
        ) and err.context.operation in (Operation.STT, Operation.TTS, Operation.IMAGE):
            # Raised only when api.x.ai rejects this session for STT/TTS/Imagine.
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                f"speech_api_access_{self.entry.entry_id}",
                is_fixable=False,
                learn_more_url="https://console.x.ai/",
                severity=ir.IssueSeverity.WARNING,
                translation_key="speech_api_access",
            )
            self._mark_unavailable(err)
            return

        if (
            isinstance(err, RateLimitedError)
            or err.category is ErrorCategory.RATE_LIMITED
        ):
            LOGGER.warning(
                "SpaceXAI rate limited: operation=%s model=%s status=%s "
                "provider_code=%s request_id=%s",
                err.context.operation,
                err.context.model,
                err.context.status,
                err.context.provider_code,
                err.context.request_id,
            )
            return

        if err.retryable:
            self._mark_unavailable(err)
            return

        LOGGER.error(
            "SpaceXAI request failed: category=%s operation=%s model=%s "
            "status=%s provider_code=%s request_id=%s retryable=%s",
            err.category,
            err.context.operation,
            err.context.model,
            err.context.status,
            err.context.provider_code,
            err.context.request_id,
            err.retryable,
        )

    def _mark_unavailable(self, err: SpaceXAIError) -> None:
        """Mark unavailable and log the transition once."""
        self._attr_available = False
        if self.hass and self.entity_id:
            self.async_write_ha_state()
        if not self._unavailable_logged:
            LOGGER.info(
                "SpaceXAI is unavailable: category=%s operation=%s model=%s "
                "status=%s request_id=%s retryable=%s",
                err.category,
                err.context.operation,
                err.context.model,
                err.context.status,
                err.context.request_id,
                err.retryable,
            )
            self._unavailable_logged = True

    def _mark_available(self) -> None:
        """Mark available and log recovery once."""
        self._attr_available = True
        if self.hass and self.entity_id:
            self.async_write_ha_state()
        if self._unavailable_logged:
            LOGGER.info("SpaceXAI is available again")
            self._unavailable_logged = False
