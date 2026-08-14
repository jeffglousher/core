"""Tests for the SpaceXAI AI Task platform."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from openai.types.responses import Response, ResponseCompletedEvent
import pytest
import voluptuous as vol

from homeassistant.components import ai_task, media_source
from homeassistant.components.spacexai.client import (
    GeneratedImage,
    ModelInfo,
    ProviderSnapshot,
)
from homeassistant.components.spacexai.const import (
    DEFAULT_IMAGE_ASPECT_RATIO,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_IMAGE_RESOLUTION,
    DEFAULT_MODEL,
    DOMAIN,
    MAX_ATTACHMENT_BYTES,
)
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
    assert state.attributes["supported_features"] == (
        ai_task.AITaskEntityFeature.GENERATE_DATA
        | ai_task.AITaskEntityFeature.SUPPORT_ATTACHMENTS
        | ai_task.AITaskEntityFeature.GENERATE_IMAGE
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
    assert raised.value.translation_key == "malformed_provider_response"


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


async def test_generate_image(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Generate an image through the Imagine API."""
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_generate_image",
            new_callable=AsyncMock,
            return_value=GeneratedImage(
                image_data=b"fake-image",
                mime_type="image/jpeg",
                model=DEFAULT_IMAGE_MODEL,
                revised_prompt="A revised prompt",
            ),
        ) as mock_generate,
        patch(
            "homeassistant.components.media_source.local_source.LocalSource.async_upload_media",
            return_value="media-source://ai_task/image/test.jpg",
        ) as mock_upload,
    ):
        result = await ai_task.async_generate_image(
            hass,
            task_name="Image Task",
            entity_id=ENTITY_ID,
            instructions="Draw a rocket",
        )
    assert result["mime_type"] == "image/jpeg"
    assert result["model"] == DEFAULT_IMAGE_MODEL
    assert result["revised_prompt"] == "A revised prompt"
    mock_generate.assert_awaited_once()
    assert mock_generate.await_args.kwargs["prompt"] == "Draw a rocket"
    assert mock_generate.await_args.kwargs["model"] == DEFAULT_IMAGE_MODEL
    assert mock_generate.await_args.kwargs["aspect_ratio"] == DEFAULT_IMAGE_ASPECT_RATIO
    assert mock_generate.await_args.kwargs["resolution"] == DEFAULT_IMAGE_RESOLUTION
    image_data = mock_upload.call_args[0][1]
    assert image_data.file.getvalue() == b"fake-image"
    assert image_data.content_type == "image/jpeg"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_image_with_attachments_edits(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Edit an image when the AI Task includes image attachments."""
    with (
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            return_value=media_source.PlayMedia(
                url="http://example.com/bike.jpg",
                mime_type="image/jpeg",
                path=Path("bike.jpg"),
            ),
        ),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "pathlib.Path.stat",
            return_value=SimpleNamespace(st_size=7),
        ),
        patch("pathlib.Path.read_bytes", return_value=b"payload"),
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_edit_image",
            new_callable=AsyncMock,
            return_value=GeneratedImage(
                image_data=b"edited-image",
                mime_type="image/jpeg",
                model=DEFAULT_IMAGE_MODEL,
                revised_prompt="a red bicycle at noon",
            ),
        ) as mock_edit,
        patch(
            "homeassistant.components.media_source.local_source.LocalSource.async_upload_media",
            return_value="media-source://ai_task/image/edited.jpg",
        ),
    ):
        result = await ai_task.async_generate_image(
            hass,
            task_name="Edit Image",
            entity_id=ENTITY_ID,
            instructions="make it noon",
            attachments=[{"media_content_id": "media-source://media/bike.jpg"}],
        )
    assert result["revised_prompt"] == "a red bicycle at noon"
    mock_edit.assert_awaited_once()
    assert mock_edit.await_args.kwargs["prompt"] == "make it noon"
    assert mock_edit.await_args.kwargs["model"] == DEFAULT_IMAGE_MODEL
    assert mock_edit.await_args.kwargs["images"] == [
        "data:image/jpeg;base64,cGF5bG9hZA=="
    ]


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_image_provider_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Translate a classified provider failure on the image path."""
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_generate_image",
            new_callable=AsyncMock,
            side_effect=RateLimitedError(
                "slow down",
                context=ErrorContext(operation=Operation.IMAGE, model=DEFAULT_MODEL),
            ),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await ai_task.async_generate_image(
            hass,
            task_name="Test Image",
            entity_id=ENTITY_ID,
            instructions="A red bicycle",
        )
    assert raised.value.translation_key == "rate_limited"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_image_unexpected_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Translate an unexpected failure on the image path."""
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_generate_image",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await ai_task.async_generate_image(
            hass,
            task_name="Test Image",
            entity_id=ENTITY_ID,
            instructions="A red bicycle",
        )
    assert raised.value.translation_key == "unexpected_provider_failure"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_data_with_attachments(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Send image, fun GIF, and PDF attachments as Responses multimodal content."""
    with (
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            side_effect=[
                media_source.PlayMedia(
                    url="http://example.com/doorbell.jpg",
                    mime_type="image/jpeg",
                    path=Path("doorbell.jpg"),
                ),
                media_source.PlayMedia(
                    url="http://example.com/party.gif",
                    mime_type="image/gif",
                    path=Path("party.gif"),
                ),
                media_source.PlayMedia(
                    url="http://example.com/manual.pdf",
                    mime_type="application/pdf",
                    path=Path("manual.pdf"),
                ),
            ],
        ),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "pathlib.Path.stat",
            return_value=SimpleNamespace(st_size=7),
        ),
        patch("pathlib.Path.read_bytes", return_value=b"payload"),
    ):
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Describe these",
            attachments=[
                {"media_content_id": "media-source://media/doorbell.jpg"},
                {"media_content_id": "media-source://media/party.gif"},
                {"media_content_id": "media-source://media/manual.pdf"},
            ],
        )

    user_message = next(
        message
        for message in mock_stream.call_args.kwargs["input"]
        if message.get("role") == "user" and isinstance(message["content"], list)
    )
    assert user_message["content"] == [
        {"type": "input_text", "text": "Describe these"},
        {
            "type": "input_image",
            "image_url": "data:image/jpeg;base64,cGF5bG9hZA==",
            "detail": "auto",
        },
        {
            "type": "input_image",
            "image_url": "data:image/gif;base64,cGF5bG9hZA==",
            "detail": "auto",
        },
        {
            "type": "input_file",
            "filename": "manual.pdf",
            "file_data": "data:application/pdf;base64,cGF5bG9hZA==",
        },
    ]


@pytest.mark.usefixtures("setup_credentials")
async def test_attachment_mime_type_is_guessed(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    mock_stream: AsyncMock,
) -> None:
    """Guess the media type when the attachment does not declare one."""
    with (
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            return_value=media_source.PlayMedia(
                url="http://example.com/doorbell.jpg",
                mime_type=None,
                path=Path("doorbell.jpg"),
            ),
        ),
        patch("pathlib.Path.exists", return_value=True),
        patch(
            "pathlib.Path.stat",
            return_value=SimpleNamespace(st_size=7),
        ),
        patch("pathlib.Path.read_bytes", return_value=b"payload"),
        patch(
            "homeassistant.components.spacexai.files.guess_file_type",
            return_value=("image/jpeg", None),
        ),
    ):
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Describe this",
            attachments=[{"media_content_id": "media-source://media/doorbell.jpg"}],
        )

    user_message = next(
        message
        for message in mock_stream.call_args.kwargs["input"]
        if message.get("role") == "user" and isinstance(message["content"], list)
    )
    assert user_message["content"][1]["type"] == "input_image"


@pytest.mark.parametrize(
    ("exists", "mime_type", "size", "translation_key"),
    [
        pytest.param(False, "image/jpeg", 7, "attachment_not_found", id="missing"),
        pytest.param(True, "text/csv", 7, "attachment_unsupported_type", id="unsupported"),
        pytest.param(
            True,
            "image/jpeg",
            MAX_ATTACHMENT_BYTES + 1,
            "attachment_too_large",
            id="too-large",
        ),
    ],
)
@pytest.mark.usefixtures("setup_credentials")
async def test_attachment_rejections(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    exists: bool,
    mime_type: str,
    size: int,
    translation_key: str,
) -> None:
    """Reject attachments Home Assistant cannot forward to SpaceXAI."""
    with (
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            return_value=media_source.PlayMedia(
                url="http://example.com/report.csv",
                mime_type=mime_type,
                path=Path("report.csv"),
            ),
        ),
        patch("pathlib.Path.exists", return_value=exists),
        patch(
            "pathlib.Path.stat",
            return_value=SimpleNamespace(st_size=size),
        ),
        patch("pathlib.Path.read_bytes", return_value=b"payload"),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Describe this",
            attachments=[{"media_content_id": "media-source://media/report.csv"}],
        )
    assert raised.value.translation_key == translation_key


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_image_translated_error_is_not_replaced(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Surface an already-translated error from the image path unchanged."""
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_generate_image",
            new_callable=AsyncMock,
            side_effect=HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="attachment_not_found",
                translation_placeholders={"path": "missing.jpg"},
            ),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await ai_task.async_generate_image(
            hass,
            task_name="Test Image",
            entity_id=ENTITY_ID,
            instructions="A red bicycle",
        )
    assert raised.value.translation_key == "attachment_not_found"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_image_rejects_unlisted_model_when_catalog_present(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """When Imagine models are catalogued, only those ids stay selectable."""
    snapshot = setup_integration.runtime_data.snapshot
    setup_integration.runtime_data.snapshot = ProviderSnapshot(
        account=snapshot.account,
        models=snapshot.models,
        image_models=(ModelInfo(id="grok-imagine-image", owner="xai"),),
    )

    with pytest.raises(HomeAssistantError) as raised:
        await ai_task.async_generate_image(
            hass,
            task_name="Catalog Image",
            entity_id=ENTITY_ID,
            instructions="A red bicycle",
        )
    assert raised.value.translation_key == "model_not_entitled"
