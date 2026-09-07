"""Tests for SpaceXAI conversation."""

import json
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
    PermissionDeniedError,
    SpaceXAISubscriptionError,
    ToolCall,
    ToolResult,
)

from homeassistant.components import conversation
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.components.spacexai.const import (
    MAX_ATTACHMENT_SIZE,
    MAX_TOOL_ITERATIONS,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import intent
from homeassistant.setup import async_setup_component

from . import setup_integration

from tests.common import MockConfigEntry, async_mock_service
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
    assert call["input_data"][0] == Message(
        "developer", mock_chat_log.content[0].content
    )
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


@pytest.mark.parametrize(
    ("exposed", "expected_targets", "expected_error"),
    [
        pytest.param(True, [["light.desk"]], None, id="exposed"),
        pytest.param(False, [], "MatchFailedError", id="not_exposed"),
    ],
)
async def test_assist_tool_respects_entity_exposure(
    hass: HomeAssistant,
    mock_config_entry_with_assist: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    exposed: bool,
    expected_targets: list[list[str]],
    expected_error: str | None,
) -> None:
    """Execute real Assist tools only for exposed entities."""
    assert await async_setup_component(hass, "intent", {})
    hass.states.async_set("light.desk", "off", {"friendly_name": "Desk"})
    hass.states.async_set("light.hall", "off", {"friendly_name": "Hall"})
    async_expose_entity(hass, conversation.DOMAIN, "light.desk", exposed)
    async_expose_entity(hass, conversation.DOMAIN, "light.hall", True)
    calls = async_mock_service(hass, "light", "turn_on")
    mock_spacexai_subscription_client.async_create_response.side_effect = [
        Completion(
            "",
            (ToolCall("call-1", "intent__HassTurnOn", {"name": "Desk"}),),
        ),
        _text_response("Request handled"),
    ]
    await setup_integration(hass, mock_config_entry_with_assist)

    result = await conversation.async_converse(
        hass, "Turn on Desk", None, Context(), agent_id="conversation.grok"
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert [call.data["entity_id"] for call in calls] == expected_targets
    requests = mock_spacexai_subscription_client.async_create_response.call_args_list
    assert len(requests) == 2
    tools = {tool.name: tool for tool in requests[0].kwargs["tools"]}
    assert tools["intent__HassTurnOn"].parameters["type"] == "object"
    tool_results = [
        item
        for item in requests[1].kwargs["input_data"]
        if isinstance(item, ToolResult)
    ]
    assert len(tool_results) == 1
    assert json.loads(tool_results[0].output).get("error") == expected_error


async def test_conversation_without_assist_does_not_offer_tools(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Keep provider requests tool-free when Assist access is disabled."""
    mock_spacexai_subscription_client.async_create_response.return_value = (
        _text_response("Hello")
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass, "Hello", None, Context(), agent_id="conversation.grok"
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert (
        mock_spacexai_subscription_client.async_create_response.call_args.kwargs[
            "tools"
        ]
        == []
    )


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
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"
    assert flows[0]["step_id"] == "reauth_confirm"


async def test_permission_denied_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Return an intent error when the account cannot use the subscription API."""
    mock_spacexai_subscription_client.async_create_response.side_effect = (
        PermissionDeniedError
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


@pytest.mark.parametrize(
    ("media_type", "expected_media_type"),
    [
        pytest.param("image/png", "image/png", id="png"),
        pytest.param("image/jpg", "image/jpeg", id="jpeg_alias"),
    ],
)
async def test_conversation_with_attachment(
    hass: HomeAssistant,
    tmp_path: Path,
    media_type: str,
    expected_media_type: str,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Pass attachments from the current conversation turn to the client."""
    image = tmp_path / "image.png"
    image.write_bytes(b"image")
    mock_chat_log.async_add_user_content(
        conversation.UserContent(
            "Describe this",
            [conversation.Attachment("media-id", media_type, image)],
        )
    )
    mock_spacexai_subscription_client.async_create_response.return_value = (
        _text_response("An image")
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Describe this",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert mock_spacexai_subscription_client.async_create_response.call_args.kwargs[
        "input_data"
    ][-1] == Message(
        "user",
        "Describe this",
        (Attachment("image.png", expected_media_type, b"image"),),
    )


@pytest.mark.parametrize(
    ("data", "message"),
    [
        pytest.param(
            b"", "The attachment changing.png is empty", id="emptied_after_stat"
        ),
        pytest.param(
            b"x" * (MAX_ATTACHMENT_SIZE + 1),
            "The selected attachments exceed the 20 MiB limit at changing.png",
            id="grew_after_stat",
        ),
    ],
)
async def test_attachment_changed_during_read(
    hass: HomeAssistant,
    tmp_path: Path,
    data: bytes,
    message: str,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Reject changed files through the conversation interface."""
    path = tmp_path / "changing.png"
    path.write_bytes(b"123")
    mock_chat_log.async_add_user_content(
        conversation.UserContent(
            "Describe this",
            [conversation.Attachment("media-id", "image/png", path)],
        )
    )
    await setup_integration(hass, mock_config_entry)

    with patch("pathlib.Path.open") as mock_open:
        mock_open.return_value.__enter__.return_value.read.return_value = data
        result = await conversation.async_converse(
            hass,
            "Describe this",
            mock_chat_log.conversation_id,
            Context(),
            agent_id="conversation.grok",
        )

    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert result.response.speech["plain"]["speech"] == message
    mock_spacexai_subscription_client.async_create_response.assert_not_awaited()
    mock_open.return_value.__enter__.return_value.read.assert_called_once_with(
        MAX_ATTACHMENT_SIZE + 1
    )


async def test_only_latest_message_attachments_are_loaded(
    hass: HomeAssistant,
    tmp_path: Path,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Ignore unavailable attachments from earlier conversation turns."""
    mock_chat_log.content.extend(
        [
            conversation.UserContent(
                "Old",
                [
                    conversation.Attachment(
                        "missing", "image/png", tmp_path / "missing.png"
                    )
                ],
            ),
            conversation.AssistantContent("conversation.grok", "Reply"),
        ]
    )
    mock_spacexai_subscription_client.async_create_response.return_value = (
        _text_response("Done")
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "New",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ACTION_DONE
    assert mock_spacexai_subscription_client.async_create_response.call_args.kwargs[
        "input_data"
    ][1:] == [
        Message("user", "Old"),
        Message("assistant", "Reply"),
        Message("user", "New"),
    ]


@pytest.mark.parametrize(
    ("filename", "media_type", "message"),
    [
        pytest.param(
            "missing.png",
            "image/png",
            "The attachment missing.png could not be read",
            id="missing",
        ),
        pytest.param(
            "data.txt",
            "text/plain",
            "The attachment data.txt is not a JPEG image, PNG image, or PDF",
            id="type",
        ),
    ],
)
async def test_reject_invalid_attachment(
    hass: HomeAssistant,
    tmp_path: Path,
    filename: str,
    media_type: str,
    message: str,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Reject unsupported or unavailable files without calling the provider."""
    mock_chat_log.async_add_user_content(
        conversation.UserContent(
            "Describe this",
            [conversation.Attachment("media-id", media_type, tmp_path / filename)],
        )
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Describe this",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert result.response.speech["plain"]["speech"] == message
    mock_spacexai_subscription_client.async_create_response.assert_not_awaited()


@pytest.mark.parametrize(
    ("size", "message"),
    [
        pytest.param(0, "The attachment image.png is empty", id="empty"),
        pytest.param(
            MAX_ATTACHMENT_SIZE + 1,
            "The selected attachments exceed the 20 MiB limit at image.png",
            id="too_large",
        ),
    ],
)
async def test_reject_attachment_size(
    hass: HomeAssistant,
    tmp_path: Path,
    size: int,
    message: str,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Reject empty and oversized attachments before reading their bytes."""
    path = tmp_path / "image.png"
    with path.open("wb") as file:
        file.truncate(size)
    mock_chat_log.async_add_user_content(
        conversation.UserContent(
            "Describe this",
            [conversation.Attachment("media-id", "image/png", path)],
        )
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Describe this",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert result.response.speech["plain"]["speech"] == message
    mock_spacexai_subscription_client.async_create_response.assert_not_awaited()


async def test_reject_attachments_over_combined_limit(
    hass: HomeAssistant,
    tmp_path: Path,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    mock_chat_log: MockChatLog,  # noqa: F811
) -> None:
    """Bound total attachment bytes across multiple files."""
    paths = [tmp_path / "first.png", tmp_path / "second.png"]
    for path in paths:
        with path.open("wb") as file:
            file.truncate(MAX_ATTACHMENT_SIZE // 2 + 1)
    mock_chat_log.async_add_user_content(
        conversation.UserContent(
            "Describe this",
            [conversation.Attachment(path.name, "image/png", path) for path in paths],
        )
    )
    await setup_integration(hass, mock_config_entry)

    result = await conversation.async_converse(
        hass,
        "Describe this",
        mock_chat_log.conversation_id,
        Context(),
        agent_id="conversation.grok",
    )

    assert result.response.response_type is intent.IntentResponseType.ERROR
    assert result.response.speech["plain"]["speech"] == (
        "The selected attachments exceed the 20 MiB limit at second.png"
    )
    mock_spacexai_subscription_client.async_create_response.assert_not_awaited()


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
