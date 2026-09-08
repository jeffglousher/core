"""Tests for SpaceXAI actions."""

from asyncio import CancelledError
from datetime import UTC, datetime
from io import BufferedWriter
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, mock_open, patch

import pytest
from spacexai_subscription_client import (
    AuthenticationError,
    GeneratedVideo,
    InvalidResponseError,
    PermissionDeniedError,
    SpaceXAISubscriptionError,
)
from spacexai_subscription_client.const import TOKEN_URL

from homeassistant.components.media_source import PlayMedia
from homeassistant.components.spacexai.const import DOMAIN
from homeassistant.components.spacexai.media import (
    async_persist_video,
    async_provider_image_url,
    async_publish_media,
)
from homeassistant.core import Context, HomeAssistant, ServiceCall
from homeassistant.exceptions import (
    HomeAssistantError,
    ServiceValidationError,
    Unauthorized,
)
from homeassistant.helpers.network import NoURLAvailableError

from . import setup_integration

from tests.common import MockConfigEntry, MockUser
from tests.test_util.aiohttp import AiohttpClientMocker

VIDEO = GeneratedVideo(
    url="https://vidgen.x.ai/video.mp4",
    model="grok-imagine-video-1.5",
    duration=8,
    respect_moderation=True,
)


@pytest.fixture(autouse=True)
def local_media_dir(hass: HomeAssistant, tmp_path: Path) -> None:
    """Use an isolated local media directory."""
    hass.config.media_dirs = {"local": str(tmp_path)}


async def test_generate_video_with_token_refresh_timeout(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Do not generate media or discard credentials when token refresh times out."""
    await setup_integration(hass, mock_config_entry)
    expired_token = {**mock_config_entry.data["token"], "expires_at": 0}
    hass.config_entries.async_update_entry(
        mock_config_entry, data={**mock_config_entry.data, "token": expired_token}
    )
    aioclient_mock.post(TOKEN_URL, exc=TimeoutError)

    with pytest.raises(HomeAssistantError) as err:
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "A calm lake at sunrise",
            },
            blocking=True,
            return_response=True,
        )

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "api_error"
    assert mock_config_entry.data["token"] == expired_token
    mock_spacexai_subscription_client.async_generate_video.assert_not_awaited()
    assert list(Path(hass.config.media_dirs["local"]).iterdir()) == []
    await hass.async_block_till_done()
    assert hass.config_entries.flow.async_progress() == []


async def test_generate_video_persists_authenticated_media(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Persist a completed video and return authenticated local media details."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.return_value = VIDEO
    aioclient_mock.get(
        VIDEO.url,
        content=b"\x00\x00\x00\x18ftypmp42video",
        headers={"Content-Length": "17", "Content-Type": "video/mp4"},
    )

    with (
        patch(
            "homeassistant.components.spacexai.media.dt_util.utcnow",
            return_value=datetime(2026, 8, 30, 12, 0, tzinfo=UTC),
        ),
        patch(
            "homeassistant.components.spacexai.media.secrets",
            token_hex=MagicMock(return_value="abcd1234"),
        ),
        patch(
            "homeassistant.components.spacexai.media.get_url",
            return_value="https://ha.example",
        ),
    ):
        response = await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "A calm lake at sunrise",
                "duration": 8,
                "aspect_ratio": "16:9",
                "resolution": "720p",
            },
            blocking=True,
            return_response=True,
        )

    filename = "2026-08-30_120000_spacexai_abcd1234.mp4"
    assert response is not None
    assert response["media_source_id"] == (
        f"media-source://media_source/local/spacexai/{filename}"
    )
    assert response["content_type"] == "video/mp4"
    assert response["duration"] == 8
    assert response["model"] == "grok-imagine-video-1.5"
    assert response["path"].startswith(f"/media/local/spacexai/{filename}?authSig=")
    assert response["url"].startswith(
        f"https://ha.example/media/local/spacexai/{filename}?authSig="
    )
    assert Path(hass.config.media_dirs["local"], "spacexai", filename).read_bytes() == (
        b"\x00\x00\x00\x18ftypmp42video"
    )
    mock_spacexai_subscription_client.async_generate_video.assert_awaited_once_with(
        "access-token",
        model="grok-imagine-video-1.5",
        prompt="A calm lake at sunrise",
        image_url=None,
        duration=8,
        aspect_ratio="16:9",
        resolution="720p",
    )


async def test_generate_video_encodes_local_image(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Encode a selected local image for image-to-video generation."""
    await setup_integration(hass, mock_config_entry)
    source = Path(hass.config.media_dirs["local"], "still.jpg")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"image")
    mock_spacexai_subscription_client.async_generate_video.return_value = VIDEO

    with patch(
        "homeassistant.components.spacexai.services.async_persist_video",
        new=AsyncMock(return_value={"media_source_id": "saved", "url": "signed"}),
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "Animate this image",
                "image": {
                    "media_content_id": "media-source://media_source/local/still.jpg",
                    "media_content_type": "image/jpeg",
                },
            },
            blocking=True,
            return_response=True,
        )

    image_url = (
        mock_spacexai_subscription_client.async_generate_video.await_args.kwargs[
            "image_url"
        ]
    )
    assert image_url == "data:image/jpeg;base64,aW1hZ2U="


@pytest.mark.parametrize(
    ("open_error", "read_error"),
    [
        pytest.param(PermissionError(), None, id="permission_denied"),
        pytest.param(FileNotFoundError(), None, id="removed_before_open"),
        pytest.param(None, OSError(), id="read_failed"),
    ],
)
async def test_generate_video_rejects_unreadable_image(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    open_error: OSError | None,
    read_error: OSError | None,
) -> None:
    """Translate source-file failures before sending a generation request."""
    await setup_integration(hass, mock_config_entry)
    source = Path(hass.config.media_dirs["local"], "still.jpg")
    source.write_bytes(b"image")
    source_open = mock_open(read_data=b"image")
    source_open.side_effect = open_error
    source_open.return_value.read.side_effect = read_error

    with (
        patch("pathlib.Path.open", source_open),
        pytest.raises(ServiceValidationError) as raised,
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "Animate this image",
                "image": {
                    "media_content_id": "media-source://media_source/local/still.jpg",
                    "media_content_type": "image/jpeg",
                },
            },
            blocking=True,
            return_response=True,
        )

    assert raised.value.translation_domain == DOMAIN
    assert raised.value.translation_key == "attachment_unavailable"
    assert raised.value.translation_placeholders == {"filename": "still.jpg"}
    mock_spacexai_subscription_client.async_generate_video.assert_not_awaited()


@pytest.mark.parametrize(
    ("error", "translation_key", "reauth_flow_count"),
    [
        pytest.param(AuthenticationError(), "invalid_auth", 1, id="authentication"),
        pytest.param(InvalidResponseError(), "invalid_response", 0, id="response"),
        pytest.param(
            PermissionDeniedError(), "not_entitled", 0, id="permission_denied"
        ),
        pytest.param(SpaceXAISubscriptionError(), "api_error", 0, id="api"),
    ],
)
async def test_generate_video_translates_client_errors(
    error: SpaceXAISubscriptionError,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    reauth_flow_count: int,
    translation_key: str,
) -> None:
    """Translate stable client failures for action callers."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.side_effect = error

    with pytest.raises(HomeAssistantError) as raised:
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "A calm lake",
            },
            blocking=True,
            return_response=True,
        )

    assert raised.value.translation_key == translation_key
    assert len(hass.config_entries.flow.async_progress()) == reauth_flow_count


async def test_generate_video_rejects_moderated_result(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Do not persist a video that did not pass provider moderation."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.return_value = (
        GeneratedVideo(
            url=VIDEO.url,
            model=VIDEO.model,
            duration=VIDEO.duration,
            respect_moderation=False,
        )
    )

    with (
        patch(
            "homeassistant.components.spacexai.services.async_persist_video",
            new=AsyncMock(),
        ) as persist,
        pytest.raises(HomeAssistantError) as raised,
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "A calm lake",
            },
            blocking=True,
            return_response=True,
        )

    assert raised.value.translation_key == "video_moderated"
    persist.assert_not_awaited()


@pytest.mark.usefixtures("mock_spacexai_subscription_client")
async def test_publish_local_media(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Return a time-limited URL without copying local media."""
    await setup_integration(hass, mock_config_entry)
    source = Path(hass.config.media_dirs["local"], "porch.jpg")
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"image")
    media_source_id = "media-source://media_source/local/porch.jpg"

    with patch(
        "homeassistant.components.spacexai.media.get_url",
        return_value="https://ha.example",
    ):
        response = await hass.services.async_call(
            DOMAIN,
            "publish_media",
            {
                "media": {
                    "media_content_id": media_source_id,
                    "media_content_type": "image/jpeg",
                }
            },
            blocking=True,
            return_response=True,
        )

    assert response is not None
    assert response["media_source_id"] == media_source_id
    assert response["content_type"] == "image/jpeg"
    assert response["path"].startswith("/media/local/porch.jpg?authSig=")
    assert response["url"].startswith(
        "https://ha.example/media/local/porch.jpg?authSig="
    )


async def test_publish_media_rejects_non_admin(
    hass: HomeAssistant,
    hass_read_only_user: MockUser,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Require an administrator before issuing a signed media URL."""
    await setup_integration(hass, mock_config_entry)

    registered = hass.services.async_services_for_domain(DOMAIN)["publish_media"]
    call = ServiceCall(
        hass,
        DOMAIN,
        "publish_media",
        {
            "media": {
                "media_content_id": "media-source://media_source/local/porch.jpg",
                "media_content_type": "image/jpeg",
            }
        },
        context=Context(user_id=hass_read_only_user.id),
        return_response=True,
    )
    with patch("homeassistant.components.spacexai.media.async_sign_path") as sign_path:
        # Unauthorized belongs to HA's admin guard, outside integration translations.
        task = hass.async_run_hass_job(registered.job, call)
        assert task is not None
        with pytest.raises(Unauthorized) as raised:
            await task

    assert raised.value.user_id == hass_read_only_user.id
    sign_path.assert_not_called()
    mock_spacexai_subscription_client.async_generate_video.assert_not_awaited()


async def test_persist_video_rejects_unsafe_or_invalid_download(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Reject provider redirects and remove an incomplete local file."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.return_value = VIDEO
    aioclient_mock.get(VIDEO.url, status=302, headers={"Location": "http://127.0.0.1"})

    with (
        patch(
            "homeassistant.components.spacexai.media.secrets",
            token_hex=MagicMock(return_value="failed"),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "A calm lake",
            },
            blocking=True,
            return_response=True,
        )

    assert raised.value.translation_key == "video_download_failed"
    assert not list(Path(hass.config.media_dirs["local"]).rglob("*.part"))


@pytest.mark.parametrize(
    ("close_error", "unlink_error"),
    [
        pytest.param(OSError(), None, id="close_failed"),
        pytest.param(None, OSError(), id="unlink_failed"),
        pytest.param(OSError(), OSError(), id="both_failed"),
    ],
)
async def test_generate_video_preserves_error_when_cleanup_fails(
    aioclient_mock: AiohttpClientMocker,
    close_error: OSError | None,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    unlink_error: OSError | None,
) -> None:
    """Attempt both cleanup operations without hiding the download failure."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.return_value = VIDEO
    aioclient_mock.get(VIDEO.url, content=b"not an mp4 file")
    output = MagicMock(spec=BufferedWriter)
    output.close.side_effect = close_error

    with (
        patch("pathlib.Path.open", return_value=output),
        patch("pathlib.Path.unlink", side_effect=unlink_error) as unlink,
        pytest.raises(HomeAssistantError) as raised,
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {"config_entry": mock_config_entry.entry_id, "prompt": "A calm lake"},
            blocking=True,
            return_response=True,
        )

    assert raised.value.translation_domain == DOMAIN
    assert raised.value.translation_key == "unsupported_video"
    output.close.assert_called_once_with()
    unlink.assert_called_once_with(missing_ok=True)


async def test_generate_video_preserves_cancellation_when_cleanup_fails(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Keep cancellation intact when the incomplete-file cleanup fails."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.return_value = VIDEO
    aioclient_mock.get(VIDEO.url, content=b"\x00\x00\x00\x18ftypmp42video")
    output = MagicMock(spec=BufferedWriter)
    output.write.side_effect = CancelledError()
    output.close.side_effect = OSError()

    with (
        patch("pathlib.Path.open", return_value=output),
        patch("pathlib.Path.unlink", side_effect=OSError) as unlink,
        pytest.raises(CancelledError),
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {"config_entry": mock_config_entry.entry_id, "prompt": "A calm lake"},
            blocking=True,
            return_response=True,
        )

    output.close.assert_called_once_with()
    unlink.assert_called_once_with(missing_ok=True)


async def test_generate_video_preserves_existing_partial_file(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Do not clean up a partial file owned by a different download."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.return_value = VIDEO
    aioclient_mock.get(VIDEO.url, content=b"\x00\x00\x00\x18ftypmp42video")
    filename = "2026-08-30_120000_spacexai_collision.mp4"
    destination = Path(hass.config.media_dirs["local"], DOMAIN, filename)
    partial = destination.with_suffix(".mp4.part")
    partial.parent.mkdir(parents=True, exist_ok=True)
    partial.write_bytes(b"another download")

    with (
        patch(
            "homeassistant.components.spacexai.media.dt_util.utcnow",
            return_value=datetime(2026, 8, 30, 12, 0, tzinfo=UTC),
        ),
        patch(
            "homeassistant.components.spacexai.media.secrets",
            token_hex=MagicMock(return_value="collision"),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {"config_entry": mock_config_entry.entry_id, "prompt": "A calm lake"},
            blocking=True,
            return_response=True,
        )

    assert raised.value.translation_domain == DOMAIN
    assert raised.value.translation_key == "video_download_failed"
    assert partial.read_bytes() == b"another download"
    assert not destination.exists()


async def test_generate_video_rejects_oversized_download(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Bound the generated video persisted by Home Assistant."""
    await setup_integration(hass, mock_config_entry)
    mock_spacexai_subscription_client.async_generate_video.return_value = VIDEO
    aioclient_mock.get(VIDEO.url, content=b"\x00\x00\x00\x18ftypmp42video")

    with (
        patch("homeassistant.components.spacexai.media.MAX_VIDEO_SIZE", 8),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": mock_config_entry.entry_id,
                "prompt": "A calm lake",
            },
            blocking=True,
            return_response=True,
        )

    assert raised.value.translation_key == "media_too_large"


@pytest.mark.parametrize(
    "url",
    [
        pytest.param(
            "https://example.com/video.mp4",
            id="untrusted_host",
        ),
        pytest.param(
            "http://vidgen.x.ai/video.mp4",
            id="insecure_scheme",
        ),
    ],
)
async def test_persist_video_rejects_untrusted_url(
    hass: HomeAssistant, url: str
) -> None:
    """Do not let a provider response turn the media download into SSRF."""
    with pytest.raises(HomeAssistantError) as raised:
        await async_persist_video(hass, url)

    assert raised.value.translation_key == "video_download_failed"


async def test_persist_video_rejects_non_mp4(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
) -> None:
    """Reject a completed download that is not an MP4 file."""
    aioclient_mock.get(VIDEO.url, content=b"not an mp4 file")

    with pytest.raises(HomeAssistantError) as raised:
        await async_persist_video(hass, VIDEO.url)

    assert raised.value.translation_key == "unsupported_video"
    assert not list(Path(hass.config.media_dirs["local"]).rglob("*.part"))


async def test_persist_video_requires_media_directory(hass: HomeAssistant) -> None:
    """Explain when local media storage is unavailable."""
    hass.config.media_dirs = {}

    with pytest.raises(HomeAssistantError) as raised:
        await async_persist_video(hass, VIDEO.url)

    assert raised.value.translation_key == "no_media_directory"


async def test_persist_video_rejects_oversized_content_length(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
) -> None:
    """Reject an oversized declared response before opening a local file."""
    aioclient_mock.get(
        VIDEO.url,
        content=b"\x00\x00\x00\x18ftypmp42video",
        headers={"Content-Length": "17"},
    )

    with (
        patch("homeassistant.components.spacexai.media.MAX_VIDEO_SIZE", 16),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await async_persist_video(hass, VIDEO.url)

    assert raised.value.translation_key == "media_too_large"


async def test_provider_image_rejects_unresolvable_media(hass: HomeAssistant) -> None:
    """Translate an image media-source resolution failure."""
    with pytest.raises(ServiceValidationError) as raised:
        await async_provider_image_url(
            hass,
            {"media_content_id": "media-source://media_source/local/missing.jpg"},
        )

    assert raised.value.translation_key == "invalid_media_reference"


async def test_provider_image_rejects_remote_media(hass: HomeAssistant) -> None:
    """Reject image media that is not backed by a local file."""
    with (
        patch(
            "homeassistant.components.spacexai.media.media_source.async_resolve_media",
            return_value=PlayMedia("https://example.com/image.jpg", "image/jpeg"),
        ),
        pytest.raises(ServiceValidationError) as raised,
    ):
        await async_provider_image_url(
            hass,
            {"media_content_id": "media-source://example/image.jpg"},
        )

    assert raised.value.translation_key == "media_not_local"


@pytest.mark.parametrize(
    ("content", "media_type", "translation_key"),
    [
        pytest.param(b"", "image/jpeg", "attachment_empty", id="empty"),
        pytest.param(b"image", "image/gif", "unsupported_media", id="type"),
        pytest.param(b"too-large", "image/jpeg", "media_too_large", id="size"),
    ],
)
async def test_provider_image_validates_local_file(
    content: bytes,
    hass: HomeAssistant,
    media_type: str,
    tmp_path: Path,
    translation_key: str,
) -> None:
    """Validate local image content before encoding it."""
    source = tmp_path / "source.jpg"
    source.write_bytes(content)

    with (
        patch(
            "homeassistant.components.spacexai.media.media_source.async_resolve_media",
            return_value=PlayMedia("/media/local/source.jpg", media_type, path=source),
        ),
        patch("homeassistant.components.spacexai.media.MAX_ATTACHMENT_SIZE", 5),
        pytest.raises(ServiceValidationError) as raised,
    ):
        await async_provider_image_url(
            hass,
            {"media_content_id": "media-source://media_source/local/source.jpg"},
        )

    assert raised.value.translation_key == translation_key


async def test_publish_media_falls_back_to_relative_url(
    hass: HomeAssistant,
    tmp_path: Path,
) -> None:
    """Return the signed path when Home Assistant has no configured base URL."""
    source = tmp_path / "image.jpg"
    source.write_bytes(b"image")
    with (
        patch(
            "homeassistant.components.spacexai.media.media_source.async_resolve_media",
            return_value=PlayMedia("/media/local/image.jpg", "image/jpeg", path=source),
        ),
        patch(
            "homeassistant.components.spacexai.media.get_url",
            side_effect=NoURLAvailableError,
        ),
        patch(
            "homeassistant.components.spacexai.media.async_sign_path",
            return_value="/media/local/image.jpg?authSig=signed",
        ),
    ):
        response = await async_publish_media(hass, "media-source://local/image.jpg")

    assert response["url"] == response["path"]
