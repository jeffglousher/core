"""Application credentials for SpaceXAI."""

from typing import override

from homeassistant.components.application_credentials import ClientCredential
from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import (
    LocalOAuth2ImplementationWithPkce,
)

from .const import AUTHORIZE_URL, GROK_CLI_OAUTH_CLIENT_ID, OAUTH_SCOPES, TOKEN_URL

# HA Application Credentials requires a secret field; public clients use placeholders.
_PUBLIC_CLIENT_SECRET_PLACEHOLDERS = {"", "-", "none", "null", "public", "n/a"}


def _normalize_client_secret(client_id: str, client_secret: str) -> str:
    """Omit secrets for the public Grok CLI client and placeholder values."""
    secret = client_secret.strip()
    if client_id == GROK_CLI_OAUTH_CLIENT_ID:
        return ""
    if secret.lower() in _PUBLIC_CLIENT_SECRET_PLACEHOLDERS:
        return ""
    return secret


async def async_get_auth_implementation(
    hass: HomeAssistant,
    auth_domain: str,
    credential: ClientCredential,
) -> SpaceXAIOAuth2Implementation:
    """Return the SpaceXAI OAuth implementation."""
    return SpaceXAIOAuth2Implementation(
        hass,
        auth_domain,
        credential.client_id,
        AUTHORIZE_URL,
        TOKEN_URL,
        _normalize_client_secret(credential.client_id, credential.client_secret),
    )


class SpaceXAIOAuth2Implementation(LocalOAuth2ImplementationWithPkce):
    """Authorization Code + PKCE implementation for SpaceXAI."""

    @property
    @override
    def extra_authorize_data(self) -> dict[str, str]:
        """Add subscription access scopes used by the Grok CLI OAuth client."""
        return super().extra_authorize_data | {
            "scope": " ".join(OAUTH_SCOPES),
            "plan": "generic",
            "referrer": "home-assistant",
        }
