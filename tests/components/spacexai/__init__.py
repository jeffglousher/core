"""Test helpers for SpaceXAI."""

from collections.abc import AsyncIterator, Iterable

from openai.types.responses import (
    Response,
    ResponseCompletedEvent,
    ResponseFunctionCallArgumentsDoneEvent,
    ResponseFunctionToolCall,
    ResponseOutputItemAddedEvent,
    ResponseOutputMessage,
    ResponseStreamEvent,
    ResponseTextDeltaEvent,
)


class EventStream:
    """Small deterministic async event stream."""

    def __init__(self, events: Iterable[ResponseStreamEvent]) -> None:
        """Initialize the stream."""
        self._events = iter(events)

    def __aiter__(self) -> AsyncIterator[ResponseStreamEvent]:
        """Return the event iterator."""
        return self

    async def __anext__(self) -> ResponseStreamEvent:
        """Return the next event."""
        try:
            return next(self._events)
        except StopIteration as err:
            raise StopAsyncIteration from err


def _completed_event(sequence_number: int) -> ResponseCompletedEvent:
    """Build a terminal response event."""
    return ResponseCompletedEvent(
        response=Response.model_validate(
            {
                "id": "response-123",
                "created_at": 1,
                "model": "grok-4.5",
                "object": "response",
                "output": [],
                "parallel_tool_calls": True,
                "tool_choice": "auto",
                "tools": [],
                "status": "completed",
                "usage": None,
            }
        ),
        sequence_number=sequence_number,
        type="response.completed",
    )


def message_events(text: str, *, complete: bool = True) -> list[ResponseStreamEvent]:
    """Build a streaming assistant text response."""
    events: list[ResponseStreamEvent] = [
        ResponseOutputItemAddedEvent(
            item=ResponseOutputMessage(
                id="msg_1",
                content=[],
                role="assistant",
                status="in_progress",
                type="message",
            ),
            output_index=0,
            sequence_number=0,
            type="response.output_item.added",
        ),
        ResponseTextDeltaEvent(
            content_index=0,
            delta=text,
            item_id="msg_1",
            logprobs=[],
            output_index=0,
            sequence_number=1,
            type="response.output_text.delta",
        ),
    ]
    if complete:
        events.append(_completed_event(2))
    return events


def tool_events(
    *calls: tuple[str, str, str],
    complete: bool = True,
) -> list[ResponseStreamEvent]:
    """Build one assistant response containing one or more tool calls."""
    events: list[ResponseStreamEvent] = []
    for index, (call_id, name, arguments) in enumerate(calls):
        item_id = f"item_{index}"
        events.extend(
            (
                ResponseOutputItemAddedEvent(
                    item=ResponseFunctionToolCall(
                        id=item_id,
                        arguments="",
                        call_id=call_id,
                        name=name,
                        status="in_progress",
                        type="function_call",
                    ),
                    output_index=index,
                    sequence_number=index * 2,
                    type="response.output_item.added",
                ),
                ResponseFunctionCallArgumentsDoneEvent(
                    arguments=arguments,
                    item_id=item_id,
                    name=name,
                    output_index=index,
                    sequence_number=index * 2 + 1,
                    type="response.function_call_arguments.done",
                ),
            )
        )
    if complete:
        events.append(_completed_event(len(calls) * 2))
    return events
