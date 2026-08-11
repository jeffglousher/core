"""Shared SpaceXAI LLM entity helpers."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterable, Callable, Iterable, Mapping
import json
import traceback
from typing import Any, Literal, NoReturn, cast

import httpx
import openai
from openai.types.responses import (
    EasyInputMessageParam,
    FunctionToolParam,
    ResponseCodeInterpreterToolCall,
    ResponseCompletedEvent,
    ResponseContentPartAddedEvent,
    ResponseContentPartDoneEvent,
    ResponseCreatedEvent,
    ResponseErrorEvent,
    ResponseFailedEvent,
    ResponseFunctionCallArgumentsDeltaEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseFunctionToolCall,
    ResponseFunctionToolCallParam,
    ResponseFunctionWebSearch,
    ResponseIncompleteEvent,
    ResponseInProgressEvent,
    ResponseInputParam,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseOutputMessage,
    ResponseOutputTextAnnotationAddedEvent,
    ResponseQueuedEvent,
    ResponseReasoningItem,
    ResponseReasoningItemParam,
    ResponseReasoningSummaryPartAddedEvent,
    ResponseReasoningSummaryPartDoneEvent,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseReasoningSummaryTextDoneEvent,
    ResponseReasoningTextDeltaEvent,
    ResponseReasoningTextDoneEvent,
    ResponseRefusalDeltaEvent,
    ResponseRefusalDoneEvent,
    ResponseStreamEvent,
    ResponseTextDeltaEvent,
    ResponseTextDoneEvent,
    ResponseWebSearchCallCompletedEvent,
    ResponseWebSearchCallInProgressEvent,
    ResponseWebSearchCallSearchingEvent,
    WebSearchToolParam,
)
from openai.types.responses.response_code_interpreter_tool_call_param import (
    ResponseCodeInterpreterToolCallParam,
)
from openai.types.responses.response_function_web_search_param import (
    ResponseFunctionWebSearchParam,
)
from openai.types.responses.response_input_param import FunctionCallOutput
from openai.types.responses.response_text_config_param import ResponseTextConfigParam
from pydantic import ValidationError
import voluptuous as vol
from voluptuous_openapi import convert

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import CONF_MODEL
from homeassistant.core import callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr, entity_platform, llm
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.json import json_dumps
from homeassistant.util import slugify

from . import SpaceXAIConfigEntry, async_mark_subscription_not_entitled
from .const import (
    CONF_CODE_INTERPRETER,
    CONF_MAX_OUTPUT_TOKENS,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    CONVERSE_TIMEOUT,
    DEFAULT_CODE_INTERPRETER,
    DEFAULT_WEB_SEARCH,
    DEFAULT_X_SEARCH,
    DOMAIN,
    LOGGER,
    MAX_TOOL_ITERATIONS,
    PROVIDER_CODE_INTERPRETER_TOOL,
    PROVIDER_SEARCH_TOOLS,
    PROVIDER_WEB_SEARCH_TOOL,
    PROVIDER_X_SEARCH_TOOL,
    RESPONSE_TIMEOUT,
)
from .errors import (
    ConnectionFailureError,
    ErrorCategory,
    ErrorContext,
    InvalidModelToolRequestError,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    Operation,
    OutputLimitError,
    PermanentProviderError,
    QuotaLimitedError,
    RateLimitedError,
    RequestTimeoutError,
    SpaceXAIError,
    SubscriptionNotEntitledError,
    ToolLoopLimitError,
    TransientProviderError,
)
from .issue import (
    MODEL_ISSUE_ORIGIN_RESPONSE,
    async_create_model_not_entitled_issue,
    async_delete_model_not_entitled_issue,
    async_model_issue_is_response_originated,
)

_IGNORED_STREAM_EVENT_PREFIXES = (
    "response.web_search_call.",
    "response.x_search_call.",
    "response.code_interpreter_call.",
)


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
    unsupported_keys = {"oneOf", "anyOf", "allOf", "enum", "not"}
    schema = convert(tool.parameters, custom_serializer=custom_serializer)
    if unsupported_keys.intersection(schema):
        schema = {
            key: value for key, value in schema.items() if key not in unsupported_keys
        }
    return FunctionToolParam(
        type="function",
        name=tool.name,
        description=tool.description,
        parameters=schema,
        strict=False,
    )


def _convert_content(
    chat_content: Iterable[conversation.Content],
) -> ResponseInputParam:
    """Convert Home Assistant-owned history to Responses API input."""
    messages: ResponseInputParam = []
    reasoning_summary: list[str] = []
    search_calls: dict[str, ResponseFunctionWebSearchParam] = {}
    code_calls: dict[str, ResponseCodeInterpreterToolCallParam] = {}
    for content in chat_content:
        if isinstance(content, conversation.ToolResultContent):
            reasoning_summary = []
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
            if content.thinking_content:
                reasoning_summary.append(content.thinking_content)
            if isinstance(content.native, ResponseReasoningItem):
                messages.append(
                    ResponseReasoningItemParam(
                        type="reasoning",
                        id=content.native.id,
                        summary=(
                            [
                                {"type": "summary_text", "text": summary}
                                for summary in reasoning_summary
                            ]
                            if content.thinking_content
                            else []
                        ),
                        encrypted_content=content.native.encrypted_content,
                    )
                )
                reasoning_summary = []
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

        reasoning_summary = []
        role: Literal["system", "user"] = content.role
        messages.append(
            EasyInputMessageParam(
                type="message",
                role=role,
                content=content.content,
            )
        )
    return messages


def _stream_failure(
    code: str | None,
    *,
    model: str,
    request_id: str | None = None,
) -> SpaceXAIError:
    """Classify a valid provider failure event."""
    context = ErrorContext(
        operation=Operation.RESPONSE,
        model=model,
        provider_code=code,
        request_id=request_id,
    )
    normalized = (code or "").lower()
    if normalized in ("insufficient_quota", "billing_hard_limit_reached"):
        return QuotaLimitedError(
            "Provider reported a quota or billing limitation", context=context
        )
    if normalized in ("model_not_found", "model_not_available"):
        return ModelNotEntitledError(
            "Configured model is not available to this account", context=context
        )
    if normalized in (
        "subscription_required",
        "subscription_not_entitled",
        "not_entitled",
        "insufficient_permissions",
    ):
        return SubscriptionNotEntitledError(
            "Account is not entitled for subscription-backed Grok access",
            context=context,
        )
    if normalized == "rate_limit_exceeded":
        return RateLimitedError("Provider rate limit reached", context=context)
    if normalized == "max_output_tokens":
        return OutputLimitError(
            "Provider reached the configured output limit", context=context
        )
    if normalized in ("server_error", "vector_store_timeout"):
        return TransientProviderError(
            "Provider reported a transient failure", context=context
        )
    return PermanentProviderError("Provider rejected the response", context=context)


def _item_type(item: object) -> str | None:
    """Return a Responses output item type when available."""
    item_type = getattr(item, "type", None)
    return item_type if isinstance(item_type, str) else None


def _external_search_deltas(
    item: object,
    tool_name: str,
) -> list[
    conversation.AssistantContentDeltaDict | conversation.ToolResultContentDeltaDict
]:
    """Emit chat-log deltas for a completed server-side search tool."""
    action = getattr(item, "action", None)
    if action is not None and hasattr(action, "to_dict"):
        action = action.to_dict()
    item_id = getattr(item, "id", None)
    status = getattr(item, "status", "completed")
    if not isinstance(item_id, str) or not item_id:
        raise MalformedProviderResponseError(
            "Provider search tool omitted its item ID",
            context=ErrorContext(operation=Operation.RESPONSE),
        )
    return [
        {
            "tool_calls": [
                llm.ToolInput(
                    id=item_id,
                    tool_name=tool_name,
                    tool_args={"action": action},
                    external=True,
                )
            ]
        },
        {
            "role": "tool_result",
            "tool_call_id": item_id,
            "tool_name": tool_name,
            "tool_result": {"status": status},
        },
    ]


async def _transform_stream(  # noqa: C901
    chat_log: conversation.ChatLog,
    stream: AsyncIterable[ResponseStreamEvent],
    *,
    model: str,
) -> AsyncGenerator[
    conversation.AssistantContentDeltaDict | conversation.ToolResultContentDeltaDict
]:
    """Transform a Responses API stream into Home Assistant chat deltas."""
    assistant_open = False
    reasoning_native_set = False
    last_summary_index: int | None = None
    announced_tool_calls: dict[str, tuple[str, str]] = {}
    call_ids: set[str] = set()
    pending_deltas: list[conversation.AssistantContentDeltaDict] = []
    content_parts: list[str] = []
    thinking_parts: list[str] = []
    terminal = False
    produced_user_visible_output = False

    def _flush_text_parts() -> None:
        if content_parts:
            pending_deltas.append({"content": "".join(content_parts)})
            content_parts.clear()
        if thinking_parts:
            pending_deltas.append({"thinking_content": "".join(thinking_parts)})
            thinking_parts.clear()

    def _emit(delta: conversation.AssistantContentDeltaDict) -> None:
        content = delta.get("content")
        if set(delta) == {"content"} and isinstance(content, str):
            if thinking_parts:
                _flush_text_parts()
            content_parts.append(content)
            return
        thinking = delta.get("thinking_content")
        if set(delta) == {"thinking_content"} and isinstance(thinking, str):
            if content_parts:
                _flush_text_parts()
            thinking_parts.append(thinking)
            return
        _flush_text_parts()
        pending_deltas.append(delta)

    async for event in stream:
        if terminal:
            raise MalformedProviderResponseError(
                "Provider emitted data after the terminal event",
                context=ErrorContext(operation=Operation.RESPONSE, model=model),
            )

        if isinstance(event, ResponseOutputItemAddedEvent):
            if isinstance(event.item, ResponseFunctionToolCall):
                if not assistant_open:
                    _emit({"role": "assistant"})
                    assistant_open = True
                if event.item.id is None:
                    raise MalformedProviderResponseError(
                        "Provider tool call omitted its item ID",
                        context=ErrorContext(operation=Operation.RESPONSE, model=model),
                    )
                if not event.item.call_id or not event.item.name:
                    raise InvalidModelToolRequestError(
                        "Provider tool call omitted call_id or name",
                        context=ErrorContext(operation=Operation.TOOL, model=model),
                    )
                if (
                    event.item.id in announced_tool_calls
                    or event.item.call_id in call_ids
                ):
                    raise InvalidModelToolRequestError(
                        "Provider emitted a duplicate tool-call identifier",
                        context=ErrorContext(operation=Operation.TOOL, model=model),
                    )
                if announced_tool_calls or call_ids:
                    raise InvalidModelToolRequestError(
                        "Provider emitted multiple tool calls in one response",
                        context=ErrorContext(operation=Operation.TOOL, model=model),
                    )
                announced_tool_calls[event.item.id] = (
                    event.item.call_id,
                    event.item.name,
                )
                call_ids.add(event.item.call_id)
                continue
            if isinstance(event.item, ResponseOutputMessage):
                _emit({"role": "assistant"})
                assistant_open = True
                continue
            if isinstance(event.item, ResponseReasoningItem):
                if not assistant_open or reasoning_native_set:
                    _emit({"role": "assistant"})
                    assistant_open = True
                reasoning_native_set = False
                last_summary_index = None
                continue
            if isinstance(
                event.item, (ResponseFunctionWebSearch, ResponseCodeInterpreterToolCall)
            ) or _item_type(event.item) in (
                PROVIDER_WEB_SEARCH_TOOL,
                PROVIDER_X_SEARCH_TOOL,
                "code_interpreter_call",
            ):
                continue
            raise MalformedProviderResponseError(
                f"Unexpected output item type {_item_type(event.item) or type(event.item)!r}",
                context=ErrorContext(operation=Operation.RESPONSE, model=model),
            )

        if isinstance(event, ResponseFunctionCallArgumentsDoneEvent):
            announced = announced_tool_calls.pop(event.item_id, None)
            if announced is None:
                raise MalformedProviderResponseError(
                    "Tool arguments did not match an announced tool call",
                    context=ErrorContext(operation=Operation.RESPONSE, model=model),
                )
            call_id, tool_name = announced
            if event.name and event.name != tool_name:
                raise InvalidModelToolRequestError(
                    "Provider changed the announced tool name",
                    context=ErrorContext(operation=Operation.TOOL, model=model),
                )
            try:
                tool_args = json.loads(event.arguments)
            except json.JSONDecodeError as err:
                raise InvalidModelToolRequestError(
                    "Model emitted malformed tool arguments",
                    context=ErrorContext(operation=Operation.TOOL, model=model),
                ) from err
            if not isinstance(tool_args, dict):
                raise InvalidModelToolRequestError(
                    "Model tool arguments were not an object",
                    context=ErrorContext(operation=Operation.TOOL, model=model),
                )
            _emit(
                {
                    "tool_calls": [
                        llm.ToolInput(
                            id=call_id,
                            tool_name=tool_name,
                            tool_args=tool_args,
                        )
                    ]
                }
            )
            produced_user_visible_output = True
            continue

        if isinstance(event, ResponseTextDeltaEvent):
            if not assistant_open:
                _emit({"role": "assistant"})
                assistant_open = True
            if event.delta:
                _emit({"content": event.delta})
                produced_user_visible_output = True
            continue

        if isinstance(event, ResponseReasoningSummaryTextDeltaEvent):
            if not assistant_open or reasoning_native_set:
                _emit({"role": "assistant"})
                assistant_open = True
                reasoning_native_set = False
                last_summary_index = None
            if (
                last_summary_index is not None
                and event.summary_index != last_summary_index
            ):
                _emit({"role": "assistant"})
                assistant_open = True
            last_summary_index = event.summary_index
            if event.delta:
                _emit({"thinking_content": event.delta})
            continue

        if isinstance(event, ResponseOutputItemDoneEvent):
            if isinstance(event.item, ResponseReasoningItem):
                _emit({"native": event.item})
                reasoning_native_set = True
            elif isinstance(event.item, ResponseFunctionWebSearch) or _item_type(
                event.item
            ) in (PROVIDER_WEB_SEARCH_TOOL, PROVIDER_X_SEARCH_TOOL):
                tool_name = (
                    PROVIDER_X_SEARCH_TOOL
                    if _item_type(event.item) == PROVIDER_X_SEARCH_TOOL
                    else PROVIDER_WEB_SEARCH_TOOL
                )
                if not assistant_open:
                    yield {"role": "assistant"}
                    assistant_open = True
                for delta in _external_search_deltas(event.item, tool_name):
                    yield delta
                assistant_open = False
                assistant_has_tool_calls = False
            elif isinstance(event.item, ResponseCodeInterpreterToolCall):
                if not assistant_open:
                    yield {"role": "assistant"}
                    assistant_open = True
                yield {
                    "tool_calls": [
                        llm.ToolInput(
                            id=event.item.id,
                            tool_name=PROVIDER_CODE_INTERPRETER_TOOL,
                            tool_args={
                                "code": event.item.code,
                                "container": event.item.container_id,
                            },
                            external=True,
                        )
                    ]
                }
                outputs: Any = None
                if event.item.outputs is not None:
                    outputs = [output.to_dict() for output in event.item.outputs]
                yield {
                    "role": "tool_result",
                    "tool_call_id": event.item.id,
                    "tool_name": PROVIDER_CODE_INTERPRETER_TOOL,
                    "tool_result": {"output": outputs},
                }
                assistant_open = False
                assistant_has_tool_calls = False
            continue

        if isinstance(event, ResponseCompletedEvent):
            if announced_tool_calls:
                raise InvalidModelToolRequestError(
                    "Provider completed with unfinished tool calls",
                    context=ErrorContext(operation=Operation.TOOL, model=model),
                )
            terminal = True
            if event.response.usage is not None:
                chat_log.async_trace(
                    {
                        "stats": {
                            "input_tokens": event.response.usage.input_tokens,
                            "cached_input_tokens": (
                                event.response.usage.input_tokens_details.cached_tokens
                            ),
                            "output_tokens": event.response.usage.output_tokens,
                        }
                    }
                )
            continue

        if isinstance(event, ResponseIncompleteEvent):
            reason = (
                event.response.incomplete_details.reason
                if event.response.incomplete_details
                else "unknown"
            )
            raise _stream_failure(
                reason,
                model=model,
                request_id=event.response.id,
            )

        if isinstance(event, ResponseFailedEvent):
            raise _stream_failure(
                event.response.error.code if event.response.error else None,
                model=model,
                request_id=event.response.id,
            )

        if isinstance(event, ResponseErrorEvent):
            raise _stream_failure(event.code, model=model)

        if isinstance(event, (ResponseRefusalDeltaEvent, ResponseRefusalDoneEvent)):
            raise PermanentProviderError(
                "Provider refused the response",
                context=ErrorContext(operation=Operation.RESPONSE, model=model),
            )

        if isinstance(
            event,
            (
                ResponseContentPartAddedEvent,
                ResponseContentPartDoneEvent,
                ResponseCreatedEvent,
                ResponseFunctionCallArgumentsDeltaEvent,
                ResponseInProgressEvent,
                ResponseOutputTextAnnotationAddedEvent,
                ResponseQueuedEvent,
                ResponseReasoningSummaryPartAddedEvent,
                ResponseReasoningSummaryPartDoneEvent,
                ResponseReasoningSummaryTextDoneEvent,
                ResponseReasoningTextDeltaEvent,
                ResponseReasoningTextDoneEvent,
                ResponseTextDoneEvent,
                ResponseWebSearchCallCompletedEvent,
                ResponseWebSearchCallInProgressEvent,
                ResponseWebSearchCallSearchingEvent,
            ),
        ) or any(
            getattr(event, "type", "").startswith(prefix)
            for prefix in _IGNORED_STREAM_EVENT_PREFIXES
        ):
            continue

        raise MalformedProviderResponseError(
            f"Unexpected stream event type {event.type}",
            context=ErrorContext(operation=Operation.RESPONSE, model=model),
        )

    if not terminal:
        raise MalformedProviderResponseError(
            "Provider stream ended without a terminal event",
            context=ErrorContext(operation=Operation.RESPONSE, model=model),
        )
    if not produced_user_visible_output:
        raise MalformedProviderResponseError(
            "Provider completed without user-visible assistant content",
            context=ErrorContext(operation=Operation.RESPONSE, model=model),
        )
    _flush_text_parts()
    for delta in pending_deltas:
        yield delta


class SpaceXAIBaseLLMEntity(Entity):
    """Shared SpaceXAI LLM entity behavior."""

    _attr_has_entity_name = True
    _attr_name: str | None = None

    def __init__(self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the shared LLM entity."""
        self.entry = entry
        self.subentry = subentry
        self._unavailable_logged = False
        self._account_wide_unavailable = False
        self._model_entitlement_blocked = False
        self._availability_epoch = 0
        model = cast(str, subentry.data[CONF_MODEL])
        self._attr_available = entry.runtime_data.snapshot.has_model(model)
        self._attr_unique_id = subentry.subentry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="SpaceXAI",
            model=model,
            model_id=model,
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    @property
    def _model(self) -> str:
        """Return the configured model."""
        return cast(str, self.subentry.data[CONF_MODEL])

    @property
    def _max_output_tokens(self) -> int:
        """Return the configured model output limit."""
        return cast(int, self.subentry.data[CONF_MAX_OUTPUT_TOKENS])

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
        if self.subentry.data.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH):
            tools.append(dict(WebSearchToolParam(type="web_search")))
        if self.subentry.data.get(CONF_X_SEARCH, DEFAULT_X_SEARCH):
            tools.append({"type": "x_search"})
        if self.subentry.data.get(CONF_CODE_INTERPRETER, DEFAULT_CODE_INTERPRETER):
            tools.append({"type": "code_interpreter"})
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

        try:
            async with asyncio.timeout(CONVERSE_TIMEOUT):
                for _iteration in range(max_iterations):
                    stream = await self.entry.runtime_data.client.async_stream_response(
                        model=model,
                        input=messages,
                        tools=tools,
                        max_output_tokens=self._max_output_tokens,
                        prompt_cache_key=chat_log.conversation_id,
                        text=text,
                        include=include,
                    )

                    async with stream:
                        deadline = asyncio.get_running_loop().time() + RESPONSE_TIMEOUT
                        try:
                            async with asyncio.timeout_at(deadline):
                                try:
                                    deltas = [
                                        delta
                                        async for delta in _transform_stream(
                                            chat_log, stream, model=model
                                        )
                                    ]
                                except httpx.TimeoutException as err:
                                    raise RequestTimeoutError(
                                        "Provider response timed out",
                                        context=ErrorContext(
                                            operation=Operation.RESPONSE,
                                            model=model,
                                        ),
                                    ) from err
                                except httpx.TransportError as err:
                                    raise ConnectionFailureError(
                                        "Could not read the provider response stream",
                                        context=ErrorContext(
                                            operation=Operation.RESPONSE,
                                            model=model,
                                        ),
                                    ) from err
                                except (openai.OpenAIError, ValidationError) as err:
                                    raise self.entry.runtime_data.client.translate_sdk_error(
                                        err,
                                        ErrorContext(
                                            operation=Operation.RESPONSE,
                                            model=model,
                                        ),
                                    ) from err
                        except TimeoutError as err:
                            raise RequestTimeoutError(
                                "Provider response timed out",
                                context=ErrorContext(
                                    operation=Operation.RESPONSE,
                                    model=model,
                                ),
                            ) from err

                        async def _replay_deltas(
                            deltas_to_replay: list[
                                conversation.AssistantContentDeltaDict
                                | conversation.ToolResultContentDeltaDict
                            ] = deltas,
                        ) -> AsyncIterable[
                            conversation.AssistantContentDeltaDict
                            | conversation.ToolResultContentDeltaDict
                        ]:
                            for delta in deltas_to_replay:
                                yield delta

                        try:
                            async with asyncio.timeout_at(deadline):
                                new_content = [
                                    content
                                    async for content in chat_log.async_add_delta_content_stream(
                                        self.entity_id,
                                        _replay_deltas(),
                                    )
                                ]
                        except TimeoutError as err:
                            raise HomeAssistantError(
                                translation_domain=DOMAIN,
                                translation_key="home_assistant_tool_failure",
                                translation_placeholders={"model": model},
                            ) from err

                    for content in new_content:
                        if (
                            isinstance(content, conversation.ToolResultContent)
                            and "error" in content.tool_result
                        ):
                            LOGGER.warning(
                                "SpaceXAI tool failure: category=%s operation=%s "
                                "model=%s tool=%s call_id=%s retryable=%s",
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
        except TimeoutError as err:
            raise RequestTimeoutError(
                "Provider response timed out",
                context=ErrorContext(operation=Operation.RESPONSE, model=model),
            ) from err

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
            self._mark_entry_agents_unavailable(err)
            return

        if err.category is ErrorCategory.MODEL_NOT_ENTITLED:
            async_create_model_not_entitled_issue(
                self.hass,
                self.entry,
                subentry_id=self.subentry.subentry_id,
                model=err.context.model or self._model,
                origin=MODEL_ISSUE_ORIGIN_RESPONSE,
            )
            self._mark_unavailable(err)
            return

        if err.category is ErrorCategory.SUBSCRIPTION_NOT_ENTITLED:
            async_mark_subscription_not_entitled(
                self.hass,
                self.entry,
                operation=err.context.operation,
            )
            return

        if err.category is ErrorCategory.QUOTA_LIMITED:
            self._mark_entry_agents_unavailable(err)
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

    def _mark_entry_agents_unavailable(self, err: SpaceXAIError) -> None:
        """Mark every conversation agent on this config entry unavailable."""
        for platform in entity_platform.async_get_platforms(self.hass, DOMAIN):
            for entity in platform.entities.values():
                if getattr(entity, "entry", None) is not self.entry:
                    continue
                mark = getattr(entity, "_mark_unavailable", None)
                if mark is not None:
                    mark(err, account_wide=True)

    def _mark_unavailable(
        self, err: SpaceXAIError, *, account_wide: bool = False
    ) -> None:
        """Mark unavailable and log the transition once."""
        self._availability_epoch += 1
        if err.category is ErrorCategory.MODEL_NOT_ENTITLED:
            if err.context.operation is Operation.RESPONSE:
                self._model_entitlement_blocked = True
            self._account_wide_unavailable = False
        elif account_wide and not self._model_entitlement_blocked:
            self._account_wide_unavailable = True
        elif not account_wide and not self._model_entitlement_blocked:
            self._account_wide_unavailable = False
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

    def _mark_available(
        self, epoch: int | None = None, *, inference_ok: bool = False
    ) -> bool:
        """Recover only when the configured model is still entitled."""
        if epoch is not None and epoch != self._availability_epoch:
            return False
        if not self.entry.runtime_data.snapshot.has_model(self._model):
            return False
        if self._model_entitlement_blocked and not inference_ok:
            return False
        self._attr_available = True
        self._account_wide_unavailable = False
        self._model_entitlement_blocked = False
        if self.hass and self.entity_id:
            self.async_write_ha_state()
        async_delete_model_not_entitled_issue(
            self.hass,
            self.subentry.subentry_id,
            catalog_only=not inference_ok,
        )
        if self._unavailable_logged:
            LOGGER.info("SpaceXAI is available again")
            self._unavailable_logged = False
        return True

    def _restore_entitled_entry_agents(
        self, availability_epochs: Mapping[str, int] | None = None
    ) -> None:
        """Restore siblings that were down only for a shared account outage."""
        for platform in entity_platform.async_get_platforms(self.hass, DOMAIN):
            for entity in platform.entities.values():
                if entity is self or getattr(entity, "entry", None) is not self.entry:
                    continue
                if not getattr(entity, "_account_wide_unavailable", False):
                    continue
                epoch: int | None = None
                subentry = getattr(entity, "subentry", None)
                if availability_epochs is not None and subentry is not None:
                    epoch = availability_epochs.get(subentry.subentry_id)
                getattr(entity, "_mark_available")(epoch)  # noqa: B009

    @callback
    def async_apply_model_entitlement(self, epoch: int | None = None) -> None:
        """Sync availability with whether the configured model remains entitled."""
        if self.hass is not None and async_model_issue_is_response_originated(
            self.hass, self.subentry.subentry_id
        ):
            self._model_entitlement_blocked = True
        if self.entry.runtime_data.snapshot.has_model(self._model):
            if self._model_entitlement_blocked:
                if self.available:
                    self._mark_unavailable(
                        ModelNotEntitledError(
                            "Configured model is not available to this account",
                            context=ErrorContext(
                                operation=Operation.RESPONSE, model=self._model
                            ),
                        )
                    )
                return
            self._mark_available(epoch)
            return
        if self.available:
            self._mark_unavailable(
                ModelNotEntitledError(
                    "Configured model is not available to this account",
                    context=ErrorContext(operation=Operation.MODELS, model=self._model),
                )
            )
