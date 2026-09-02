"""Tests for SpaceXAI conversation."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from spacexai_subscription_client import (
    Attachment,
    AuthenticationError,
    BuiltinTool,
    Completion,
    InvalidResponseError,
    Message,
    SpaceXAISubscriptionError,
    ToolCall,
    ToolResult,
)

from homeassistant.components import conversation
from homeassistant.components.spacexai.const import (
    DOMAIN,
    MAX_ATTACHMENT_SIZE,
    MAX_TOOL_ITERATIONS,
)
from homeassistant.components.spacexai.conversation import (
    _async_convert_content,
    _convert_content,
    _prepare_attachments,
)
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


async def test_prepare_attachments(hass: HomeAssistant, tmp_path: Path) -> None:
    """Load supported attachments from the latest user message."""
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    content = conversation.UserContent(
        "Describe this",
        [conversation.Attachment("media-id", "image/png", image)],
    )

    assert await _async_convert_content(hass, [content]) == [
        Message(
            "user", "Describe this", (Attachment("image.png", "image/png", b"image"),)
        )
    ]


async def test_only_latest_message_attachments_are_loaded(
    hass: HomeAssistant, tmp_path: Path
) -> None:
    """Ignore attachment paths retained on older conversation turns."""
    content: list[conversation.Content] = [
        conversation.UserContent(
            "Old",
            [conversation.Attachment("missing", "image/png", tmp_path / "missing.png")],
        ),
        conversation.AssistantContent("conversation.grok", "Reply"),
        conversation.UserContent("New"),
    ]

    assert await _async_convert_content(hass, content) == [
        Message("user", "Old"),
        Message("assistant", "Reply"),
        Message("user", "New"),
    ]


@pytest.mark.parametrize(
    ("path", "media_type", "translation_key"),
    [
        pytest.param(
            Path("missing.png"), "image/png", "attachment_unavailable", id="missing"
        ),
        pytest.param(
            Path("data.txt"), "text/plain", "unsupported_attachment", id="type"
        ),
    ],
)
def test_reject_invalid_attachment(
    path: Path, media_type: str, translation_key: str
) -> None:
    """Reject unavailable and unsupported attachments."""
    with pytest.raises(HomeAssistantError) as err:
        _prepare_attachments([(path, media_type)])

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == translation_key


def test_reject_large_attachment(tmp_path: Path) -> None:
    """Reject attachments larger than the provider limit."""
    path = tmp_path / "large.png"
    with path.open("wb") as file:
        file.truncate(MAX_ATTACHMENT_SIZE + 1)

    with pytest.raises(HomeAssistantError) as err:
        _prepare_attachments([(path, "image/png")])

    assert err.value.translation_key == "attachment_too_large"


def test_reject_empty_attachment(tmp_path: Path) -> None:
    """Reject an empty attachment before calling the client."""
    path = tmp_path / "empty.png"
    path.touch()

    with pytest.raises(HomeAssistantError) as err:
        _prepare_attachments([(path, "image/png")])

    assert err.value.translation_key == "attachment_empty"


def test_reject_attachments_over_combined_limit(tmp_path: Path) -> None:
    """Bound memory used by multiple attachments."""
    first = tmp_path / "first.png"
    second = tmp_path / "second.png"
    first.write_bytes(b"123")
    second.write_bytes(b"456")

    with (
        patch("homeassistant.components.spacexai.conversation.MAX_ATTACHMENT_SIZE", 5),
        pytest.raises(HomeAssistantError) as err,
    ):
        _prepare_attachments([(first, "image/png"), (second, "image/png")])

    assert err.value.translation_key == "attachment_too_large"


async def test_provider_tools(
    hass: HomeAssistant,
    mock_config_entry_with_provider_tools: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Enable only the configured provider-hosted tools."""
    mock_spacexai_subscription_client.async_create_response.return_value = (
        _text_response("Done")
    )
    await setup_integration(hass, mock_config_entry_with_provider_tools)

    await conversation.async_converse(
        hass,
        "Research this",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert mock_spacexai_subscription_client.async_create_response.call_args.kwargs[
        "tools"
    ] == [
        BuiltinTool("web_search"),
        BuiltinTool("x_search"),
        BuiltinTool("code_interpreter"),
    ]
