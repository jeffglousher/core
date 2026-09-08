"""Tests for SpaceXAI text-to-speech."""

from http import HTTPStatus
from unittest.mock import MagicMock

import pytest
from spacexai_subscription_client import (
    AuthenticationError,
    InvalidResponseError,
    PermissionDeniedError,
    SpaceXAISubscriptionError,
)
from spacexai_subscription_client.const import TOKEN_URL

from homeassistant.components import media_source, tts
from homeassistant.components.spacexai.const import DOMAIN
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component

from . import setup_integration

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator, WebSocketGenerator


@pytest.mark.usefixtures("mock_tts_cache_dir")
async def test_token_refresh_timeout_and_retry(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Keep credentials after a transient refresh failure and retry speech."""
    await setup_integration(hass, mock_config_entry_with_speech)
    expired_token = {**mock_config_entry_with_speech.data["token"], "expires_at": 0}
    hass.config_entries.async_update_entry(
        mock_config_entry_with_speech,
        data={**mock_config_entry_with_speech.data, "token": expired_token},
    )
    aioclient_mock.post(TOKEN_URL, exc=TimeoutError)
    media_source_id = tts.generate_media_source_id(
        hass, "Hello", "tts.grok_tts", "en", cache=False
    )

    with pytest.raises(HomeAssistantError) as err:
        await tts.async_get_media_source_audio(hass, media_source_id)

    assert err.value.translation_domain == DOMAIN
    assert err.value.translation_key == "api_error"
    assert mock_config_entry_with_speech.data["token"] == expired_token
    mock_spacexai_subscription_client.async_synthesize_speech.assert_not_awaited()
    await hass.async_block_till_done()
    assert hass.config_entries.flow.async_progress() == []

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        TOKEN_URL,
        json={
            "access_token": "new-access-token",
            "refresh_token": "new-refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )

    assert await tts.async_get_media_source_audio(hass, media_source_id) == (
        "mp3",
        b"speech",
    )
    assert mock_config_entry_with_speech.data["token"]["refresh_token"] == (
        "new-refresh-token"
    )
    mock_spacexai_subscription_client.async_synthesize_speech.assert_awaited_once_with(
        "new-access-token", text="Hello", voice_id="eve", language="en", speed=1.1
    )


async def test_media_browser_distinguishes_tts_subentries(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Show each speech engine's configured name in the media browser."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=mock_config_entry_with_speech.data,
        subentries_data=[
            ConfigSubentryData(
                data={},
                subentry_type="tts",
                title=name,
                unique_id=None,
            )
            for name in ("Grok Bedroom", "Grok Kitchen")
        ],
    )
    assert await async_setup_component(hass, "media_source", {})
    await setup_integration(hass, entry)

    item = await media_source.async_browse_media(hass, "media-source://tts")

    assert item.children is not None
    assert [(child.title, child.media_content_id) for child in item.children] == [
        ("Grok Bedroom", "media-source://tts/tts.grok_bedroom"),
        ("Grok Kitchen", "media-source://tts/tts.grok_kitchen"),
    ]
    mock_spacexai_subscription_client.async_synthesize_speech.assert_not_awaited()


@pytest.mark.usefixtures("mock_tts_cache_dir")
async def test_supported_voices_and_synthesis(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """List voices and synthesize MP3 speech through the TTS interfaces."""
    await setup_integration(hass, mock_config_entry_with_speech)
    state = hass.states.get("tts.grok_tts")
    assert state is not None
    assert state.attributes["friendly_name"] == "Grok TTS"
    client = await hass_ws_client()
    await client.send_json_auto_id(
        {
            "type": "tts/engine/voices",
            "engine_id": "tts.grok_tts",
            "language": "en",
        }
    )
    response = await client.receive_json()

    assert response["success"]
    assert [voice["voice_id"] for voice in response["result"]["voices"]] == [
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

    result = await tts.async_get_media_source_audio(
        hass,
        tts.generate_media_source_id(
            hass,
            "Welcome home",
            "tts.grok_tts",
            "en",
            options={tts.ATTR_VOICE: "leo"},
            cache=False,
        ),
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
            "engine_id": "tts.grok_tts",
            "message": "HTTP playback smoke",
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
        pytest.param(PermissionDeniedError, "not_entitled", id="permission_denied"),
        pytest.param(SpaceXAISubscriptionError, "api_error", id="api"),
    ],
)
@pytest.mark.usefixtures("mock_tts_cache_dir")
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
        await tts.async_get_media_source_audio(
            hass,
            tts.generate_media_source_id(
                hass, "Hello", "tts.grok_tts", "en", cache=False
            ),
        )

    assert err.value.translation_domain == "spacexai"
    assert err.value.translation_key == translation_key
