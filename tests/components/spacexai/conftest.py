"""Fixtures for SpaceXAI tests."""

from collections.abc import Generator
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from spacexai_subscription_client import SpaceXAISubscriptionClient

from homeassistant.components.spacexai.const import (
    CONF_CODE_INTERPRETER,
    CONF_TTS_SPEED,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    DOMAIN,
)
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.const import CONF_LLM_HASS_API, CONF_MODEL, CONF_PROMPT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry

ACCESS_TOKEN = "access-token"
REFRESH_TOKEN = "refresh-token"


@pytest.fixture
def enable_assist() -> bool:
    """Return whether the conversation agent can control Home Assistant."""
    return False


def _mock_config_entry(
    enable_assist: bool,
    *,
    enable_provider_tools: bool = False,
    include_ai_task: bool = False,
    include_speech: bool = False,
) -> MockConfigEntry:
    """Return a configured SpaceXAI entry."""
    data: dict[str, Any] = {
        CONF_MODEL: "grok-4.6",
        CONF_PROMPT: "Be helpful.",
    }
    if enable_assist:
        data[CONF_LLM_HASS_API] = [llm.LLM_API_ASSIST]
    if enable_provider_tools:
        data.update(
            {
                CONF_CODE_INTERPRETER: True,
                CONF_WEB_SEARCH: True,
                CONF_X_SEARCH: True,
            }
        )
    subentries = [
        ConfigSubentryData(
            data=data,
            subentry_id="conversation-subentry",
            subentry_type="conversation",
            title="Grok",
            unique_id=None,
        )
    ]
    if include_ai_task:
        subentries.append(
            ConfigSubentryData(
                data={CONF_MODEL: "grok-4.6"},
                subentry_id="ai-task-subentry",
                subentry_type="ai_task_data",
                title="Grok AI Task",
                unique_id=None,
            )
        )
    if include_speech:
        subentries.extend(
            [
                ConfigSubentryData(
                    data={},
                    subentry_id="stt-subentry",
                    subentry_type="stt",
                    title="Grok Speech-to-text",
                    unique_id=None,
                ),
                ConfigSubentryData(
                    data={CONF_TTS_SPEED: 1.1},
                    subentry_id="tts-subentry",
                    subentry_type="tts",
                    title="Grok TTS",
                    unique_id=None,
                ),
            ]
        )
    return MockConfigEntry(
        domain=DOMAIN,
        title="Home User",
        unique_id="account-123",
        data={
            "auth_implementation": DOMAIN,
            "token": {
                "access_token": ACCESS_TOKEN,
                "refresh_token": REFRESH_TOKEN,
                "expires_at": time.time() + 3600,
                "expires_in": 3600,
                "token_type": "Bearer",
            },
        },
        subentries_data=subentries,
    )


@pytest.fixture
def mock_config_entry(enable_assist: bool) -> MockConfigEntry:
    """Return a configured SpaceXAI entry."""
    return _mock_config_entry(enable_assist)


@pytest.fixture
def mock_config_entry_with_assist() -> MockConfigEntry:
    """Return a configured SpaceXAI entry with Assist tools enabled."""
    return _mock_config_entry(True)


@pytest.fixture
def mock_config_entry_with_provider_tools() -> MockConfigEntry:
    """Return a configured entry with provider-hosted tools enabled."""
    return _mock_config_entry(False, enable_provider_tools=True)


@pytest.fixture
def mock_config_entry_with_ai_task() -> MockConfigEntry:
    """Return a configured entry with an AI Task entity."""
    return _mock_config_entry(False, include_ai_task=True)


@pytest.fixture
def mock_config_entry_with_speech() -> MockConfigEntry:
    """Return a configured entry with speech entities."""
    return _mock_config_entry(False, include_speech=True)


@pytest.fixture
def mock_spacexai_subscription_client() -> Generator[MagicMock]:
    """Return a mocked SpaceXAI client."""
    client = MagicMock(spec=SpaceXAISubscriptionClient)
    client.async_list_models = AsyncMock(return_value=("grok-4.6",))
    client.async_create_response = AsyncMock()
    client.async_generate_image = AsyncMock()
    client.async_edit_image = AsyncMock()
    client.async_transcribe = AsyncMock(return_value="Turn on the kitchen light")
    client.async_synthesize_speech = AsyncMock(return_value=b"speech")
    client.async_generate_video = AsyncMock()
    with patch("homeassistant.components.spacexai.create_client", return_value=client):
        yield client


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Prevent config flows from setting up created entries."""
    with patch(
        "homeassistant.components.spacexai.async_setup_entry",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture(autouse=True)
async def setup_homeassistant(hass: HomeAssistant) -> None:
    """Set up the Home Assistant LLM API."""
    assert await async_setup_component(hass, "homeassistant", {})
