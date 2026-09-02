"""Tests for SpaceXAI diagnostics."""

from copy import deepcopy
from unittest.mock import MagicMock

from syrupy.assertion import SnapshotAssertion

from homeassistant.components.spacexai.const import DOMAIN
from homeassistant.const import CONF_LLM_HASS_API
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from . import setup_integration

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator


async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_provider_tools: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Exclude identities, prompts, tokens, API names, and unknown future fields."""
    entry = mock_config_entry_with_provider_tools
    entry.add_to_hass(hass)
    subentry = entry.subentries["conversation-subentry"]
    hass.config_entries.async_update_subentry(
        entry,
        subentry,
        data={
            **subentry.data,
            CONF_LLM_HASS_API: ["private-api-name"],
            "future_secret": "private-subentry-value",
        },
    )
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, "future_secret": "private-account-value"},
        options={"future_secret": "private-option-value"},
    )
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    original_data = deepcopy(entry.as_dict())
    mock_spacexai_subscription_client.reset_mock()

    assert await get_diagnostics_for_config_entry(hass, hass_client, entry) == snapshot

    assert entry.as_dict() == original_data
    assert mock_spacexai_subscription_client.mock_calls == []


async def test_speech_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Include speech configuration without making provider requests."""
    await setup_integration(hass, mock_config_entry_with_speech)
    mock_spacexai_subscription_client.reset_mock()

    assert (
        await get_diagnostics_for_config_entry(
            hass, hass_client, mock_config_entry_with_speech
        )
        == snapshot
    )

    assert mock_spacexai_subscription_client.mock_calls == []


async def test_not_loaded_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Allow diagnostics before setup has created runtime data."""
    assert await async_setup_component(hass, DOMAIN, {})
    mock_config_entry.add_to_hass(hass)

    assert (
        await get_diagnostics_for_config_entry(hass, hass_client, mock_config_entry)
        == snapshot
    )
