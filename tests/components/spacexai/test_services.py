"""Tests for SpaceXAI admin services."""

from unittest.mock import AsyncMock

import pytest

from homeassistant.components.spacexai.client import GeneratedVideo
from homeassistant.components.spacexai.const import DEFAULT_VIDEO_MODEL, DOMAIN
from homeassistant.components.spacexai.errors import (
    ErrorContext,
    Operation,
    PermanentProviderError,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_returns_provider_url(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Return the completed Imagine video URL for an entitled model."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        return_value=GeneratedVideo(
            url="https://vidgen.example/video.mp4",
            model=DEFAULT_VIDEO_MODEL,
        )
    )

    response = await hass.services.async_call(
        DOMAIN,
        "generate_video",
        {
            "config_entry": entry.entry_id,
            "prompt": "A bouncing red ball",
            "duration": 3,
        },
        blocking=True,
        return_response=True,
    )

    assert response == {
        "url": "https://vidgen.example/video.mp4",
        "model": DEFAULT_VIDEO_MODEL,
    }
    entry.runtime_data.client.async_generate_video.assert_awaited_once()


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_rejects_unknown_entry(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Reject calls that do not target a loaded SpaceXAI entry."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": "missing-entry",
                "prompt": "A bouncing red ball",
            },
            blocking=True,
            return_response=True,
        )


@pytest.mark.usefixtures("setup_credentials")
async def test_generate_video_translates_provider_errors(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Translate SpaceXAI provider failures into HomeAssistantError."""
    entry = setup_integration
    entry.runtime_data.client.async_generate_video = AsyncMock(
        side_effect=PermanentProviderError(
            "video failed",
            context=ErrorContext(
                operation=Operation.VIDEO,
                model=DEFAULT_VIDEO_MODEL,
                provider_code="failed",
            ),
        )
    )

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "generate_video",
            {
                "config_entry": entry.entry_id,
                "prompt": "A bouncing red ball",
            },
            blocking=True,
            return_response=True,
        )
