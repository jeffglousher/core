"""Tests for SpaceXAI text-to-speech."""

from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from spacexai_subscription_client import (
    AuthenticationError,
    InvalidResponseError,
    SpaceXAISubscriptionError,
)
from spacexai_subscription_client.const import TOKEN_URL

from homeassistant.components import tts
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from . import setup_integration

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker
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
    ("error", "translation_key", "reauth_flow_count"),
    [
        pytest.param(AuthenticationError, "invalid_auth", 1, id="authentication"),
        pytest.param(InvalidResponseError, "invalid_response", 0, id="response"),
        pytest.param(SpaceXAISubscriptionError, "api_error", 0, id="api"),
    ],
)
async def test_synthesis_error(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    error: type[SpaceXAISubscriptionError],
    reauth_flow_count: int,
    translation_key: str,
) -> None:
    """Translate client failures into localized Home Assistant errors."""
    mock_spacexai_subscription_client.async_synthesize_speech.side_effect = error
    await setup_integration(hass, mock_config_entry_with_speech)

    with pytest.raises(HomeAssistantError) as err:
        await _entity(hass).async_get_tts_audio("Hello", "en", {})

    assert err.value.translation_domain == "spacexai"
    assert err.value.translation_key == translation_key
    assert len(hass.config_entries.flow.async_progress()) == reauth_flow_count


@pytest.mark.parametrize(
    ("status", "error_code", "translation_key", "reauth_flow_count"),
    [
        pytest.param(400, "invalid_grant", "invalid_auth", 1, id="revoked"),
        pytest.param(503, "temporarily_unavailable", "api_error", 0, id="transient"),
    ],
)
@pytest.mark.usefixtures("mock_spacexai_subscription_client")
async def test_token_refresh_error(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    status: int,
    error_code: str,
    translation_key: str,
    reauth_flow_count: int,
) -> None:
    """Start reauthentication only for a rejected OAuth refresh token."""
    await setup_integration(hass, mock_config_entry_with_speech)
    hass.config_entries.async_update_entry(
        mock_config_entry_with_speech,
        data={
            **mock_config_entry_with_speech.data,
            "token": {
                **mock_config_entry_with_speech.data["token"],
                "expires_at": 0,
            },
        },
    )
    aioclient_mock.post(TOKEN_URL, status=status, json={"error": error_code})

    with pytest.raises(HomeAssistantError) as err:
        await _entity(hass).async_get_tts_audio("Hello", "en", {})

    await hass.async_block_till_done()
    assert err.value.translation_key == translation_key
    assert aioclient_mock.call_count == 1
    assert len(hass.config_entries.flow.async_progress()) == reauth_flow_count


@pytest.mark.parametrize("access_token", [None, "", 123])
@pytest.mark.usefixtures("mock_spacexai_subscription_client")
async def test_missing_access_token_starts_reauth(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    access_token: str | int | None,
) -> None:
    """Recover an entry whose stored access token is unusable."""
    await setup_integration(hass, mock_config_entry_with_speech)
    hass.config_entries.async_update_entry(
        mock_config_entry_with_speech,
        data={
            **mock_config_entry_with_speech.data,
            "token": {
                **mock_config_entry_with_speech.data["token"],
                "access_token": access_token,
            },
        },
    )

    with pytest.raises(HomeAssistantError) as err:
        await _entity(hass).async_get_tts_audio("Hello", "en", {})

    assert err.value.translation_key == "invalid_auth"
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"
    assert flows[0]["step_id"] == "reauth_confirm"
