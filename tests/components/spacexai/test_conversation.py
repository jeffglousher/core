"""Tests for SpaceXAI Conversation."""

import asyncio
from collections.abc import AsyncIterator
import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
from openai import APIConnectionError
from openai.types.responses import (
    Response,
    ResponseCodeInterpreterToolCall,
    ResponseCompletedEvent,
    ResponseCreatedEvent,
    ResponseErrorEvent,
    ResponseFailedEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseFunctionToolCall,
    ResponseFunctionWebSearch,
    ResponseIncompleteEvent,
    ResponseOutputItemAddedEvent,
    ResponseOutputItemDoneEvent,
    ResponseReasoningItem,
    ResponseReasoningSummaryTextDeltaEvent,
    ResponseRefusalDeltaEvent,
    ResponseStreamEvent,
    ResponseTextDeltaEvent,
    ResponseWebSearchCallSearchingEvent,
)
import pytest

from homeassistant.components import conversation
from homeassistant.components.spacexai.const import (
    CONF_CODE_INTERPRETER,
    CONF_MAX_OUTPUT_TOKENS,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    DEFAULT_MODEL,
    MAX_TOOL_ITERATIONS,
)
from homeassistant.components.spacexai.errors import (
    ErrorContext,
    Operation,
    RateLimitedError,
    ReauthenticationRequiredError,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.const import (
    CONF_PROMPT,
    STATE_UNAVAILABLE,
    __version__ as HA_VERSION,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import device_registry as dr, intent

from . import EventStream, message_events, tool_events
from .conftest import ACCESS_TOKEN

from tests.common import MockConfigEntry
from tests.components.conversation import (
    MockChatLog,
    mock_chat_log,  # noqa: F401
)


def _response(**changes: Any) -> Response:
    """Build a minimal Responses API response for lifecycle events."""
    data = {
        "id": "response-123",
        "created_at": 1,
        "model": DEFAULT_MODEL,
        "object": "response",
        "output": [],
        "parallel_tool_calls": True,
        "tool_choice": "auto",
        "tools": [],
        "status": "completed",
        "usage": None,
    }
    data.update(changes)
    return Response.model_validate(data)


async def test_entity_and_device(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Expose a translated Conversation entity and service device."""
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert (
        state.attributes["supported_features"]
        == conversation.ConversationEntityFeature.CONTROL
    )
    subentry = next(
        entry
        for entry in setup_integration.subentries.values()
        if entry.subentry_type == "conversation"
    )
    device = device_registry.async_get_device_by_identifier(
        ("spacexai", subentry.subentry_id), setup_integration.entry_id
    )
    assert device is not None
    assert device.manufacturer == "SpaceXAI"
    assert device.model_id == DEFAULT_MODEL
    assert device.entry_type is dr.DeviceEntryType.SERVICE
    agent = conversation.agent_manager.async_get_agent(hass, "conversation.grok")
    assert agent.supported_languages == "*"


async def test_runtime_identity_is_in_system_prompt(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Expose Home Assistant and Grok model versions in the system prompt."""
    await conversation.async_converse(
        hass,
        "What versions are you?",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    system_message = next(
        item
        for item in mock_stream.call_args.kwargs["input"]
        if item.get("type") == "message" and item.get("role") == "system"
    )
    content = system_message["content"]
    if isinstance(content, list):
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    else:
        text = str(content)
    assert HA_VERSION in text
    assert DEFAULT_MODEL in text
    assert "SpaceXAI" in text


async def test_streaming_conversation_and_continuation(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Stream responses and continue using Home Assistant-owned history."""
    first = await conversation.async_converse(
        hass,
        "Hello",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert first.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert first.response.speech["plain"]["speech"] == "Hello from Grok"

    mock_stream.return_value = EventStream(message_events("Welcome back"))
    second = await conversation.async_converse(
        hass,
        "Remember me?",
        first.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )
    assert second.conversation_id == first.conversation_id
    assert second.response.speech["plain"]["speech"] == "Welcome back"
    second_input = mock_stream.call_args.kwargs["input"]
    assert [item["role"] for item in second_input if item["type"] == "message"] == [
        "system",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert mock_stream.call_args.kwargs["prompt_cache_key"] == first.conversation_id
    assert mock_stream.call_args.kwargs["max_output_tokens"] == 2048


async def test_web_search_tool_is_server_side(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Enable SpaceXAI web search and treat provider search calls as external."""
    subentry = next(
        entry
        for entry in setup_integration.subentries.values()
        if entry.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        setup_integration,
        subentry,
        data={**subentry.data, CONF_WEB_SEARCH: True},
    )
    await hass.config_entries.async_reload(setup_integration.entry_id)
    await hass.async_block_till_done()

    mock_stream.return_value = EventStream(
        [
            ResponseOutputItemAddedEvent(
                item=ResponseFunctionWebSearch.model_validate(
                    {
                        "id": "ws_1",
                        "status": "in_progress",
                        "type": "web_search_call",
                        "action": {"type": "search", "query": "xAI"},
                    }
                ),
                output_index=0,
                sequence_number=0,
                type="response.output_item.added",
            ),
            ResponseWebSearchCallSearchingEvent(
                item_id="ws_1",
                output_index=0,
                sequence_number=1,
                type="response.web_search_call.searching",
            ),
            ResponseOutputItemDoneEvent(
                item=ResponseFunctionWebSearch.model_validate(
                    {
                        "id": "ws_1",
                        "status": "completed",
                        "type": "web_search_call",
                        "action": {"type": "search", "query": "xAI"},
                    }
                ),
                output_index=0,
                sequence_number=2,
                type="response.output_item.done",
            ),
            *message_events("Found it", complete=True),
        ]
    )
    result = await conversation.async_converse(
        hass,
        "Search for xAI",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.speech["plain"]["speech"] == "Found it"
    tools = mock_stream.call_args.kwargs["tools"]
    assert {"type": "web_search"} in tools


async def test_parallel_tool_calls(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Correlate multiple provider tool calls and send every result."""
    mock_stream.side_effect = [
        EventStream(
            tool_events(
                ("call_1", "test_tool", '{"value": 1}'),
                ("call_2", "test_tool", '{"value": 2}'),
            )
        ),
        EventStream(message_events("Both tools completed")),
    ]
    mock_chat_log.mock_tool_results(
        {
            "call_1": {"result": "one"},
            "call_2": {"result": "two"},
        }
    )

    result = await conversation.async_converse(
        hass,
        "Run both",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.speech["plain"]["speech"] == "Both tools completed"
    assert mock_stream.await_count == 2
    advertised_tools = mock_stream.await_args_list[0].kwargs["tools"]
    assert advertised_tools
    assert all(tool["type"] == "function" for tool in advertised_tools)
    assert all(tool["parameters"]["type"] == "object" for tool in advertised_tools)
    second_input = mock_stream.call_args.kwargs["input"]
    outputs = [item for item in second_input if item["type"] == "function_call_output"]
    assert [item["call_id"] for item in outputs] == ["call_1", "call_2"]


async def test_tool_call_arguments_done_without_name(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Accept xAI streams that omit name on function_call_arguments.done."""
    # Live xAI payloads leave name unset; construct the SDK model the same way.
    arguments_done = ResponseFunctionCallArgumentsDoneEvent.model_construct(
        arguments='{"value": 1}',
        item_id="item_0",
        name=None,
        output_index=0,
        sequence_number=1,
        type="response.function_call_arguments.done",
    )
    mock_stream.side_effect = [
        EventStream(
            [
                ResponseOutputItemAddedEvent(
                    item=ResponseFunctionToolCall(
                        id="item_0",
                        arguments="",
                        call_id="call_1",
                        name="test_tool",
                        status="in_progress",
                        type="function_call",
                    ),
                    output_index=0,
                    sequence_number=0,
                    type="response.output_item.added",
                ),
                arguments_done,
                ResponseCompletedEvent(
                    response=_response(),
                    sequence_number=2,
                    type="response.completed",
                ),
            ]
        ),
        EventStream(message_events("Done")),
    ]
    mock_chat_log.mock_tool_results({"call_1": {"result": "ok"}})

    result = await conversation.async_converse(
        hass,
        "Run tool",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.speech["plain"]["speech"] == "Done"
    assert mock_stream.await_count == 2
    second_input = mock_stream.call_args.kwargs["input"]
    outputs = [item for item in second_input if item["type"] == "function_call_output"]
    assert [item["call_id"] for item in outputs] == ["call_1"]


async def test_sequential_tool_calls(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Continue through sequential provider tool turns."""
    mock_stream.side_effect = [
        EventStream(tool_events(("call_1", "test_tool", '{"step": 1}'))),
        EventStream(tool_events(("call_2", "test_tool", '{"step": 2}'))),
        EventStream(message_events("Both steps completed")),
    ]
    mock_chat_log.mock_tool_results(
        {
            "call_1": {"result": "one"},
            "call_2": {"result": "two"},
        }
    )
    result = await conversation.async_converse(
        hass,
        "Run two dependent steps",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.speech["plain"]["speech"] == "Both steps completed"
    assert mock_stream.await_count == 3


async def test_tool_failure_is_returned_to_provider(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Keep a Home Assistant tool failure explicit in the model loop."""
    mock_stream.side_effect = [
        EventStream(tool_events(("call_1", "missing_tool", "{}"))),
        EventStream(message_events("The tool failed")),
    ]
    mock_chat_log.mock_tool_results(
        {"call_1": {"error": "HomeAssistantError", "error_text": "Tool not found"}}
    )

    with caplog.at_level(logging.WARNING):
        result = await conversation.async_converse(
            hass,
            "Use a missing tool",
            mock_chat_log.conversation_id,
            Context(),
            agent_id="conversation.grok",
        )
    assert result.response.speech["plain"]["speech"] == "The tool failed"
    assert '"error":"HomeAssistantError"' in str(mock_stream.call_args.kwargs["input"])
    assert "call_1" in caplog.text


@pytest.mark.parametrize("arguments", ['{"broken"', "[]"])
async def test_invalid_tool_arguments(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    arguments: str,
) -> None:
    """Reject malformed and non-object model tool arguments."""
    mock_stream.return_value = EventStream(
        tool_events(("call_1", "test_tool", arguments))
    )
    result = await conversation.async_converse(
        hass,
        "Use a tool",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert (
        result.response.speech["plain"]["speech"]
        == f"{DEFAULT_MODEL} requested a Home Assistant tool with invalid arguments"
    )


async def test_bounded_tool_loop(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Terminate deterministic tool loops at the configured bound."""
    mock_stream.side_effect = [
        EventStream(tool_events((f"call_{index}", "test_tool", "{}")))
        for index in range(MAX_TOOL_ITERATIONS)
    ]
    mock_chat_log.mock_tool_results(
        {f"call_{index}": {"ok": True} for index in range(MAX_TOOL_ITERATIONS)}
    )
    result = await conversation.async_converse(
        hass,
        "Never stop",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert (
        result.response.speech["plain"]["speech"]
        == f"{DEFAULT_MODEL} reached the Home Assistant tool-call limit"
    )
    assert mock_stream.await_count == MAX_TOOL_ITERATIONS


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        pytest.param(
            RateLimitedError(
                "limited",
                context=ErrorContext(
                    operation=Operation.RESPONSE,
                    model=DEFAULT_MODEL,
                    status=429,
                    request_id="request-123",
                ),
            ),
            f"SpaceXAI is rate limiting requests to {DEFAULT_MODEL}. Try again later",
            id="rate-limit",
        ),
    ],
)
async def test_provider_errors(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    error: Exception,
    expected: str,
) -> None:
    """Expose translated safe provider failures."""
    mock_stream.side_effect = error
    result = await conversation.async_converse(
        hass,
        "Hello",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert result.response.speech["plain"]["speech"] == expected
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


async def test_auth_error_starts_reauthentication(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Mark unavailable and start reauthentication after session rejection."""
    mock_stream.side_effect = ReauthenticationRequiredError(
        "expired",
        context=ErrorContext(
            operation=Operation.RESPONSE,
            model=DEFAULT_MODEL,
            status=401,
        ),
    )
    result = await conversation.async_converse(
        hass,
        "Hello",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    flows = hass.config_entries.flow.async_progress_by_handler("spacexai")
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"


async def test_stalled_stream_times_out(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Cancel a provider stream that stops producing events."""

    class StalledStream:
        def __aiter__(self) -> AsyncIterator[ResponseStreamEvent]:
            return self

        async def __anext__(self) -> ResponseStreamEvent:
            await asyncio.Event().wait()
            raise StopAsyncIteration

    mock_stream.return_value = StalledStream()
    with patch("homeassistant.components.spacexai.entity.RESPONSE_TIMEOUT", 0):
        result = await conversation.async_converse(
            hass,
            "Wait",
            None,
            Context(),
            agent_id="conversation.grok",
        )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert (
        result.response.speech["plain"]["speech"]
        == f"SpaceXAI did not finish the response from {DEFAULT_MODEL} in time"
    )


async def test_cancellation_propagates(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Do not convert task cancellation into a user-facing provider error."""
    mock_stream.side_effect = asyncio.CancelledError
    with pytest.raises(asyncio.CancelledError):
        await conversation.async_converse(
            hass,
            "Cancel",
            None,
            Context(),
            agent_id="conversation.grok",
        )


async def test_unexpected_error_logging_is_sanitized(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Keep stack locations while excluding unexpected credential-like messages."""
    mock_stream.side_effect = RuntimeError(
        f"Authorization: Bearer {ACCESS_TOKEN}; refresh-token"
    )
    with caplog.at_level(logging.ERROR):
        result = await conversation.async_converse(
            hass,
            "Hello",
            None,
            Context(),
            agent_id="conversation.grok",
        )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert ACCESS_TOKEN not in caplog.text
    assert "refresh-token" not in caplog.text
    assert "_async_handle_chat_log" in caplog.text


async def test_configured_token_limit_forwarded(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Forward the subentry response-token limit."""
    subentry = next(
        entry
        for entry in setup_integration.subentries.values()
        if entry.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        setup_integration,
        subentry,
        data={**subentry.data, CONF_MAX_OUTPUT_TOKENS: 8192},
    )
    await hass.config_entries.async_reload(setup_integration.entry_id)
    await conversation.async_converse(
        hass,
        "Hello",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert mock_stream.call_args.kwargs["max_output_tokens"] == 8192


async def test_reasoning_stream(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Stream summarized reasoning and text without exposing raw reasoning."""
    reasoning_item = ResponseReasoningItem(
        id="reasoning-1",
        summary=[],
        encrypted_content="encrypted-reasoning",
        type="reasoning",
    )
    mock_stream.return_value = EventStream(
        [
            ResponseOutputItemAddedEvent(
                item=reasoning_item,
                output_index=0,
                sequence_number=0,
                type="response.output_item.added",
            ),
            ResponseReasoningSummaryTextDeltaEvent(
                delta="Checking the request",
                item_id="reasoning-1",
                output_index=0,
                sequence_number=1,
                summary_index=0,
                type="response.reasoning_summary_text.delta",
            ),
            ResponseOutputItemDoneEvent(
                item=reasoning_item,
                output_index=0,
                sequence_number=2,
                type="response.output_item.done",
            ),
            ResponseTextDeltaEvent(
                content_index=0,
                delta="Done",
                item_id="message-1",
                logprobs=[],
                output_index=1,
                sequence_number=3,
                type="response.output_text.delta",
            ),
            ResponseCompletedEvent(
                response=_response(),
                sequence_number=4,
                type="response.completed",
            ),
        ]
    )
    result = await conversation.async_converse(
        hass,
        "Think",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.speech["plain"]["speech"] == "Done"
    chat_log = hass.data[conversation.chat_log.DATA_CHAT_LOGS][result.conversation_id]
    assistant_content = chat_log.content[-1]
    assert isinstance(assistant_content, conversation.AssistantContent)
    assert assistant_content.thinking_content == "Checking the request"
    assert any(
        item["type"] == "reasoning"
        and item["encrypted_content"] == "encrypted-reasoning"
        for item in mock_stream.call_args.kwargs["input"]
    )


@pytest.mark.parametrize(
    ("event", "expected"),
    [
        pytest.param(
            ResponseIncompleteEvent(
                response=_response(
                    status="incomplete",
                    incomplete_details={"reason": "max_output_tokens"},
                ),
                sequence_number=0,
                type="response.incomplete",
            ),
            (f"SpaceXAI reached the configured output-token limit for {DEFAULT_MODEL}"),
            id="incomplete",
        ),
        pytest.param(
            ResponseFailedEvent(
                response=_response(
                    status="failed",
                    error={"code": "server_error", "message": "failed"},
                ),
                sequence_number=0,
                type="response.failed",
            ),
            (
                "SpaceXAI encountered a temporary error while using "
                f"{DEFAULT_MODEL}. Try again later"
            ),
            id="failed",
        ),
        pytest.param(
            ResponseErrorEvent(
                code="stream_error",
                message="failed",
                sequence_number=0,
                type="error",
            ),
            f"SpaceXAI rejected the request to {DEFAULT_MODEL}",
            id="error",
        ),
        pytest.param(
            ResponseErrorEvent(
                code="rate_limit_exceeded",
                message="limited",
                sequence_number=0,
                type="error",
            ),
            f"SpaceXAI is rate limiting requests to {DEFAULT_MODEL}. Try again later",
            id="rate-limit",
        ),
    ],
)
async def test_stream_lifecycle_failures(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    event: ResponseStreamEvent,
    expected: str,
) -> None:
    """Classify provider lifecycle failures."""
    mock_stream.return_value = EventStream([event])
    result = await conversation.async_converse(
        hass,
        "Hello",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert result.response.speech["plain"]["speech"] == expected


async def test_refusal_and_ignored_lifecycle_event(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Ignore known lifecycle metadata and surface provider refusal safely."""
    mock_stream.return_value = EventStream(
        [
            ResponseCreatedEvent(
                response=_response(),
                sequence_number=0,
                type="response.created",
            ),
            *message_events("Done"),
        ]
    )
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.speech["plain"]["speech"] == "Done"

    mock_stream.return_value = EventStream(
        [
            ResponseRefusalDeltaEvent(
                content_index=0,
                delta="refused",
                item_id="message",
                output_index=0,
                sequence_number=0,
                type="response.refusal.delta",
            )
        ]
    )
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert (
        result.response.speech["plain"]["speech"]
        == f"SpaceXAI rejected the request to {DEFAULT_MODEL}"
    )


async def test_completed_usage_tracing(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Consume provider completion and cached-token usage metadata."""
    mock_stream.return_value = EventStream(
        [
            *message_events("Done", complete=False),
            ResponseCompletedEvent(
                response=_response(
                    usage={
                        "input_tokens": 10,
                        "input_tokens_details": {
                            "cache_write_tokens": 0,
                            "cached_tokens": 5,
                        },
                        "output_tokens": 2,
                        "output_tokens_details": {"reasoning_tokens": 0},
                        "total_tokens": 12,
                    }
                ),
                sequence_number=3,
                type="response.completed",
            ),
        ]
    )
    with patch.object(mock_chat_log, "async_trace") as trace:
        result = await conversation.async_converse(
            hass,
            "Hello",
            mock_chat_log.conversation_id,
            Context(),
            agent_id="conversation.grok",
        )
    assert result.response.speech["plain"]["speech"] == "Done"
    trace.assert_any_call(
        {
            "stats": {
                "input_tokens": 10,
                "cached_input_tokens": 5,
                "output_tokens": 2,
            }
        }
    )


async def test_unannounced_and_missing_id_tool_calls(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Reject uncorrelated tool arguments and calls without provider item IDs."""
    mock_stream.return_value = EventStream(
        [
            ResponseFunctionCallArgumentsDoneEvent(
                arguments="{}",
                item_id="missing",
                name="tool",
                output_index=0,
                sequence_number=0,
                type="response.function_call_arguments.done",
            )
        ]
    )
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR

    mock_stream.return_value = EventStream(
        [
            ResponseOutputItemAddedEvent(
                item=ResponseFunctionToolCall(
                    arguments="",
                    call_id="call",
                    name="tool",
                    type="function_call",
                ),
                output_index=0,
                sequence_number=0,
                type="response.output_item.added",
            )
        ]
    )
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR


@pytest.mark.parametrize(
    "events",
    [
        pytest.param(message_events("partial", complete=False), id="missing-terminal"),
        pytest.param(
            [
                ResponseCompletedEvent(
                    response=_response(),
                    sequence_number=0,
                    type="response.completed",
                ),
                ResponseTextDeltaEvent(
                    content_index=0,
                    delta="late",
                    item_id="message",
                    logprobs=[],
                    output_index=0,
                    sequence_number=1,
                    type="response.output_text.delta",
                ),
            ],
            id="after-terminal",
        ),
        pytest.param(
            [
                ResponseOutputItemAddedEvent(
                    item=ResponseFunctionToolCall(
                        id="item",
                        arguments="",
                        call_id="call",
                        name="announced",
                        type="function_call",
                    ),
                    output_index=0,
                    sequence_number=0,
                    type="response.output_item.added",
                ),
                ResponseFunctionCallArgumentsDoneEvent(
                    arguments="{}",
                    item_id="item",
                    name="changed",
                    output_index=0,
                    sequence_number=1,
                    type="response.function_call_arguments.done",
                ),
            ],
            id="changed-tool-name",
        ),
        pytest.param(
            [
                ResponseOutputItemAddedEvent(
                    item=ResponseFunctionToolCall(
                        id="item-1",
                        arguments="",
                        call_id="duplicate",
                        name="tool",
                        type="function_call",
                    ),
                    output_index=0,
                    sequence_number=0,
                    type="response.output_item.added",
                ),
                ResponseOutputItemAddedEvent(
                    item=ResponseFunctionToolCall(
                        id="item-2",
                        arguments="",
                        call_id="duplicate",
                        name="tool",
                        type="function_call",
                    ),
                    output_index=1,
                    sequence_number=1,
                    type="response.output_item.added",
                ),
            ],
            id="duplicate-call-id",
        ),
        pytest.param(
            [
                ResponseOutputItemAddedEvent(
                    item=ResponseFunctionToolCall(
                        id="unfinished",
                        arguments="",
                        call_id="call",
                        name="tool",
                        type="function_call",
                    ),
                    output_index=0,
                    sequence_number=0,
                    type="response.output_item.added",
                ),
                ResponseCompletedEvent(
                    response=_response(),
                    sequence_number=1,
                    type="response.completed",
                ),
            ],
            id="unfinished-tool-call",
        ),
    ],
)
async def test_invalid_stream_state(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    events: list[ResponseStreamEvent],
) -> None:
    """Reject truncated, duplicate, and inconsistent stream state."""
    mock_stream.return_value = EventStream(events)
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR


async def test_unexpected_output_item(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Reject provider output items that are not supported."""

    class FakeUnsupported:
        """Unsupported server-side tool item."""

        type = "file_search_call"
        id = "fs_1"

    mock_stream.return_value = EventStream(
        [
            ResponseOutputItemAddedEvent.model_construct(
                item=FakeUnsupported(),
                output_index=0,
                sequence_number=0,
                type="response.output_item.added",
            )
        ]
    )
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR


async def test_code_interpreter_tool_is_server_side(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Enable SpaceXAI code interpreter and treat provider calls as external."""
    subentry = next(
        entry
        for entry in setup_integration.subentries.values()
        if entry.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        setup_integration,
        subentry,
        data={**subentry.data, CONF_CODE_INTERPRETER: True},
    )
    await hass.config_entries.async_reload(setup_integration.entry_id)
    await hass.async_block_till_done()

    item = ResponseCodeInterpreterToolCall.model_validate(
        {
            "id": "code_1",
            "code": "print(2+2)",
            "container_id": "container",
            "outputs": [{"type": "logs", "logs": "4"}],
            "status": "completed",
            "type": "code_interpreter_call",
        }
    )
    mock_stream.return_value = EventStream(
        [
            ResponseOutputItemAddedEvent(
                item=item,
                output_index=0,
                sequence_number=0,
                type="response.output_item.added",
            ),
            ResponseOutputItemDoneEvent(
                item=item,
                output_index=0,
                sequence_number=1,
                type="response.output_item.done",
            ),
            *message_events("Four", complete=True),
        ]
    )
    result = await conversation.async_converse(
        hass,
        "What is 2+2?",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.speech["plain"]["speech"] == "Four"
    tools = mock_stream.call_args.kwargs["tools"]
    assert {"type": "code_interpreter"} in tools
    assert "code_interpreter_call.outputs" in mock_stream.call_args.kwargs["include"]


async def test_x_search_tool_is_server_side(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Enable SpaceXAI X search and treat provider search calls as external."""
    subentry = next(
        entry
        for entry in setup_integration.subentries.values()
        if entry.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        setup_integration,
        subentry,
        data={**subentry.data, CONF_X_SEARCH: True},
    )
    await hass.config_entries.async_reload(setup_integration.entry_id)
    await hass.async_block_till_done()

    class FakeXSearch:
        """Minimal x_search_call stand-in for SDK-unknown types."""

        type = "x_search_call"
        id = "xs_1"
        status = "completed"
        action = {"type": "search", "query": "xAI"}

    mock_stream.return_value = EventStream(
        [
            ResponseOutputItemAddedEvent.model_construct(
                item=FakeXSearch(),
                output_index=0,
                sequence_number=0,
                type="response.output_item.added",
            ),
            ResponseOutputItemDoneEvent.model_construct(
                item=FakeXSearch(),
                output_index=0,
                sequence_number=1,
                type="response.output_item.done",
            ),
            *message_events("Trending", complete=True),
        ]
    )
    result = await conversation.async_converse(
        hass,
        "What are people saying?",
        None,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.speech["plain"]["speech"] == "Trending"
    tools = mock_stream.call_args.kwargs["tools"]
    assert {"type": "x_search"} in tools


async def test_stream_transport_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Classify SDK errors raised after the streaming response starts."""

    class FailingStream:
        def __aiter__(self) -> AsyncIterator[ResponseStreamEvent]:
            return self

        async def __anext__(self) -> ResponseStreamEvent:
            raise APIConnectionError(
                request=httpx.Request("POST", "https://api.x.ai/v1/responses")
            )

    mock_stream.return_value = FailingStream()
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert (
        result.response.speech["plain"]["speech"]
        == f"Home Assistant could not connect to SpaceXAI while using {DEFAULT_MODEL}"
    )


async def test_template_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Return the ChatLog error when prompt rendering fails."""
    subentry = next(
        entry
        for entry in setup_integration.subentries.values()
        if entry.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        setup_integration,
        subentry,
        data={**subentry.data, CONF_PROMPT: "{{ invalid("},
    )
    await hass.config_entries.async_reload(setup_integration.entry_id)
    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR
    mock_stream.assert_not_awaited()


async def test_unavailable_and_recovery_logged_once(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Log one outage transition and one recovery transition."""
    mock_stream.side_effect = RateLimitedError(
        "limited",
        context=ErrorContext(operation=Operation.RESPONSE, model=DEFAULT_MODEL),
    )
    with caplog.at_level(logging.INFO):
        await conversation.async_converse(
            hass, "Hello", None, Context(), agent_id="conversation.grok"
        )
        await conversation.async_converse(
            hass, "Again", None, Context(), agent_id="conversation.grok"
        )
        state = hass.states.get("conversation.grok")
        assert state is not None
        assert state.state == STATE_UNAVAILABLE
        mock_stream.side_effect = None
        mock_stream.return_value = EventStream(message_events("Recovered"))
        await conversation.async_converse(
            hass, "Retry", None, Context(), agent_id="conversation.grok"
        )
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert caplog.text.count("SpaceXAI is unavailable:") == 1
    assert caplog.text.count("SpaceXAI is available again") == 1


@pytest.mark.usefixtures("setup_credentials")
async def test_text_without_announced_message_item(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Open an assistant turn when text arrives before an output item."""
    events = [
        ResponseTextDeltaEvent(
            content_index=0,
            delta="Hello",
            item_id="msg_1",
            logprobs=[],
            output_index=0,
            sequence_number=0,
            type="response.output_text.delta",
        ),
        ResponseReasoningSummaryTextDeltaEvent(
            delta="thinking",
            item_id="reason_1",
            output_index=0,
            sequence_number=1,
            summary_index=0,
            type="response.reasoning_summary_text.delta",
        ),
        *message_events("", complete=True)[2:],
    ]
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_stream_response",
        new_callable=AsyncMock,
        return_value=EventStream(events),
    ):
        result = await conversation.async_converse(
            hass, "hello", None, Context(), agent_id="conversation.grok"
        )
    assert result.response.speech["plain"]["speech"] == "Hello"


@pytest.mark.usefixtures("setup_credentials")
async def test_unexpected_stream_event_type(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Reject a stream event the integration does not model."""

    class _UnmodelledEvent:
        type = "response.unmodelled"

    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_stream_response",
        new_callable=AsyncMock,
        return_value=EventStream([_UnmodelledEvent()]),
    ):
        result = await conversation.async_converse(
            hass, "hello", None, Context(), agent_id="conversation.grok"
        )
    assert result.response.error_code == "unknown"


@pytest.mark.parametrize(
    ("side_effect", "expected_state"),
    [
        pytest.param(TimeoutError, STATE_UNAVAILABLE, id="timeout"),
        pytest.param(
            APIConnectionError(request=httpx.Request("POST", "https://api.x.ai/v1")),
            STATE_UNAVAILABLE,
            id="connection",
        ),
    ],
)
@pytest.mark.usefixtures("setup_credentials")
async def test_stream_request_failures(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_chat_log: MockChatLog,  # noqa: F811
    side_effect: Exception,
    expected_state: str,
) -> None:
    """Translate failures raised while starting the provider stream."""
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_stream_response",
        new_callable=AsyncMock,
        side_effect=side_effect,
    ):
        result = await conversation.async_converse(
            hass, "hello", None, Context(), agent_id="conversation.grok"
        )
    assert result.response.error_code == "unknown"
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert state.state == expected_state


@pytest.mark.usefixtures("setup_credentials")
async def test_foreign_subentry_creates_no_entity(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Ignore subentry types the conversation platform does not own."""
    hass.config_entries.async_add_subentry(
        mock_config_entry,
        ConfigSubentry(
            data={},
            subentry_type="unsupported",
            title="Unsupported",
            unique_id=None,
        ),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    conversation_entities = [
        state.entity_id
        for state in hass.states.async_all("conversation")
        if state.entity_id.startswith("conversation.grok")
    ]
    assert conversation_entities == ["conversation.grok"]


@pytest.mark.usefixtures("setup_credentials")
async def test_reasoning_summary_before_assistant_turn(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Open an assistant turn when reasoning arrives before any output item."""
    events = [
        ResponseReasoningSummaryTextDeltaEvent(
            delta="planning",
            item_id="reason_1",
            output_index=0,
            sequence_number=0,
            summary_index=0,
            type="response.reasoning_summary_text.delta",
        ),
        ResponseOutputItemDoneEvent(
            item=ResponseReasoningItem(
                id="reason_1",
                summary=[],
                type="reasoning",
            ),
            output_index=0,
            sequence_number=1,
            type="response.output_item.done",
        ),
        ResponseOutputItemDoneEvent(
            item=ResponseReasoningItem(
                id="reason_2",
                summary=[],
                type="reasoning",
            ),
            output_index=1,
            sequence_number=2,
            type="response.output_item.done",
        ),
        *message_events("Done")[:2],
        *message_events("Done")[2:],
    ]
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_stream_response",
        new_callable=AsyncMock,
        return_value=EventStream(events),
    ):
        result = await conversation.async_converse(
            hass, "hello", None, Context(), agent_id="conversation.grok"
        )
    assert result.response.speech["plain"]["speech"] == "Done"
