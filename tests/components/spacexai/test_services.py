"""Tests for SpaceXAI admin services."""

from contextlib import AbstractContextManager
from datetime import UTC, datetime
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
from tests.test_util.aiohttp import AiohttpClientMocker

PERSISTED_VIDEO = {
    "filename": "2026-08-14_180000_imagine_video.mp4",
    "path": "/local/spacexai/2026-08-14_180000_imagine_video.mp4",
    "url": "http://10.0.0.5:8123/local/spacexai/2026-08-14_180000_imagine_video.mp4",
}


def _persist_patch() -> AbstractContextManager[AsyncMock]:
    """Return a patch that skips the provider download."""
    return patch(
        "homeassistant.components.spacexai.async_persist_remote_media",
        new=AsyncMock(return_value=PERSISTED_VIDEO),
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_returns_local_copy(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Persist the completed Imagine video and return the local URL."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/video.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )

    with _persist_patch() as persist:
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
        **PERSISTED_VIDEO,
        "model": DEFAULT_VIDEO_MODEL,
        "provider_url": "https://vidgen.example/video.mp4",
    }
    persist.assert_awaited_once()
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

    with _persist_patch():
        response = await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": entry.entry_id,
                "prompt": "Animate this still",
                "image_url": "https://example.com/ball.jpg",
                "duration": 2,
                "aspect_ratio": "16:9",
                "resolution": "720p",
            },
            blocking=True,
            return_response=True,
        )

    assert response == {
        **PERSISTED_VIDEO,
        "model": DEFAULT_VIDEO_MODEL,
        "provider_url": "https://vidgen.example/from-image.mp4",
    }
    entry.runtime_data.client.async_generate_video.assert_awaited_once_with(
        model=DEFAULT_VIDEO_MODEL,
        prompt="Animate this still",
        image_url="https://example.com/ball.jpg",
        duration=2,
        aspect_ratio="16:9",
        resolution="720p",
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
                "model": "grok-imagine-video-unknown",
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

    with (
        patch(
            "homeassistant.components.spacexai.media.media_source.async_resolve_media",
            return_value=PlayMedia(
                url="/ai_task/image/still.jpg",
                mime_type="image/jpeg",
                path=source,
            ),
        ),
        _persist_patch(),
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
        **PERSISTED_VIDEO,
        "model": DEFAULT_VIDEO_MODEL,
        "provider_url": "https://vidgen.example/from-local.mp4",
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
async def test_generate_video_persists_provider_download(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Download the Imagine URL into /local before it expires."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/video.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )
    payload = b"\x00\x00\x00\x18ftypmp42video"
    aioclient_mock.get(
        "https://vidgen.example/video.mp4",
        content=payload,
        headers={"Content-Type": "video/mp4"},
    )
    Path(hass.config.path("www")).mkdir(parents=True, exist_ok=True)
    dest = (
        Path(hass.config.path("www"))
        / "spacexai"
        / "2026-08-14_180000_imagine_video.mp4"
    )
    dest.parent.mkdir(parents=True, exist_ok=True)
    for leftover in dest.parent.glob("2026-08-14_180000_imagine_video*.mp4"):
        leftover.unlink()

    with (
        patch(
            "homeassistant.components.spacexai.media.dt_util.utcnow",
            return_value=datetime(2026, 8, 14, 18, 0, 0, tzinfo=UTC),
        ),
        patch(
            "homeassistant.components.spacexai.media.get_url",
            return_value="http://10.0.0.5:8123",
        ),
    ):
        response = await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": entry.entry_id,
                "prompt": "A bouncing red ball",
            },
            blocking=True,
            return_response=True,
        )

    assert dest.read_bytes() == payload
    assert response == {
        "filename": "2026-08-14_180000_imagine_video.mp4",
        "model": DEFAULT_VIDEO_MODEL,
        "path": "/local/spacexai/2026-08-14_180000_imagine_video.mp4",
        "provider_url": "https://vidgen.example/video.mp4",
        "url": "http://10.0.0.5:8123/local/spacexai/2026-08-14_180000_imagine_video.mp4",
    }


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_persist_failure(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Raise when the provider video URL cannot be downloaded."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/video.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )
    aioclient_mock.get("https://vidgen.example/video.mp4", status=404)

    with pytest.raises(HomeAssistantError) as raised:
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
    assert raised.value.translation_key == "video_persist_failed"


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
    dest_dir = www / "spacexai"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for leftover in dest_dir.glob("porch*.jpg"):
        leftover.unlink()

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


@pytest.mark.usefixtures("setup_credentials")
async def test_publish_media_keeps_existing_file(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    tmp_path: Path,
) -> None:
    """Append a timestamp when the publish filename already exists."""
    source = tmp_path / "porch.jpg"
    source.write_bytes(b"\xff\xd8\xffjpeg")
    later = tmp_path / "later.jpg"
    later.write_bytes(b"\xff\xd8\xfflater")
    www = Path(hass.config.path("www"))
    dest_dir = www / "spacexai"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for leftover in dest_dir.glob("porch*.jpg"):
        leftover.unlink()
    (dest_dir / "porch.jpg").write_bytes(b"keep-me")

    with (
        patch(
            "homeassistant.components.spacexai.media.media_source.async_resolve_media",
            return_value=PlayMedia(
                url="/ai_task/image/later.jpg",
                mime_type="image/jpeg",
                path=later,
            ),
        ),
        patch(
            "homeassistant.components.spacexai.media.get_url",
            return_value="http://10.0.0.5:8123",
        ),
        patch(
            "homeassistant.components.spacexai.media.dt_util.utcnow",
            return_value=datetime(2026, 8, 14, 18, 0, tzinfo=UTC),
        ),
    ):
        response = await hass.services.async_call(
            DOMAIN,
            "publish_media",
            {
                "media_source_id": "media-source://ai_task/image/later.jpg",
                "filename": "porch.jpg",
            },
            blocking=True,
            return_response=True,
        )

    assert response == {
        "filename": "porch_2026-08-14_180000.jpg",
        "path": "/local/spacexai/porch_2026-08-14_180000.jpg",
        "url": "http://10.0.0.5:8123/local/spacexai/porch_2026-08-14_180000.jpg",
    }
    assert (dest_dir / "porch.jpg").read_bytes() == b"keep-me"
    assert (dest_dir / "porch_2026-08-14_180000.jpg").read_bytes() == later.read_bytes()


@pytest.mark.usefixtures("setup_credentials")
async def test_publish_media_rejects_filename_escape(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    tmp_path: Path,
) -> None:
    """Keep a requested filename under /local/spacexai."""
    source = tmp_path / "porch.jpg"
    source.write_bytes(b"\xff\xd8\xffjpeg")
    www = Path(hass.config.path("www"))
    dest_dir = www / "spacexai"
    dest_dir.mkdir(parents=True, exist_ok=True)
    (dest_dir / "escape.jpg").unlink(missing_ok=True)

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
            {
                "media_source_id": "media-source://ai_task/image/porch.jpg",
                "filename": "../escape.jpg",
            },
            blocking=True,
            return_response=True,
        )

    assert response["filename"] == "escape.jpg"
    assert response["path"] == "/local/spacexai/escape.jpg"
    assert (dest_dir / "escape.jpg").read_bytes() == source.read_bytes()
    assert not (www / "escape.jpg").exists()


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_keeps_existing_persist_file(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Append a timestamp when the default persist filename already exists."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/video.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )
    payload = b"\x00\x00\x00\x18ftypmp42later"
    aioclient_mock.get(
        "https://vidgen.example/video.mp4",
        content=payload,
        headers={"Content-Type": "video/mp4"},
    )
    dest_dir = Path(hass.config.path("www")) / "spacexai"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for leftover in dest_dir.glob("2026-08-14_180000_imagine_video*.mp4"):
        leftover.unlink()
    existing = dest_dir / "2026-08-14_180000_imagine_video.mp4"
    existing.write_bytes(b"keep-me")

    with (
        patch(
            "homeassistant.components.spacexai.media.dt_util.utcnow",
            return_value=datetime(2026, 8, 14, 18, 0, 0, tzinfo=UTC),
        ),
        patch(
            "homeassistant.components.spacexai.media.get_url",
            return_value="http://10.0.0.5:8123",
        ),
    ):
        response = await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": entry.entry_id,
                "prompt": "A bouncing red ball",
            },
            blocking=True,
            return_response=True,
        )

    assert (
        response["filename"] == "2026-08-14_180000_imagine_video_2026-08-14_180000.mp4"
    )
    assert existing.read_bytes() == b"keep-me"
    assert (
        dest_dir / "2026-08-14_180000_imagine_video_2026-08-14_180000.mp4"
    ).read_bytes() == payload


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_rejects_oversized_download(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Reject a provider video that exceeds the local persist cap."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/huge.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )
    aioclient_mock.get(
        "https://vidgen.example/huge.mp4",
        content=b"x" * 17,
        headers={"Content-Type": "video/mp4"},
    )

    with (
        patch("homeassistant.components.spacexai.media.MAX_VIDEO_BYTES", 16),
        pytest.raises(HomeAssistantError) as raised,
    ):
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
    assert raised.value.translation_key == "video_too_large"
