"""Tests for SpaceXAI text-to-speech."""

from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from spacexai_subscription_client import (
    AuthenticationError,
    InvalidResponseError,
    SpaceXAISubscriptionError,
)

from homeassistant.components import tts
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import setup_integration

from tests.common import MockConfigEntry
from tests.typing import ClientSessionGenerator


def _entity(hass: HomeAssistant) -> tts.TextToSpeechEntity:
    """Return the configured text-to-speech entity."""
    entity = hass.data[tts.DOMAIN].get_entity("tts.grok_tts_text_to_speech")
    assert entity is not None
    return entity


async def test_properties_and_synthesis(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Expose supported options and synthesize MP3 speech."""
    await setup_integration(hass, mock_config_entry_with_speech)
    entity = _entity(hass)

    assert entity.name == "Text-to-speech"
    assert entity.default_language == "en"
    assert entity.default_options == {tts.ATTR_VOICE: "eve"}
    assert [voice.voice_id for voice in entity.async_get_supported_voices("en")] == [
        "altair",
        "ara",
        "atlas",
        "aurora",
        "carina",
        "castor",
        "celeste",
        "cosmo",
        "eve",
        "helix",
        "helios",
        "iris",
        "kepler",
        "leo",
        "liora",
        "lumen",
        "luna",
        "lux",
        "naksh",
        "orion",
        "perseus",
        "rex",
        "rigel",
        "sal",
        "sirius",
        "ursa",
        "zagan",
        "zenith",
    ]

    result = await entity.async_get_tts_audio(
        "Welcome home", "en", {tts.ATTR_VOICE: "leo"}
    )

    assert result == ("mp3", b"speech")
    mock_spacexai_subscription_client.async_synthesize_speech.assert_awaited_once_with(
        "access-token",
        text="Welcome home",
        voice_id="leo",
        language="en",
        speed=1.1,
    )


@pytest.mark.usefixtures("mock_tts_cache_dir")
async def test_tts_http_playback(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Generate and retrieve speech through Home Assistant's TTS manager."""
    await setup_integration(hass, mock_config_entry_with_speech)
    client = await hass_client()

    response = await client.post(
        "/api/tts_get_url",
        json={
            "engine_id": "tts.grok_tts_text_to_speech",
            "message": "HTTP playback smoke",
            "language": "en",
            "cache": False,
        },
    )
    assert response.status == HTTPStatus.OK
    path = (await response.json())["path"]

    response = await client.get(path)
    assert response.status == HTTPStatus.OK
    assert await response.read() == b"speech"
    mock_spacexai_subscription_client.async_synthesize_speech.assert_awaited_once_with(
        "access-token",
        text="HTTP playback smoke",
        voice_id="eve",
        language="en",
        speed=1.1,
    )


@pytest.mark.parametrize(
    ("error", "translation_key"),
    [
        pytest.param(AuthenticationError, "invalid_auth", id="authentication"),
        pytest.param(InvalidResponseError, "invalid_response", id="response"),
        pytest.param(SpaceXAISubscriptionError, "api_error", id="api"),
    ],
)
async def test_synthesis_error(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    error: type[SpaceXAISubscriptionError],
    translation_key: str,
) -> None:
    """Translate client failures into localized Home Assistant errors."""
    mock_spacexai_subscription_client.async_synthesize_speech.side_effect = error
    await setup_integration(hass, mock_config_entry_with_speech)

    with pytest.raises(HomeAssistantError) as err:
        await _entity(hass).async_get_tts_audio("Hello", "en", {})

    assert err.value.translation_domain == "spacexai"
    assert err.value.translation_key == translation_key
