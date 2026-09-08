"""Tests for SpaceXAI speech-to-text."""

from collections.abc import AsyncIterable
from http import HTTPStatus
import io
from unittest.mock import MagicMock
import wave

import pytest
from spacexai_subscription_client import AuthenticationError, SpaceXAISubscriptionError
from spacexai_subscription_client.const import TOKEN_URL

from homeassistant.core import HomeAssistant

from . import setup_integration

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator

STT_URL = "/api/stt/stt.grok_speech_to_text"
OGG_HEADERS = {
    "X-Speech-Content": (
        "format=ogg; codec=opus; sample_rate=16000; bit_rate=16; channel=1; language=en"
    )
}


async def _audio_stream(*chunks: bytes) -> AsyncIterable[bytes]:
    """Yield audio chunks."""
    for chunk in chunks:
        yield chunk


async def test_token_refresh_timeout_and_retry(
    aioclient_mock: AiohttpClientMocker,
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Return a speech error on a refresh timeout and recover on the next request."""
    await setup_integration(hass, mock_config_entry_with_speech)
    expired_token = {**mock_config_entry_with_speech.data["token"], "expires_at": 0}
    hass.config_entries.async_update_entry(
        mock_config_entry_with_speech,
        data={**mock_config_entry_with_speech.data, "token": expired_token},
    )
    aioclient_mock.post(TOKEN_URL, exc=TimeoutError)
    client = await hass_client()

    response = await client.post(
        STT_URL, headers=OGG_HEADERS, data=_audio_stream(b"audio")
    )

    assert response.status == HTTPStatus.OK
    assert await response.json() == {"text": None, "result": "error"}
    assert mock_config_entry_with_speech.data["token"] == expired_token
    mock_spacexai_subscription_client.async_transcribe.assert_not_awaited()
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
    response = await client.post(
        STT_URL, headers=OGG_HEADERS, data=_audio_stream(b"audio")
    )

    assert response.status == HTTPStatus.OK
    assert await response.json() == {
        "text": "Turn on the kitchen light",
        "result": "success",
    }
    assert mock_config_entry_with_speech.data["token"]["refresh_token"] == (
        "new-refresh-token"
    )
    mock_spacexai_subscription_client.async_transcribe.assert_awaited_once_with(
        "new-access-token",
        audio=b"audio",
        filename="speech.ogg",
        media_type="audio/ogg",
        language="en",
    )


async def test_capabilities_and_ogg_transcription(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Expose supported audio metadata and transcribe an HTTP audio stream."""
    await setup_integration(hass, mock_config_entry_with_speech)
    client = await hass_client()

    response = await client.get(STT_URL)
    assert response.status == HTTPStatus.OK
    assert await response.json() == {
        "languages": [
            "ar",
            "cs",
            "da",
            "de",
            "en",
            "es",
            "fa",
            "fil",
            "fr",
            "hi",
            "id",
            "it",
            "ja",
            "ko",
            "mk",
            "ms",
            "nl",
            "pl",
            "pt",
            "ro",
            "ru",
            "sv",
            "th",
            "tr",
            "vi",
        ],
        "formats": ["wav", "ogg"],
        "codecs": ["pcm", "opus"],
        "sample_rates": [8000, 16000, 44100, 48000],
        "bit_rates": [16],
        "channels": [1, 2],
    }

    response = await client.post(
        STT_URL, headers=OGG_HEADERS, data=_audio_stream(b"one", b"two")
    )

    assert response.status == HTTPStatus.OK
    assert await response.json() == {
        "text": "Turn on the kitchen light",
        "result": "success",
    }
    mock_spacexai_subscription_client.async_transcribe.assert_awaited_once_with(
        "access-token",
        audio=b"onetwo",
        filename="speech.ogg",
        media_type="audio/ogg",
        language="en",
    )


async def test_wav_transcription_adds_header(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Wrap raw PCM in a WAV container before transcription."""
    await setup_integration(hass, mock_config_entry_with_speech)
    client = await hass_client()

    response = await client.post(
        STT_URL,
        headers={
            "X-Speech-Content": (
                "format=wav; codec=pcm; sample_rate=16000; bit_rate=16;"
                " channel=1; language=en"
            )
        },
        data=_audio_stream(b"\x00\x01", b"\x02\x03"),
    )

    assert response.status == HTTPStatus.OK
    assert await response.json() == {
        "text": "Turn on the kitchen light",
        "result": "success",
    }
    audio = mock_spacexai_subscription_client.async_transcribe.await_args.kwargs[
        "audio"
    ]
    with wave.open(io.BytesIO(audio), "rb") as wav_file:
        assert wav_file.getnchannels() == 1
        assert wav_file.getsampwidth() == 2
        assert wav_file.getframerate() == 16000
        assert wav_file.getnframes() == 2
        assert wav_file.readframes(2) == b"\x00\x01\x02\x03"
    mock_spacexai_subscription_client.async_transcribe.assert_awaited_once_with(
        "access-token",
        audio=audio,
        filename="speech.wav",
        media_type="audio/wav",
        language="en",
    )


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(SpaceXAISubscriptionError, id="provider_error"),
        pytest.param(AuthenticationError, id="authentication_error"),
    ],
)
async def test_transcription_error(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    error: type[SpaceXAISubscriptionError],
) -> None:
    """Return an error result for a client failure."""
    mock_spacexai_subscription_client.async_transcribe.side_effect = error
    await setup_integration(hass, mock_config_entry_with_speech)
    client = await hass_client()

    response = await client.post(
        STT_URL, headers=OGG_HEADERS, data=_audio_stream(b"audio")
    )

    assert response.status == HTTPStatus.OK
    assert await response.json() == {"text": None, "result": "error"}


@pytest.mark.parametrize(
    "audio_size",
    [
        pytest.param(0, id="empty"),
        pytest.param(25 * 1024 * 1024 + 1, id="oversized"),
    ],
)
async def test_transcription_rejects_empty_and_oversized_audio(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
    audio_size: int,
) -> None:
    """Reject invalid audio before calling the service."""
    await setup_integration(hass, mock_config_entry_with_speech)
    client = await hass_client()

    response = await client.post(
        STT_URL, headers=OGG_HEADERS, data=_audio_stream(b"x" * audio_size)
    )

    assert response.status == HTTPStatus.OK
    assert await response.json() == {"text": None, "result": "error"}
    mock_spacexai_subscription_client.async_transcribe.assert_not_awaited()
