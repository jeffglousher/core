"""Tests for SpaceXAI Assist pipeline helpers."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.assist_pipeline import async_get_pipelines
from homeassistant.components.assist_pipeline.pipeline import KEY_ASSIST_PIPELINE
from homeassistant.components.spacexai.assist import async_setup_assist_pipeline
from homeassistant.components.spacexai.const import CONF_DEFAULT_ASSIST
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("setup_credentials")
async def test_assist_setup_creates_pipeline_and_clears_flag(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Create a Grok Assist pipeline once, then clear the install-time flag."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={**mock_config_entry.data, CONF_DEFAULT_ASSIST: True},
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    pipelines = async_get_pipelines(hass)
    grok = next((item for item in pipelines if item.name == "Grok"), None)
    assert grok is not None
    assert grok.conversation_engine.startswith("conversation.")
    assert grok.stt_engine is not None
    assert grok.stt_engine.startswith("stt.")
    assert grok.tts_engine is not None
    assert grok.tts_engine.startswith("tts.")
    assert CONF_DEFAULT_ASSIST not in mock_config_entry.data


@pytest.mark.usefixtures("setup_credentials")
async def test_assist_never_mutates_unrelated_preferred_pipeline(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Do not rewrite the preferred pipeline when a Grok pipeline cannot be created."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    preferred_before = hass.data[
        KEY_ASSIST_PIPELINE
    ].pipeline_store.async_get_preferred_item()

    with (
        patch(
            "homeassistant.components.spacexai.assist.async_create_default_pipeline",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "homeassistant.components.spacexai.assist.async_get_pipelines",
            return_value=[],
        ),
        patch(
            "homeassistant.components.spacexai.assist.stt.async_default_engine",
            return_value=None,
        ),
    ):
        applied = await async_setup_assist_pipeline(
            hass, mock_config_entry, set_preferred=True
        )

    assert applied is False
    preferred_after = hass.data[
        KEY_ASSIST_PIPELINE
    ].pipeline_store.async_get_preferred_item()
    assert preferred_after == preferred_before


@pytest.mark.usefixtures("setup_credentials")
async def test_assist_updates_owned_pipeline_with_speech_engines(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Update a pipeline owned by this conversation engine and wire speech."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    conversation_entity = next(
        entity.entity_id
        for entity in entity_registry.entities.values()
        if entity.config_entry_id == mock_config_entry.entry_id
        and entity.domain == "conversation"
    )
    stt_entity = next(
        entity.entity_id
        for entity in entity_registry.entities.values()
        if entity.config_entry_id == mock_config_entry.entry_id
        and entity.domain == "stt"
    )
    tts_entity = next(
        entity.entity_id
        for entity in entity_registry.entities.values()
        if entity.config_entry_id == mock_config_entry.entry_id
        and entity.domain == "tts"
    )

    existing = MagicMock()
    existing.id = "pipeline-grok"
    existing.name = "Grok"
    existing.conversation_engine = conversation_entity

    with (
        patch(
            "homeassistant.components.spacexai.assist.async_update_pipeline",
            new_callable=AsyncMock,
        ) as update_pipeline,
        patch(
            "homeassistant.components.spacexai.assist.async_get_pipelines",
            return_value=[existing],
        ),
    ):
        applied = await async_setup_assist_pipeline(
            hass, mock_config_entry, set_preferred=False
        )

    assert applied is True
    update_pipeline.assert_awaited_once()
    kwargs = update_pipeline.await_args.kwargs
    assert kwargs["conversation_engine"] == conversation_entity
    assert kwargs["stt_engine"] == stt_entity
    assert kwargs["tts_engine"] == tts_entity


@pytest.mark.usefixtures("setup_credentials")
async def test_assist_does_not_hijack_foreign_pipeline_named_grok(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Never mutate a pipeline that only shares the Grok display name."""
    assert await async_setup_component(hass, "assist_pipeline", {})
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    conversation_entity = next(
        entity.entity_id
        for entity in entity_registry.entities.values()
        if entity.config_entry_id == mock_config_entry.entry_id
        and entity.domain == "conversation"
    )

    foreign = MagicMock()
    foreign.id = "pipeline-foreign"
    foreign.name = "Grok"
    foreign.conversation_engine = "conversation.home_assistant"

    created = MagicMock()
    created.id = "pipeline-new"
    created.name = "Grok"
    created.conversation_engine = "stt.home_assistant_cloud"

    with (
        patch(
            "homeassistant.components.spacexai.assist.async_get_pipelines",
            return_value=[foreign],
        ),
        patch(
            "homeassistant.components.spacexai.assist.async_create_default_pipeline",
            new_callable=AsyncMock,
            return_value=created,
        ) as create_pipeline,
        patch(
            "homeassistant.components.spacexai.assist.async_update_pipeline",
            new_callable=AsyncMock,
        ) as update_pipeline,
        patch(
            "homeassistant.components.spacexai.assist.stt.async_default_engine",
            return_value="stt.home_assistant_cloud",
        ),
        patch(
            "homeassistant.components.spacexai.assist.tts.async_default_engine",
            return_value="tts.home_assistant_cloud",
        ),
    ):
        applied = await async_setup_assist_pipeline(
            hass, mock_config_entry, set_preferred=False
        )

    assert applied is True
    create_pipeline.assert_awaited_once()
    assert (
        update_pipeline.await_args.kwargs["conversation_engine"] == conversation_entity
    )
    # Foreign pipeline must not be the update target.
    assert update_pipeline.await_args.args[1] is created
