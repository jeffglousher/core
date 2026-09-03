"""Actions for SpaceXAI video generation and local media publishing."""

from collections.abc import Mapping
from typing import Any, cast

from spacexai_subscription_client import (
    AuthenticationError,
    InvalidResponseError,
    SpaceXAISubscriptionError,
)
import voluptuous as vol

from homeassistant.const import CONF_MODEL, CONF_PROMPT
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv, selector, service
from homeassistant.helpers.service import async_register_admin_service

from .const import (
    DOMAIN,
    LOGGER,
    RECOMMENDED_VIDEO_MODEL,
    SERVICE_GENERATE_VIDEO,
    SERVICE_PUBLISH_MEDIA,
)
from .entity import async_access_token
from .media import async_persist_video, async_provider_image_url, async_publish_media
from .models import SpaceXAIConfigEntry

CONF_ASPECT_RATIO = "aspect_ratio"
CONF_CONFIG_ENTRY = "config_entry"
CONF_DURATION = "duration"
CONF_IMAGE = "image"
CONF_MEDIA = "media"
CONF_RESOLUTION = "resolution"

_ASPECT_RATIOS = ("1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3")
_RESOLUTIONS = ("480p", "720p", "1080p")
_MEDIA_SELECTOR = selector.MediaSelector(
    selector.MediaSelectorConfig(accept=["image/*", "video/*"])
)

GENERATE_VIDEO_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_CONFIG_ENTRY): selector.ConfigEntrySelector(
            {"integration": DOMAIN}
        ),
        vol.Required(CONF_PROMPT): vol.All(cv.string, vol.Length(min=1)),
        vol.Optional(CONF_MODEL, default=RECOMMENDED_VIDEO_MODEL): vol.All(
            cv.string, vol.Length(min=1)
        ),
        vol.Optional(CONF_IMAGE): selector.MediaSelector(
            selector.MediaSelectorConfig(accept=["image/*"])
        ),
        vol.Optional(CONF_DURATION): vol.All(vol.Coerce(int), vol.Range(min=1, max=15)),
        vol.Optional(CONF_ASPECT_RATIO): vol.In(_ASPECT_RATIOS),
        vol.Optional(CONF_RESOLUTION): vol.In(_RESOLUTIONS),
    }
)
PUBLISH_MEDIA_SCHEMA = vol.Schema({vol.Required(CONF_MEDIA): _MEDIA_SELECTOR})


def async_setup_services(hass: HomeAssistant) -> None:
    """Register SpaceXAI actions."""

    async def async_generate_video(call: ServiceCall) -> ServiceResponse:
        """Generate a video and persist it in local authenticated media."""
        entry: SpaceXAIConfigEntry = service.async_get_config_entry(
            hass, DOMAIN, call.data[CONF_CONFIG_ENTRY]
        )
        image_url = None
        if selected_media := call.data.get(CONF_IMAGE):
            image_url = await async_provider_image_url(
                hass, cast(Mapping[str, str], selected_media)
            )
        try:
            video = await entry.runtime_data.client.async_generate_video(
                await async_access_token(hass, entry),
                model=call.data[CONF_MODEL],
                prompt=call.data[CONF_PROMPT],
                image_url=image_url,
                duration=call.data.get(CONF_DURATION),
                aspect_ratio=call.data.get(CONF_ASPECT_RATIO),
                resolution=call.data.get(CONF_RESOLUTION),
            )
        except AuthenticationError as err:
            entry.async_start_reauth(hass)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
            ) from err
        except InvalidResponseError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_response",
            ) from err
        except SpaceXAISubscriptionError as err:
            LOGGER.error("Error communicating with SpaceXAI: %s", type(err).__name__)
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
            ) from err
        if not video.respect_moderation:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="video_moderated",
            )
        published = await async_persist_video(hass, video.url)
        return {
            **published,
            "duration": video.duration,
            "model": video.model,
        }

    async def async_publish_media_service(call: ServiceCall) -> ServiceResponse:
        """Create a time-limited URL for local media."""
        selected_media = cast(Mapping[str, Any], call.data[CONF_MEDIA])
        return await async_publish_media(hass, selected_media["media_content_id"])

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_GENERATE_VIDEO,
        async_generate_video,
        schema=GENERATE_VIDEO_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_PUBLISH_MEDIA,
        async_publish_media_service,
        schema=PUBLISH_MEDIA_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
