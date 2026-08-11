"""Diagnostics support for SpaceXAI."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant

from . import SpaceXAIConfigEntry, SpaceXAIData

TO_REDACT = {
    "access_token",
    "account_id",
    "email",
    "name",
    "prompt",
    "refresh_token",
    "token",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SpaceXAIConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime = entry.runtime_data
    return {
        "account": async_redact_data(
            {
                "account_id": runtime.snapshot.account.subject,
                "name": runtime.snapshot.account.name,
                "email": runtime.snapshot.account.email,
            },
            TO_REDACT,
        ),
        "auth_implementation": entry.data["auth_implementation"],
        "oauth": {
            "expires_at": entry.data["token"].get("expires_at"),
            "scope": entry.data["token"].get("scope"),
        },
        "available_models": [model.id for model in runtime.snapshot.models],
        "conversation": _subentry_diagnostics(runtime, entry, "conversation"),
        "ai_task": _subentry_diagnostics(runtime, entry, "ai_task_data"),
    }


def _subentry_diagnostics(
    runtime: SpaceXAIData,
    entry: SpaceXAIConfigEntry,
    subentry_type: str,
) -> list[dict[str, Any]]:
    """Return diagnostics for one subentry type."""
    return [
        async_redact_data(
            {
                "title": subentry.title,
                **subentry.data,
                "model_entitled": runtime.snapshot.has_model(subentry.data[CONF_MODEL]),
            },
            TO_REDACT,
        )
        for subentry in entry.subentries.values()
        if subentry.subentry_type == subentry_type
    ]
