"""Tests for SpaceXAI admin services."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.media_source import PlayMedia
from homeassistant.components.spacexai.client import (
    GeneratedVideo,
    ModelInfo,
    ProviderSnapshot,
)
from homeassistant.components.spacexai.const import DEFAULT_VIDEO_MODEL, DOMAIN
from homeassistant.components.spacexai.errors import (
    ErrorContext,
    Operation,
    PermanentProviderError,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_returns_provider_url(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Return the completed Imagine video URL for an entitled model."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/video.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )

    response = await hass.services.async_call(
        DOMAIN,
        "generate_video",
        {
            "config_entry": entry.entry_id,
            "prompt": "A bouncing red ball",
            "duration": 3,
        },
        blocking=True,
        return_response=True,
    )

    assert response == {
        "url": "https://vidgen.example/video.mp4",
        "model": DEFAULT_VIDEO_MODEL,
    }
    entry.runtime_data.client.async_generate_video.assert_awaited_once()


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_forwards_image_url(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Pass an image URL through to Imagine for image-to-video."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/from-image.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )

    response = await hass.services.async_call(
        DOMAIN,
        "generate_video",
        {
            "config_entry": entry.entry_id,
            "prompt": "Animate this still",
            "image_url": "https://example.com/ball.jpg",
            "duration": 2,
        },
        blocking=True,
        return_response=True,
    )

    assert response == {
        "url": "https://vidgen.example/from-image.mp4",
        "model": DEFAULT_VIDEO_MODEL,
    }
    entry.runtime_data.client.async_generate_video.assert_awaited_once_with(
        model=DEFAULT_VIDEO_MODEL,
        prompt="Animate this still",
        image_url="https://example.com/ball.jpg",
        duration=2,
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_rejects_unknown_entry(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Reject calls that do not target a loaded SpaceXAI entry."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": "missing-entry",
                "prompt": "A bouncing red ball",
            },
            blocking=True,
            return_response=True,
        )


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_rejects_non_entitled_model(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Reject video models that are not in the entitled catalog."""
    entry = setup_integration
    snapshot = entry.runtime_data.snapshot
    entry.runtime_data.snapshot = ProviderSnapshot(
        account=snapshot.account,
        models=snapshot.models,
        image_models=snapshot.image_models,
        video_models=(ModelInfo(id=DEFAULT_VIDEO_MODEL, owner="xai"),),
    )

    with pytest.raises(ServiceValidationError) as raised:
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": entry.entry_id,
                "prompt": "A bouncing red ball",
                "model": "grok-imagine-video",
            },
            blocking=True,
            return_response=True,
        )
    assert raised.value.translation_key == "model_not_entitled"


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_translates_provider_errors(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Translate SpaceXAI provider failures into HomeAssistantError."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        side_effect=PermanentProviderError(
            "video failed",
            context=ErrorContext(
                operation=Operation.VIDEO,
                model=DEFAULT_VIDEO_MODEL,
                provider_code="failed",
            ),
        )
    )

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": entry.entry_id,
                "prompt": "A bouncing red ball",
            },
            blocking=True,
            return_response=True,
        )


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_encodes_local_media_source(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    tmp_path: Path,
) -> None:
    """Encode a Home Assistant media-source image for image-to-video."""
    entry = setup_integration
    source = tmp_path / "still.jpg"
    source.write_bytes(b"\xff\xd8\xffpayload")
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/from-local.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )

    with patch(
        "homeassistant.components.spacexai.media.media_source.async_resolve_media",
        return_value=PlayMedia(
            url="/ai_task/image/still.jpg",
            mime_type="image/jpeg",
            path=source,
        ),
    ):
        response = await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": entry.entry_id,
                "prompt": "Animate this still",
                "image_url": "media-source://ai_task/image/still.jpg",
                "duration": 2,
            },
            blocking=True,
            return_response=True,
        )

    assert response == {
        "url": "https://vidgen.example/from-local.mp4",
        "model": DEFAULT_VIDEO_MODEL,
    }
    image_url = entry.runtime_data.client.async_generate_video.await_args.kwargs[
        "image_url"
    ]
    assert image_url.startswith("data:image/jpeg;base64,")


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_rejects_local_path_escape(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Reject /local references that escape the www directory."""
    Path(hass.config.path("www")).mkdir(parents=True, exist_ok=True)
    Path(hass.config.path("secrets.yaml")).write_text("nope", encoding="utf-8")

    with pytest.raises(ServiceValidationError) as raised:
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": setup_integration.entry_id,
                "prompt": "Animate this still",
                "image_url": "/local/../secrets.yaml",
            },
            blocking=True,
            return_response=True,
        )
    assert raised.value.translation_key == "invalid_media_reference"


@pytest.mark.usefixtures("setup_credentials")
async def test_publish_media_copies_to_local(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    tmp_path: Path,
) -> None:
    """Copy an AI Task image into /local for Companion notifications."""
    source = tmp_path / "porch.jpg"
    source.write_bytes(b"\xff\xd8\xffjpeg")
    www = Path(hass.config.path("www"))
    www.mkdir(parents=True, exist_ok=True)

    with (
        patch(
            "homeassistant.components.spacexai.media.media_source.async_resolve_media",
            return_value=PlayMedia(
                url="/ai_task/image/porch.jpg",
                mime_type="image/jpeg",
                path=source,
            ),
        ),
        patch(
            "homeassistant.components.spacexai.media.get_url",
            return_value="http://10.0.0.5:8123",
        ),
    ):
        response = await hass.services.async_call(
            DOMAIN,
            "publish_media",
            {"media_source_id": "media-source://ai_task/image/porch.jpg"},
            blocking=True,
            return_response=True,
        )

    assert response == {
        "filename": "porch.jpg",
        "path": "/local/spacexai/porch.jpg",
        "url": "http://10.0.0.5:8123/local/spacexai/porch.jpg",
    }
    assert (www / "spacexai" / "porch.jpg").read_bytes() == source.read_bytes()
