"""Diagnostics for SpaceXAI."""

from typing import Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_LLM_HASS_API, CONF_MODEL
from homeassistant.core import HomeAssistant

from .const import CONF_CODE_INTERPRETER, CONF_TTS_SPEED, CONF_WEB_SEARCH, CONF_X_SEARCH
from .models import SpaceXAIConfigEntry

_CONFIG_KEYS = (
    CONF_MODEL,
    CONF_CODE_INTERPRETER,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    CONF_TTS_SPEED,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SpaceXAIConfigEntry
) -> dict[str, Any]:
    """Return configuration metadata without credentials or user-authored content."""
    return {
        "entry_version": f"{entry.version}.{entry.minor_version}",
        "state": entry.state.value,
        "models": entry.runtime_data.models
        if entry.state is ConfigEntryState.LOADED
        else None,
        "subentries": [
            {
                "subentry_type": subentry.subentry_type,
                "data": {
                    key: subentry.data[key]
                    for key in _CONFIG_KEYS
                    if key in subentry.data
                },
                "llm_api_count": len(subentry.data.get(CONF_LLM_HASS_API, [])),
            }
            for subentry in entry.subentries.values()
        ],
    }
