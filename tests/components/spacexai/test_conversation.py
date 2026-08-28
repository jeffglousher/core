"""Tests for SpaceXAI conversation."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from spacexai_subscription_client import (
    AuthenticationError,
    Completion,
    InvalidResponseError,
    Message,
    SpaceXAISubscriptionError,
    ToolCall,
    ToolResult,
)

from homeassistant.components import conversation
from homeassistant.components.spacexai.const import DOMAIN, MAX_TOOL_ITERATIONS
from homeassistant.components.spacexai.conversation import _convert_content
from homeassistant.core import Context, HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import intent

from . import setup_integration

from tests.common import MockConfigEntry
from tests.components.conversation import MockChatLog, mock_chat_log  # noqa: F401


def _text_response(text: str) -> Completion:
    """Return a client response containing assistant text."""
    return Completion(text, ())


def _tool_response() -> Completion:
    """Return a client response containing a Home Assistant tool call."""
    return Completion("", (ToolCall("call-1", "test_tool", {"param1": "call1"}),))


async def test_conversation_response(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Return a Grok response through the Conversation platform."""
    mock_spacexai_subscription_client.async_create_response.return_value = (
        _text_response("Hello from Grok")
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert result.response.speech["plain"]["speech"] == "Hello from Grok"
    call = mock_spacexai_subscription_client.async_create_response.call_args.kwargs
    assert call["model"] == "grok-4.6"
    assert mock_spacexai_subscription_client.async_create_response.call_args.args == (
        "access-token",
    )


async def test_home_assistant_tool_call(
    hass: HomeAssistant,
    mock_config_entry_with_assist: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Execute a Home Assistant tool and send its result back to Grok."""
    mock_chat_log.mock_tool_results({"call-1": "tool result"})
    mock_spacexai_subscription_client.async_create_response.side_effect = [
        _tool_response(),
        _text_response("The tool succeeded"),
    ]
    await setup_integration(hass, mock_config_entry_with_assist)

    result = await conversation.async_converse(
        hass,
        "Call the tool",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert mock_spacexai_subscription_client.async_create_response.await_count == 2
    second_input = (
        mock_spacexai_subscription_client.async_create_response.call_args_list[
            1
        ].kwargs["input_data"]
    )
    assert ToolResult("call-1", '"tool result"') in second_input


async def test_empty_response(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Return an intent error for an empty provider response."""
    mock_spacexai_subscription_client.async_create_response.side_effect = (
        InvalidResponseError
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR


async def test_authentication_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Return an intent error when the OAuth access token is rejected."""
    mock_spacexai_subscription_client.async_create_response.side_effect = (
        AuthenticationError
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )
    assert result.response.response_type is intent.IntentResponseType.ERROR


async def test_api_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Return an intent error when the provider request fails."""
    mock_spacexai_subscription_client.async_create_response.side_effect = (
        SpaceXAISubscriptionError
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR


async def test_llm_data_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Return the conversation error raised while preparing LLM data."""
    error_response = intent.IntentResponse(language="en")
    mock_chat_log.async_provide_llm_data = AsyncMock(
        side_effect=conversation.ConverseError(
            "failed", mock_chat_log.conversation_id or "", error_response
        )
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Hello",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response is error_response
    mock_spacexai_subscription_client.async_create_response.assert_not_awaited()


async def test_tool_iteration_limit(
    hass: HomeAssistant,
    mock_config_entry_with_assist: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Stop a provider that repeatedly requests tools."""
    mock_chat_log.mock_tool_results({"call-1": "tool result"})
    mock_spacexai_subscription_client.async_create_response.return_value = (
        _tool_response()
    )
    await setup_integration(hass, mock_config_entry_with_assist)

    result = await conversation.async_converse(
        hass,
        "Keep calling the tool",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert (
        mock_spacexai_subscription_client.async_create_response.await_count
        == MAX_TOOL_ITERATIONS
    )


def test_convert_system_content() -> None:
    """Map a Home Assistant system prompt to a developer message."""
    assert _convert_content([conversation.SystemContent("Be helpful")]) == [
        Message("developer", "Be helpful")
    ]


def test_attachments_not_supported() -> None:
    """Reject attachments before making a provider request."""
    content = conversation.UserContent(
        "Describe this",
        [conversation.Attachment("media-id", "image/png", Path("image.png"))],
    )

    with pytest.raises(HomeAssistantError) as err:
        _convert_content([content])

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "attachments_not_supported"
