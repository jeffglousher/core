"""Tests for SpaceXAI setup."""

from unittest.mock import MagicMock, patch

import pytest
from spacexai_subscription_client import AuthenticationError, SpaceXAISubscriptionError
from spacexai_subscription_client.const import GROK_CLI_OAUTH_CLIENT_ID, TOKEN_URL

from homeassistant.components.spacexai import create_client, oauth_implementation
from homeassistant.components.spacexai.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.httpx_client import get_async_client

from . import setup_integration

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker


async def test_setup_and_unload(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Set up and unload the Conversation platform."""
    await setup_integration(hass, mock_config_entry)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get("conversation.grok") is not None
    mock_spacexai_subscription_client.async_list_models.assert_awaited_once_with(
        "access-token"
    )
    device = device_registry.async_get_device_by_identifier(
        (DOMAIN, "conversation-subentry"), mock_config_entry.entry_id
    )
    assert device is not None
    assert device.manufacturer == "SpaceXAI"
    assert device.model == "grok-4.6"
    assert device.entry_type is dr.DeviceEntryType.SERVICE

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.parametrize(
    ("error", "state"),
    [
        pytest.param(
            AuthenticationError,
            ConfigEntryState.SETUP_ERROR,
            id="authentication",
        ),
        pytest.param(
            SpaceXAISubscriptionError,
            ConfigEntryState.SETUP_RETRY,
            id="connection",
        ),
    ],
)
async def test_setup_error(
    hass: HomeAssistant,
    error: type[SpaceXAISubscriptionError],
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    state: ConfigEntryState,
) -> None:
    """Translate client failures during setup."""
    mock_spacexai_subscription_client.async_list_models.side_effect = error
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is state


async def test_setup_without_models(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Retry setup when the account has no available models."""
    mock_spacexai_subscription_client.async_list_models.return_value = ()
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_create_client_uses_shared_sessions(hass: HomeAssistant) -> None:
    """Inject Home Assistant's shared HTTP sessions into the client."""
    with patch(
        "homeassistant.components.spacexai.SpaceXAISubscriptionClient"
    ) as client_class:
        client = create_client(hass)

    assert client is client_class.return_value
    client_class.assert_called_once_with(
        async_get_clientsession(hass),
        get_async_client(hass),
    )


async def test_oauth_token_refresh(
    aioclient_mock: AiohttpClientMocker, hass: HomeAssistant
) -> None:
    """Refresh an OAuth token through the configured token endpoint."""
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )

    token = await oauth_implementation(hass).async_refresh_token(
        {
            "access_token": "old-access-token",
            "refresh_token": "old-refresh-token",
            "expires_in": 3600,
            "expires_at": 0,
            "token_type": "Bearer",
        }
    )

    assert token["access_token"] == "new-access-token"
    assert token["refresh_token"] == "new-refresh-token"
    assert aioclient_mock.mock_calls[0][2] == {
        "client_id": GROK_CLI_OAUTH_CLIENT_ID,
        "grant_type": "refresh_token",
        "refresh_token": "old-refresh-token",
    }
