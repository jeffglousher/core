"""Diagnostics support for SpaceXAI."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_MODEL
from homeassistant.core import HomeAssistant

from . import SpaceXAIConfigEntry, SpaceXAIData
from .const import DEFAULT_IMAGE_MODEL, DEFAULT_MODEL, DEFAULT_VIDEO_MODEL

TO_REDACT = {"account_id", "email", "name", "prompt"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SpaceXAIConfigEntry
) -> dict[str, Any]:
    """Return sanitized diagnostics for a SpaceXAI account."""
    runtime = entry.runtime_data
    subentry_types = {subentry.subentry_type for subentry in entry.subentries.values()}
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
        "available_image_models": [model.id for model in runtime.snapshot.image_models],
        "available_video_models": [model.id for model in runtime.snapshot.video_models],
        "selectable_image_models": list(runtime.snapshot.selectable_image_models),
        "selectable_video_models": list(runtime.snapshot.selectable_video_models),
        "fallback_chat_model": DEFAULT_MODEL,
        "fallback_image_model": DEFAULT_IMAGE_MODEL,
        "fallback_video_model": DEFAULT_VIDEO_MODEL,
        "platforms": {
            "conversation": "conversation" in subentry_types,
            "ai_task": "ai_task_data" in subentry_types,
            "stt": "stt" in subentry_types,
            "tts": "tts" in subentry_types,
        },
        "conversation": _subentry_diagnostics(runtime, entry, "conversation"),
        "ai_task": _subentry_diagnostics(runtime, entry, "ai_task_data"),
        "stt": _subentry_diagnostics(runtime, entry, "stt"),
        "tts": _subentry_diagnostics(runtime, entry, "tts"),
    }


def _subentry_diagnostics(
    runtime: SpaceXAIData,
    entry: SpaceXAIConfigEntry,
    subentry_type: str,
) -> list[dict[str, Any]]:
    """Return redacted diagnostics for one subentry type."""
    results: list[dict[str, Any]] = []
    for subentry in entry.subentries.values():
        if subentry.subentry_type != subentry_type:
            continue
        payload: dict[str, Any] = {
            "title": subentry.title,
            **subentry.data,
        }
        if CONF_MODEL in subentry.data:
            payload["model_entitled"] = runtime.snapshot.has_model(
                subentry.data[CONF_MODEL]
            )
        results.append(async_redact_data(payload, TO_REDACT))
    return results
