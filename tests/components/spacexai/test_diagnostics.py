"""Tests for SpaceXAI diagnostics."""

import json
from unittest.mock import AsyncMock

from homeassistant.components.diagnostics import REDACTED
from homeassistant.const import CONF_PROMPT
from homeassistant.core import HomeAssistant

from .conftest import ACCESS_TOKEN, ACCOUNT_ID, REFRESH_TOKEN

from tests.common import MockConfigEntry
from tests.components.diagnostics import get_diagnostics_for_config_entry
from tests.typing import ClientSessionGenerator


async def test_diagnostics_are_sanitized(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    setup_credentials: None,
    hass_client: ClientSessionGenerator,
) -> None:
    """Exclude OAuth credentials and redact account identity."""
    subentry = next(
        entry
        for entry in mock_config_entry.subentries.values()
        if entry.subentry_type == "conversation"
    )
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={**subentry.data, CONF_PROMPT: "private household prompt"},
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, mock_config_entry
    )
    assert diagnostics["account"] == {
        "account_id": REDACTED,
        "name": REDACTED,
        "email": REDACTED,
    }
    assert diagnostics["auth_implementation"] == "spacexai"
    assert "expires_at" in diagnostics["oauth"]
    assert "token" not in diagnostics
    assert "access_token" not in diagnostics["oauth"]
    assert "refresh_token" not in diagnostics["oauth"]
    assert diagnostics["available_models"] == ["grok-4.5", "grok-4.3"]
    assert diagnostics["conversation"][0]["model"] == "grok-4.5"
    assert diagnostics["conversation"][0]["model_entitled"] is True
    assert diagnostics["conversation"][0][CONF_PROMPT] == REDACTED
    serialized = json.dumps(diagnostics)
    assert ACCESS_TOKEN not in serialized
    assert REFRESH_TOKEN not in serialized
    assert ACCOUNT_ID not in serialized
    assert "home@example.com" not in serialized
    assert "private household prompt" not in serialized
    assert '"access_token"' not in serialized
    assert '"refresh_token"' not in serialized
