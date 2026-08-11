"""Tests for the SpaceXAI AI Task platform."""

from unittest.mock import AsyncMock, patch

from openai.types.responses import Response, ResponseCompletedEvent
import pytest
import voluptuous as vol

from homeassistant.components import ai_task
from homeassistant.components.spacexai.const import DEFAULT_MODEL, DOMAIN
from homeassistant.components.spacexai.errors import (
    ErrorContext,
    Operation,
    RateLimitedError,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, selector

from . import EventStream, message_events

from tests.common import MockConfigEntry

ENTITY_ID = "ai_task.grok_ai_task"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_data(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Generate plain-text AI Task data through SpaceXAI."""
    entity_entry = entity_registry.async_get(ENTITY_ID)
    assert entity_entry is not None
    assert entity_entry.translation_key == "ai_task_data"
    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert (
        state.attributes["supported_features"]
        == ai_task.AITaskEntityFeature.GENERATE_DATA
    )
    ai_task_subentry = next(
        subentry
        for subentry in setup_integration.subentries.values()
        if subentry.subentry_type == "ai_task_data"
    )
    assert entity_entry.config_subentry_id == ai_task_subentry.subentry_id

    mock_stream.return_value = EventStream(message_events("The test data"))
    result = await ai_task.async_generate_data(
        hass,
        task_name="Test Task",
        entity_id=ENTITY_ID,
        instructions="Generate test data",
    )
    assert result.data == "The test data"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_structured_data(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Parse structured AI Task JSON responses."""
    mock_stream.return_value = EventStream(
        message_events('{"value": 42, "tags": ["a"], "optional": null}')
    )
    result = await ai_task.async_generate_data(
        hass,
        task_name="Structured Task",
        entity_id=ENTITY_ID,
        instructions="Return JSON",
        structure=vol.Schema(
            {
                vol.Required("value"): int,
                vol.Required("tags"): [str],
                vol.Optional("optional"): str,
            }
        ),
    )
    assert result.data == {"value": 42, "tags": ["a"], "optional": None}
    text = mock_stream.call_args.kwargs["text"]
    assert text["format"]["type"] == "json_schema"
    assert text["format"]["name"] == "structured_task"
    assert text["format"]["schema"]["additionalProperties"] is False
    assert "optional" in text["format"]["schema"]["required"]
    assert text["format"]["schema"]["properties"]["tags"]["type"] == "array"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_structured_empty_object_schema(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Normalize empty object schemas for Responses API structured output."""
    mock_stream.return_value = EventStream(message_events("{}"))
    result = await ai_task.async_generate_data(
        hass,
        task_name="Empty Object",
        entity_id=ENTITY_ID,
        instructions="Return an empty object",
        structure=vol.Schema({}),
    )
    assert result.data == {}
    schema = mock_stream.call_args.kwargs["text"]["format"]["schema"]
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_structured_array_schema(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Normalize array-root schemas for Responses API structured output."""
    mock_stream.return_value = EventStream(message_events('["a", "b"]'))
    result = await ai_task.async_generate_data(
        hass,
        task_name="Array Root",
        entity_id=ENTITY_ID,
        instructions="Return a string array",
        structure=vol.Schema([str]),
    )
    assert result.data == ["a", "b"]
    schema = mock_stream.call_args.kwargs["text"]["format"]["schema"]
    assert schema["type"] == "array"
    assert "items" in schema


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_invalid_structured_data(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Fail when structured AI Task output is not valid JSON."""
    mock_stream.return_value = EventStream(message_events("not-json"))
    with pytest.raises(HomeAssistantError) as raised:
        await ai_task.async_generate_data(
            hass,
            task_name="Structured Task",
            entity_id=ENTITY_ID,
            instructions="Return JSON",
            structure=vol.Schema({vol.Required("value"): int}),
        )
    assert raised.value.translation_domain == DOMAIN
    assert raised.value.translation_key == "json_parse_error"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_data_provider_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Surface translated provider failures from AI Task."""
    mock_stream.side_effect = RateLimitedError(
        "limited",
        context=ErrorContext(operation=Operation.RESPONSE, model=DEFAULT_MODEL),
    )
    with pytest.raises(HomeAssistantError) as raised:
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Generate test data",
        )
    assert raised.value.translation_key == "rate_limited"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_data_missing_assistant_content(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Fail when the provider completes without assistant content."""
    mock_stream.return_value = EventStream(
        [
            ResponseCompletedEvent(
                response=Response.model_validate(
                    {
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
                ),
                sequence_number=0,
                type="response.completed",
            )
        ]
    )
    with pytest.raises(HomeAssistantError) as raised:
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Generate test data",
        )
    assert raised.value.translation_key == "response_not_found"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_data_unexpected_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Translate an unexpected failure on the AI Task path."""
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_stream_response",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Generate test data",
        )
    assert raised.value.translation_key == "unexpected_provider_failure"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_structured_data_optional_and_nested(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Make optional fields nullable and required for Responses structured output."""
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_stream_response",
        new_callable=AsyncMock,
        return_value=EventStream(message_events('{"name": null, "tags": []}')),
    ) as stream:
        result = await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Generate test data",
            structure=vol.Schema(
                {
                    vol.Optional("name"): selector.TextSelector(),
                    vol.Required("tags"): selector.SelectSelector(
                        selector.SelectSelectorConfig(options=["a", "b"], multiple=True)
                    ),
                }
            ),
        )
    assert result.data == {"name": None, "tags": []}
    schema = stream.call_args.kwargs["text"]["format"]["schema"]
    assert schema["required"] == ["tags", "name"]
    assert schema["properties"]["name"]["type"] == ["string", "null"]
    assert schema["additionalProperties"] is False
