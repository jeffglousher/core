"""Safe local media handling for SpaceXAI actions."""

import base64
from collections.abc import Mapping
from datetime import timedelta
from pathlib import Path
import secrets
from typing import BinaryIO

from aiohttp import ClientError, ClientTimeout
from yarl import URL

from homeassistant.components import media_source
from homeassistant.components.http.auth import async_sign_path
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.network import NoURLAvailableError, get_url
from homeassistant.util import dt as dt_util
from homeassistant.util.json import JsonObjectType

from .const import DOMAIN, MAX_ATTACHMENT_SIZE, MAX_VIDEO_SIZE

_DOWNLOAD_CHUNK_SIZE = 1024 * 1024
_DOWNLOAD_TIMEOUT = ClientTimeout(total=180)
_IMAGE_MEDIA_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
_MEDIA_URL_EXPIRY = timedelta(hours=1)


async def async_provider_image_url(
    hass: HomeAssistant, selected_media: Mapping[str, str]
) -> str:
    """Resolve a local image and return a bounded data URL."""
    media_source_id = selected_media["media_content_id"]
    try:
        media = await media_source.async_resolve_media(hass, media_source_id, None)
    except (HomeAssistantError, media_source.Unresolvable) as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_media_reference",
        ) from err
    media_type = selected_media.get("media_content_type") or media.mime_type
    if media.path is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="media_not_local",
        )
    return await hass.async_add_executor_job(_image_data_url, media.path, media_type)


async def async_persist_video(hass: HomeAssistant, url: str) -> JsonObjectType:
    """Persist a provider video in Home Assistant's authenticated media source."""
    parsed = URL(url)
    if (
        parsed.scheme != "https"
        or parsed.host is None
        or not (parsed.host == "x.ai" or parsed.host.endswith(".x.ai"))
    ):
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="video_download_failed",
        )
    if not hass.config.media_dirs:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="no_media_directory",
        )

    source_id, source_dir = next(iter(hass.config.media_dirs.items()))
    filename = (
        f"{dt_util.utcnow().strftime('%Y-%m-%d_%H%M%S')}_"
        f"spacexai_{secrets.token_hex(4)}.mp4"
    )
    destination = Path(source_dir, DOMAIN, filename)
    partial = destination.with_suffix(".mp4.part")
    output: BinaryIO | None = None
    complete = False
    prefix = bytearray()
    total = 0
    try:
        session = async_get_clientsession(hass)
        async with session.get(
            url,
            allow_redirects=False,
            timeout=_DOWNLOAD_TIMEOUT,
        ) as response:
            if response.status != 200:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="video_download_failed",
                )
            content_length = response.headers.get("Content-Length")
            if content_length is not None and int(content_length) > MAX_VIDEO_SIZE:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="media_too_large",
                    translation_placeholders={"max_mb": str(MAX_VIDEO_SIZE // 1048576)},
                )
            output = await hass.async_add_executor_job(_open_output, partial)
            async for chunk in response.content.iter_chunked(_DOWNLOAD_CHUNK_SIZE):
                total += len(chunk)
                if total > MAX_VIDEO_SIZE:
                    raise HomeAssistantError(
                        translation_domain=DOMAIN,
                        translation_key="media_too_large",
                        translation_placeholders={
                            "max_mb": str(MAX_VIDEO_SIZE // 1048576)
                        },
                    )
                if len(prefix) < 12:
                    prefix.extend(chunk[: 12 - len(prefix)])
                await hass.async_add_executor_job(output.write, chunk)
        if total == 0 or len(prefix) < 12 or prefix[4:8] != b"ftyp":
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="unsupported_video",
            )
        await hass.async_add_executor_job(output.close)
        output = None
        await hass.async_add_executor_job(_finish_output, partial, destination)
        complete = True
    except (ClientError, TimeoutError, OSError, ValueError) as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="video_download_failed",
        ) from err
    finally:
        if output is not None:
            await hass.async_add_executor_job(output.close)
        if not complete:
            await hass.async_add_executor_job(_remove_output, partial)

    media_source_id = f"media-source://media_source/{source_id}/{DOMAIN}/{filename}"
    return await async_publish_media(hass, media_source_id)


async def async_publish_media(
    hass: HomeAssistant, media_source_id: str
) -> JsonObjectType:
    """Return a time-limited URL for local Home Assistant media."""
    try:
        media = await media_source.async_resolve_media(hass, media_source_id, None)
    except (HomeAssistantError, media_source.Unresolvable) as err:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_media_reference",
        ) from err
    if media.path is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="media_not_local",
        )
    signed_path = async_sign_path(hass, media.url, _MEDIA_URL_EXPIRY)
    try:
        base_url = get_url(hass, prefer_external=True, prefer_cloud=True)
    except NoURLAvailableError:
        url = signed_path
    else:
        url = f"{base_url.rstrip('/')}{signed_path}"
    return {
        "media_source_id": media_source_id,
        "content_type": media.mime_type,
        "path": signed_path,
        "url": url,
    }


def _image_data_url(path: Path, media_type: str) -> str:
    """Read and encode a supported local image."""
    if media_type not in _IMAGE_MEDIA_TYPES or not path.is_file():
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unsupported_media",
        )
    with path.open("rb") as image_file:
        data = image_file.read(MAX_ATTACHMENT_SIZE + 1)
    if not data:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="attachment_empty",
            translation_placeholders={"filename": path.name},
        )
    if len(data) > MAX_ATTACHMENT_SIZE:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="media_too_large",
            translation_placeholders={"max_mb": str(MAX_ATTACHMENT_SIZE // 1048576)},
        )
    return f"data:{media_type};base64,{base64.b64encode(data).decode()}"


def _open_output(path: Path) -> BinaryIO:
    """Open a new partial media file without replacing existing data."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("xb")


def _finish_output(partial: Path, destination: Path) -> None:
    """Atomically expose a completed media file."""
    partial.replace(destination)


def _remove_output(path: Path) -> None:
    """Remove an incomplete output file."""
    path.unlink(missing_ok=True)
