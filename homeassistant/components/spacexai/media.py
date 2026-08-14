"""Local media helpers for SpaceXAI notify and Imagine."""

import base64
from mimetypes import guess_type
from pathlib import Path
import re
from shutil import copyfile

from homeassistant.components import media_source
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers.network import NoURLAvailableError, get_url, is_hass_url
from homeassistant.util import slugify
import yarl

from .const import DOMAIN, MAX_IMAGE_BYTES, PUBLISH_DIR

_SAFE_FILENAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp", ".gif"})


async def async_provider_image_url(hass: HomeAssistant, image_ref: str) -> str:
    """Return an image URL xAI can fetch.

    Public https and data URIs pass through. Home Assistant media-source ids,
    /local/ paths, and HA-owned http(s) URLs are encoded as data URIs.
    """
    ref = image_ref.strip()
    if not ref:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_media_reference",
            translation_placeholders={"media": image_ref},
        )
    if ref.startswith("data:"):
        return ref
    if ref.startswith("https://") and not is_hass_url(hass, ref):
        return ref
    path, mime = await async_resolve_local_image(hass, ref)
    return await hass.async_add_executor_job(_data_uri, path, mime)


async def async_publish_media(
    hass: HomeAssistant,
    media_source_id: str,
    *,
    filename: str | None = None,
) -> dict[str, str]:
    """Copy a media-source image into /local so Companion can fetch it."""
    path, mime = await async_resolve_local_image(hass, media_source_id)
    dest_name = _publish_filename(path, filename, mime)
    www = Path(hass.config.path("www"))
    dest_dir = www / PUBLISH_DIR
    dest = dest_dir / dest_name
    await hass.async_add_executor_job(_copy_publish, path, dest_dir, dest)
    local_path = f"/local/{PUBLISH_DIR}/{dest_name}"
    return {
        "filename": dest_name,
        "path": local_path,
        "url": _absolute_url(hass, local_path),
    }


async def async_resolve_local_image(
    hass: HomeAssistant, image_ref: str
) -> tuple[Path, str]:
    """Resolve a media-source id, /local/ path, or HA URL to a local image file."""
    ref = image_ref.strip()
    if ref.startswith(("http://", "https://")):
        parsed = yarl.URL(ref)
        if parsed.path.startswith("/local/"):
            ref = parsed.path
        elif ref.startswith("media-source://"):
            pass
        else:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_media_reference",
                translation_placeholders={"media": image_ref},
            )
    if ref.startswith("media-source://"):
        try:
            play = await media_source.async_resolve_media(hass, ref, None)
        except (HomeAssistantError, media_source.Unresolvable) as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_media_reference",
                translation_placeholders={"media": image_ref},
            ) from err
        if play.path is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_media_reference",
                translation_placeholders={"media": image_ref},
            )
        path = Path(play.path)
        mime = play.mime_type or guess_type(path)[0] or "image/jpeg"
        _assert_readable_image(path, mime)
        return path, mime
    if ref.startswith("/local/"):
        www = Path(hass.config.path("www"))
        path = _safe_under(www, www / ref.removeprefix("/local/"))
        mime = guess_type(path)[0] or "image/jpeg"
        _assert_readable_image(path, mime)
        return path, mime
    raise ServiceValidationError(
        translation_domain=DOMAIN,
        translation_key="invalid_media_reference",
        translation_placeholders={"media": image_ref},
    )


def _assert_readable_image(path: Path, mime: str) -> None:
    """Reject missing, oversized, or non-image files."""
    if not path.is_file():
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="attachment_not_found",
            translation_placeholders={"path": path.name},
        )
    if not mime.startswith("image/"):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="attachment_unsupported_type",
            translation_placeholders={"path": path.name},
        )
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="attachment_too_large",
            translation_placeholders={
                "path": path.name,
                "max_mb": str(MAX_IMAGE_BYTES // (1024 * 1024)),
            },
        )


def _publish_filename(source: Path, filename: str | None, mime: str) -> str:
    """Return a safe filename under www/spacexai."""
    if filename:
        name = Path(filename).name
        if _SAFE_FILENAME.match(name) and Path(name).suffix.lower() in _IMAGE_EXTENSIONS:
            return name
        stem = slugify(Path(name).stem) or "spacexai-notify"
        ext = Path(name).suffix.lower()
        if ext not in _IMAGE_EXTENSIONS:
            ext = _extension_for_mime(mime)
        return f"{stem}{ext}"
    if _SAFE_FILENAME.match(source.name) and source.suffix.lower() in _IMAGE_EXTENSIONS:
        return source.name
    return f"spacexai-notify{_extension_for_mime(mime)}"


def _extension_for_mime(mime: str) -> str:
    """Return a filename extension for a MIME type."""
    if mime == "image/png":
        return ".png"
    if mime == "image/webp":
        return ".webp"
    if mime == "image/gif":
        return ".gif"
    return ".jpg"


def _copy_publish(source: Path, dest_dir: Path, dest: Path) -> None:
    """Create the publish directory and copy the image."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    _safe_under(dest_dir, dest)
    copyfile(source, dest)


def _safe_under(root: Path, candidate: Path) -> Path:
    """Resolve candidate and require it to stay under root."""
    resolved = candidate.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="invalid_media_reference",
            translation_placeholders={"media": str(candidate)},
        )
    return resolved


def _data_uri(path: Path, mime: str) -> str:
    """Encode a local image as a data URI."""
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _absolute_url(hass: HomeAssistant, local_path: str) -> str:
    """Prefix a /local path with the best available Home Assistant URL."""
    try:
        base = get_url(hass, prefer_external=True, prefer_cloud=True)
    except NoURLAvailableError:
        try:
            base = get_url(hass)
        except NoURLAvailableError:
            return local_path
    return f"{base.rstrip('/')}{local_path}"
