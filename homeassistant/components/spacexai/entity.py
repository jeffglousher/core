"""Shared entity helpers for SpaceXAI."""

from spacexai_subscription_client import AuthenticationError

from homeassistant.config_entries import ConfigSubentry
from homeassistant.exceptions import (
    HomeAssistantError,
    OAuth2TokenRequestError,
    OAuth2TokenRequestReauthError,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.entity import Entity

from . import SpaceXAIConfigEntry
from .const import DOMAIN


async def async_access_token(entry: SpaceXAIConfigEntry) -> str:
    """Return a valid OAuth access token."""
    try:
        await entry.runtime_data.oauth_session.async_ensure_token_valid()
    except (AuthenticationError, OAuth2TokenRequestReauthError) as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="invalid_auth",
        ) from err
    except OAuth2TokenRequestError as err:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="api_error",
        ) from err
    access_token = entry.runtime_data.oauth_session.token.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise HomeAssistantError(
            translation_domain=DOMAIN,
            translation_key="invalid_auth",
        )
    return access_token


class SpaceXAISpeechEntity(Entity):
    """Base entity for a SpaceXAI speech service."""

    _attr_has_entity_name = True

    def __init__(
        self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry, model: str
    ) -> None:
        """Initialize a SpaceXAI speech entity."""
        self.entry = entry
        self.subentry = subentry
        self._attr_unique_id = subentry.subentry_id
        self._attr_device_info = dr.DeviceInfo(
            identifiers={(DOMAIN, subentry.subentry_id)},
            name=subentry.title,
            manufacturer="SpaceXAI",
            model=model,
            entry_type=dr.DeviceEntryType.SERVICE,
        )

    async def _async_access_token(self) -> str:
        """Return a valid OAuth access token."""
        return await async_access_token(self.entry)
