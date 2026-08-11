"""Tests for SpaceXAI diagnostics."""

import json

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.filters import props

from homeassistant.components.diagnostics import REDACTED
from homeassistant.const import CONF_PROMPT
from homeassistant.core import HomeAssistant

from . import conversation_subentry
from .conftest import ACCESS_TOKEN, ACCOUNT_ID, REFRESH_TOKEN

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator


@pytest.mark.usefixtures("setup_credentials", "mock_validate")
async def test_diagnostics_are_sanitized(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    hass_client: ClientSessionGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Config entry diagnostics redact secrets."""
    subentry = conversation_subentry(mock_config_entry)
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={**subentry.data, CONF_PROMPT: "private household prompt"},
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry
    )

    assert diagnostics == snapshot(exclude=props("expires_at"))
    assert diagnostics["account"] == {
        "account_id": REDACTED,
        "name": REDACTED,
        "email": REDACTED,
    }
    assert diagnostics["ai_task"][0]["model"] == "grok-4.5"
    assert diagnostics["ai_task"][0]["model_entitled"] is True
    serialized = json.dumps(diagnostics)
    assert ACCESS_TOKEN not in serialized
    assert REFRESH_TOKEN not in serialized
    assert ACCOUNT_ID not in serialized
    assert "home@example.com" not in serialized
    assert "private household prompt" not in serialized
    assert '"access_token"' not in serialized
    assert '"refresh_token"' not in serialized
