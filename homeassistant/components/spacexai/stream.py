"""Responses API stream transform for SpaceXAI chat logs."""

import asyncio
from collections.abc import AsyncGenerator, AsyncIterable
import json
from typing import Any

from openai.types.responses import (
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
    ResponseFunctionWebSearch,
    ResponseIncompleteEvent,
    ResponseInProgressEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseOutputMessage,
    ResponseOutputTextAnnotationAddedEvent,
    ResponseQueuedEvent,
    ResponseReasoningItem,
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
)
from openai.types.responses.response_output_item import ImageGenerationCall

from homeassistant.components import conversation
from homeassistant.helpers import llm

from .const import (
    PROVIDER_CODE_INTERPRETER_TOOL,
    PROVIDER_WEB_SEARCH_TOOL,
    PROVIDER_X_SEARCH_TOOL,
    RESPONSE_IDLE_TIMEOUT,
    RESPONSE_TIMEOUT,
)
from .errors import (
    ErrorContext,
    InvalidModelToolRequestError,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    Operation,
    OutputLimitError,
    PermanentProviderError,
    QuotaLimitedError,
    RateLimitedError,
    SpaceXAIError,
    SubscriptionNotEntitledError,
    TransientProviderError,
)

_IGNORED_STREAM_EVENT_PREFIXES = (
    "response.web_search_call.",
    "response.x_search_call.",
    "response.code_interpreter_call.",
    "response.image_generation_call.",
)


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
            "This SpaceXAI account cannot use Grok this way",
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


async def _transform_stream(  # noqa: C901 - Keep stream state in one parser.
    chat_log: conversation.ChatLog,
    stream: AsyncIterable[ResponseStreamEvent],
    *,
    model: str,
) -> AsyncGenerator[
    conversation.AssistantContentDeltaDict | conversation.ToolResultContentDeltaDict
]:
    """Transform a Responses API stream into Home Assistant chat deltas."""
    assistant_open = False
    assistant_has_tool_calls = False
    reasoning_native_set = False
    last_summary_index: int | None = None
    announced_tool_calls: dict[str, tuple[str, str]] = {}
    call_ids: set[str] = set()
    terminal = False

    async with asyncio.timeout(RESPONSE_TIMEOUT):
        stream_iterator = aiter(stream)
        while True:
            try:
                async with asyncio.timeout(RESPONSE_IDLE_TIMEOUT):
                    event = await anext(stream_iterator)
            except StopAsyncIteration:
                break

            if terminal:
                raise MalformedProviderResponseError(
                    "Provider emitted data after the terminal event",
                    context=ErrorContext(operation=Operation.RESPONSE, model=model),
                )

            if isinstance(event, ResponseOutputItemAddedEvent):
                if isinstance(event.item, ResponseFunctionToolCall):
                    if announced_tool_calls or assistant_has_tool_calls:
                        raise InvalidModelToolRequestError(
                            "Provider emitted multiple tool calls in one response",
                            context=ErrorContext(operation=Operation.TOOL, model=model),
                        )
                    if not assistant_open:
                        yield {"role": "assistant"}
                        assistant_open = True
                    if event.item.id is None:
                        raise MalformedProviderResponseError(
                            "Provider tool call omitted its item ID",
                            context=ErrorContext(
                                operation=Operation.RESPONSE, model=model
                            ),
                        )
                    if (
                        event.item.id in announced_tool_calls
                        or event.item.call_id in call_ids
                    ):
                        raise InvalidModelToolRequestError(
                            "Provider emitted a duplicate tool-call identifier",
                            context=ErrorContext(operation=Operation.TOOL, model=model),
                        )
                    announced_tool_calls[event.item.id] = (
                        event.item.call_id,
                        event.item.name,
                    )
                    call_ids.add(event.item.call_id)
                    continue
                if isinstance(event.item, ResponseOutputMessage):
                    if not assistant_open or assistant_has_tool_calls:
                        yield {"role": "assistant"}
                    assistant_open = True
                    assistant_has_tool_calls = False
                    continue
                if isinstance(event.item, ResponseReasoningItem):
                    if not assistant_open:
                        yield {"role": "assistant"}
                        assistant_open = True
                    continue
                if (
                    isinstance(event.item, ImageGenerationCall)
                    or _item_type(event.item) == "image_generation_call"
                ):
                    if not assistant_open:
                        yield {"role": "assistant"}
                        assistant_open = True
                    continue
                if isinstance(
                    event.item,
                    (ResponseFunctionWebSearch, ResponseCodeInterpreterToolCall),
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
                # xAI omits name on function_call_arguments.done (SDK leaves it
                # None); the announced output_item.added name is authoritative.
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
                yield {
                    "tool_calls": [
                        llm.ToolInput(
                            id=call_id,
                            tool_name=tool_name,
                            tool_args=tool_args,
                        )
                    ]
                }
                assistant_has_tool_calls = True
                continue

            if isinstance(event, ResponseTextDeltaEvent):
                if not assistant_open:
                    yield {"role": "assistant"}
                    assistant_open = True
                if event.delta:
                    yield {"content": event.delta}
                continue

            if isinstance(event, ResponseReasoningSummaryTextDeltaEvent):
                if not assistant_open or (
                    last_summary_index is not None
                    and event.summary_index != last_summary_index
                ):
                    yield {"role": "assistant"}
                    assistant_open = True
                last_summary_index = event.summary_index
                if event.delta:
                    yield {"thinking_content": event.delta}
                continue

            if isinstance(event, ResponseOutputItemDoneEvent):
                if isinstance(event.item, ResponseReasoningItem):
                    if reasoning_native_set:
                        yield {"role": "assistant"}
                    yield {"native": event.item}
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
                elif (
                    isinstance(event.item, ImageGenerationCall)
                    or _item_type(event.item) == "image_generation_call"
                ):
                    if not assistant_open:
                        yield {"role": "assistant"}
                        assistant_open = True
                    yield {"native": event.item}
                    # Next text/message should open a fresh assistant content.
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
        if not assistant_open and not assistant_has_tool_calls:
            raise MalformedProviderResponseError(
                "Provider completed without response content",
                context=ErrorContext(operation=Operation.RESPONSE, model=model),
            )
