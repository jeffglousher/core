"""Tests for the SpaceXAI AI Task platform."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from spacexai_subscription_client import (
    Attachment,
    AuthenticationError,
    Completion,
    GeneratedImage,
    Message,
    ResponseFormat,
)
import voluptuous as vol

from homeassistant.components import ai_task, media_source
from homeassistant.components.spacexai.const import RECOMMENDED_IMAGE_MODEL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, selector

from . import setup_integration
from .conftest import ACCESS_TOKEN

from tests.common import MockConfigEntry

ENTITY_ID = "ai_task.grok_ai_task"


async def test_generate_data(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Generate unstructured data from the AI Task entity."""
    mock_spacexai_subscription_client.async_create_response.return_value = Completion(
        "The answer", ()
    )
    await setup_integration(hass, mock_config_entry_with_ai_task)

    entity_entry = entity_registry.async_get(ENTITY_ID)
    assert entity_entry is not None
    assert entity_entry.config_subentry_id == "ai-task-subentry"

    result = await ai_task.async_generate_data(
        hass,
        task_name="Test Task",
        entity_id=ENTITY_ID,
        instructions="Answer the question",
    )

    assert result.data == "The answer"
    mock_spacexai_subscription_client.async_create_response.assert_awaited_once()
    call = mock_spacexai_subscription_client.async_create_response.call_args
    assert call.args == (ACCESS_TOKEN,)
    assert call.kwargs["model"] == "grok-4.6"
    assert call.kwargs["tools"] == []
    assert call.kwargs["response_format"] is None
    assert call.kwargs["input_data"][-1] == Message("user", "Answer the question")


async def test_generate_structured_data(
    hass: HomeAssistant,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Request and parse strict structured output."""
    mock_spacexai_subscription_client.async_create_response.return_value = Completion(
        '{"summary":"Clear","score":null}', ()
    )
    await setup_integration(hass, mock_config_entry_with_ai_task)

    result = await ai_task.async_generate_data(
        hass,
        task_name="Review Result",
        entity_id=ENTITY_ID,
        instructions="Review this result",
        structure=vol.Schema(
            {
                vol.Required("summary"): selector.TextSelector(),
                vol.Optional("score"): selector.NumberSelector(),
            }
        ),
    )

    assert result.data == {"summary": "Clear", "score": None}
    response_format = (
        mock_spacexai_subscription_client.async_create_response.call_args.kwargs[
            "response_format"
        ]
    )
    assert isinstance(response_format, ResponseFormat)
    assert response_format.name == "review_result"
    assert response_format.schema["additionalProperties"] is False
    assert response_format.schema["required"] == ["summary", "score"]
    assert response_format.schema["properties"]["score"]["type"] == [
        "number",
        "null",
    ]


async def test_generate_data_invalid_json(
    hass: HomeAssistant,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Translate malformed structured output."""
    mock_spacexai_subscription_client.async_create_response.return_value = Completion(
        "invalid", ()
    )
    await setup_integration(hass, mock_config_entry_with_ai_task)

    with pytest.raises(HomeAssistantError):
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Return data",
            structure=vol.Schema({vol.Required("result"): str}),
        )


@pytest.mark.freeze_time("2026-08-29 12:00:00")
async def test_generate_image(
    hass: HomeAssistant,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Generate an image and publish it through the AI Task integration."""
    mock_spacexai_subscription_client.async_generate_image.return_value = (
        GeneratedImage(
            b"image-data",
            "image/png",
            RECOMMENDED_IMAGE_MODEL,
            "A refined prompt",
        )
    )
    await setup_integration(hass, mock_config_entry_with_ai_task)

    with patch.object(
        media_source.local_source.LocalSource,
        "async_upload_media",
        return_value="media-source://ai_task/image/result.png",
    ) as mock_upload:
        result = await ai_task.async_generate_image(
            hass,
            task_name="Test Image",
            entity_id=ENTITY_ID,
            instructions="Draw a smart home",
        )

    assert result is not None
    assert result["mime_type"] == "image/png"
    assert result["model"] == RECOMMENDED_IMAGE_MODEL
    assert result["revised_prompt"] == "A refined prompt"
    image_file = mock_upload.call_args.args[1]
    assert image_file.file.getvalue() == b"image-data"
    mock_spacexai_subscription_client.async_generate_image.assert_awaited_once_with(
        ACCESS_TOKEN,
        model=RECOMMENDED_IMAGE_MODEL,
        prompt="Draw a smart home",
    )


async def test_edit_image_with_maximum_references(
    hass: HomeAssistant,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Edit an image with the provider's maximum reference count."""
    mock_spacexai_subscription_client.async_edit_image.return_value = GeneratedImage(
        b"edited-image", "image/jpeg", RECOMMENDED_IMAGE_MODEL
    )
    await setup_integration(hass, mock_config_entry_with_ai_task)

    with (
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            return_value=media_source.PlayMedia(
                url="http://example.com/source.png",
                mime_type="image/png",
                path=Path("source.png"),
            ),
        ),
        patch("pathlib.Path.stat") as mock_stat,
        patch("pathlib.Path.read_bytes", return_value=b"source-image"),
        patch.object(
            media_source.local_source.LocalSource,
            "async_upload_media",
            return_value="media-source://ai_task/image/result.jpg",
        ),
    ):
        mock_stat.return_value.st_size = len(b"source-image")
        result = await ai_task.async_generate_image(
            hass,
            task_name="Edit Image",
            entity_id=ENTITY_ID,
            instructions="Add a lamp",
            attachments=[
                {"media_content_id": f"media-source://media/source-{index}.png"}
                for index in range(5)
            ],
        )

    assert result is not None
    assert result["mime_type"] == "image/jpeg"
    mock_spacexai_subscription_client.async_edit_image.assert_awaited_once_with(
        ACCESS_TOKEN,
        model=RECOMMENDED_IMAGE_MODEL,
        prompt="Add a lamp",
        images=(Attachment("source.png", "image/png", b"source-image"),) * 5,
    )
    mock_spacexai_subscription_client.async_generate_image.assert_not_awaited()


async def test_generate_data_authentication_error(
    hass: HomeAssistant,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Translate authentication rejection from data generation."""
    mock_spacexai_subscription_client.async_create_response.side_effect = (
        AuthenticationError
    )
    await setup_integration(hass, mock_config_entry_with_ai_task)

    with pytest.raises(HomeAssistantError):
        await ai_task.async_generate_data(
            hass,
            task_name="Test Task",
            entity_id=ENTITY_ID,
            instructions="Return data",
        )

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"
    assert flows[0]["step_id"] == "reauth_confirm"


async def test_generate_image_authentication_error(
    hass: HomeAssistant,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Start reauthentication when image generation rejects the token."""
    mock_spacexai_subscription_client.async_generate_image.side_effect = (
        AuthenticationError
    )
    await setup_integration(hass, mock_config_entry_with_ai_task)

    with pytest.raises(HomeAssistantError) as err:
        await ai_task.async_generate_image(
            hass,
            task_name="Test Image",
            entity_id=ENTITY_ID,
            instructions="Draw a smart home",
        )

    assert err.value.translation_key == "invalid_auth"
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"
    assert flows[0]["step_id"] == "reauth_confirm"


@pytest.mark.parametrize(
    ("media_type", "attachment_count"),
    [
        pytest.param("application/pdf", 1, id="unsupported_type"),
        pytest.param("image/png", 6, id="too_many"),
    ],
)
async def test_reject_invalid_image_attachments(
    hass: HomeAssistant,
    mock_config_entry_with_ai_task: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    media_type: str,
    attachment_count: int,
) -> None:
    """Reject unsupported image-edit attachments before calling SpaceXAI."""
    await setup_integration(hass, mock_config_entry_with_ai_task)
    resolved = media_source.PlayMedia(
        url="http://example.com/source",
        mime_type=media_type,
        path=Path("source"),
    )
    attachments = [
        {"media_content_id": f"media-source://media/source-{index}"}
        for index in range(attachment_count)
    ]

    with (
        patch(
            "homeassistant.components.media_source.async_resolve_media",
            return_value=resolved,
        ),
        patch(
            "pathlib.Path.stat",
            return_value=MagicMock(st_size=len(b"source")),
        ),
        patch("pathlib.Path.read_bytes", return_value=b"source"),
        pytest.raises(HomeAssistantError),
    ):
        await ai_task.async_generate_image(
            hass,
            task_name="Edit Image",
            entity_id=ENTITY_ID,
            instructions="Edit this image",
            attachments=attachments,
        )

    mock_spacexai_subscription_client.async_edit_image.assert_not_awaited()
    mock_spacexai_subscription_client.async_generate_image.assert_not_awaited()
