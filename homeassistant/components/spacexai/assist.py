"""Assist pipeline helpers for SpaceXAI."""

from __future__ import annotations

from homeassistant.components import conversation, stt, tts
from homeassistant.components.assist_pipeline import (
    async_create_default_pipeline,
    async_get_pipelines,
    async_setup_pipeline_store,
    async_update_pipeline,
)
from homeassistant.components.assist_pipeline.pipeline import KEY_ASSIST_PIPELINE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from . import SpaceXAIConfigEntry
from .const import DEFAULT_CONVERSATION_NAME, LOGGER


async def async_setup_assist_pipeline(
    hass: HomeAssistant,
    entry: SpaceXAIConfigEntry,
    *,
    set_preferred: bool,
) -> bool:
    """Create or update a Grok Assist pipeline after platforms are loaded.

    Returns True when a SpaceXAI-owned pipeline was created or updated.
    Never mutates an unrelated preferred pipeline or a foreign pipeline that
    only shares the "Grok" display name.
    """
    await async_setup_pipeline_store(hass)

    registry = er.async_get(hass)
    conversation_entity_id: str | None = None
    stt_entity_id: str | None = None
    tts_entity_id: str | None = None
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.domain == conversation.DOMAIN and conversation_entity_id is None:
            conversation_entity_id = entity.entity_id
        elif entity.domain == stt.DOMAIN and stt_entity_id is None:
            stt_entity_id = entity.entity_id
        elif entity.domain == tts.DOMAIN and tts_entity_id is None:
            tts_entity_id = entity.entity_id

    if conversation_entity_id is None:
        LOGGER.warning(
            "SpaceXAI Assist setup skipped; no conversation entity for entry %s",
            entry.entry_id,
        )
        return False

    # Only claim pipelines that already use this conversation engine.
    pipeline = next(
        (
            item
            for item in async_get_pipelines(hass)
            if item.conversation_engine == conversation_entity_id
        ),
        None,
    )

    stt_engine = stt_entity_id or stt.async_default_engine(hass)
    tts_engine = tts_entity_id or tts.async_default_engine(hass)

    if pipeline is not None:
        kwargs: dict[str, object] = {
            "conversation_engine": conversation_entity_id,
        }
        if stt_engine:
            kwargs["stt_engine"] = stt_engine
        if tts_engine:
            kwargs["tts_engine"] = tts_engine
        await async_update_pipeline(hass, pipeline, **kwargs)  # type: ignore[arg-type]
    else:
        if not stt_engine or not tts_engine:
            LOGGER.warning(
                "SpaceXAI Assist setup skipped; no STT/TTS engines available "
                "to create pipeline for entry %s",
                entry.entry_id,
            )
            return False
        pipeline = await async_create_default_pipeline(
            hass,
            stt_engine_id=stt_engine,
            tts_engine_id=tts_engine,
            pipeline_name=DEFAULT_CONVERSATION_NAME,
        )
        if pipeline is None:
            LOGGER.warning(
                "SpaceXAI Assist setup could not create pipeline for entry %s",
                entry.entry_id,
            )
            return False
        await async_update_pipeline(
            hass,
            pipeline,
            conversation_engine=conversation_entity_id,
            stt_engine=stt_engine,
            tts_engine=tts_engine,
        )

    if set_preferred:
        store = hass.data[KEY_ASSIST_PIPELINE].pipeline_store
        store.async_set_preferred_item(pipeline.id)
        LOGGER.info(
            "Set Assist preferred pipeline to %s (%s)",
            pipeline.name,
            pipeline.id,
        )
    return True
