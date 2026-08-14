"""Tests for SpaceXAI speech platforms."""

from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components import stt, tts
from homeassistant.components.spacexai.const import DEFAULT_VOICE
from homeassistant.components.spacexai.errors import (
    ErrorContext,
    Operation,
    RateLimitedError,
    SubscriptionNotEntitledError,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import issue_registry as ir

from tests.common import MockConfigEntry

STT_ENTITY = "stt.grok_stt"
TTS_ENTITY = "tts.grok_tts"


async def _audio_chunks(*chunks: bytes) -> AsyncIterator[bytes]:
    """Yield audio chunks."""
    for chunk in chunks:
        yield chunk


def _metadata() -> stt.SpeechMetadata:
    """Return metadata for a supported audio stream."""
    return stt.SpeechMetadata(
        language="en-US",
        format=stt.AudioFormats.WAV,
        codec=stt.AudioCodecs.PCM,
        bit_rate=stt.AudioBitRates.BITRATE_16,
        sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
        channel=stt.AudioChannels.CHANNEL_MONO,
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_stt_success(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Transcribe audio through SpaceXAI STT."""
    assert hass.states.get(STT_ENTITY) is not None
    entity: stt.SpeechToTextEntity = hass.data[stt.DOMAIN].get_entity(STT_ENTITY)
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_transcribe",
        new_callable=AsyncMock,
        return_value="hello world",
    ) as mock_transcribe:
        result = await entity.async_process_audio_stream(
            stt.SpeechMetadata(
                language="en-US",
                format=stt.AudioFormats.WAV,
                codec=stt.AudioCodecs.PCM,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            ),
            _audio_chunks(b"\x00\x01" * 80),
        )
    assert result.result == stt.SpeechResultState.SUCCESS
    assert result.text == "hello world"
    mock_transcribe.assert_awaited_once()
    assert mock_transcribe.await_args.kwargs["language"] == "en"
    assert mock_transcribe.await_args.kwargs["content_type"] == "audio/wav"


@pytest.mark.usefixtures("setup_credentials")
async def test_stt_provider_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Return an STT error when the provider fails."""
    entity: stt.SpeechToTextEntity = hass.data[stt.DOMAIN].get_entity(STT_ENTITY)
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_transcribe",
        new_callable=AsyncMock,
        side_effect=RateLimitedError(
            "limited",
            context=ErrorContext(operation=Operation.STT),
        ),
    ):
        result = await entity.async_process_audio_stream(
            stt.SpeechMetadata(
                language="en-US",
                format=stt.AudioFormats.OGG,
                codec=stt.AudioCodecs.OPUS,
                bit_rate=stt.AudioBitRates.BITRATE_16,
                sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
                channel=stt.AudioChannels.CHANNEL_MONO,
            ),
            _audio_chunks(b"ogg"),
        )
    assert result.result == stt.SpeechResultState.ERROR


@pytest.mark.usefixtures("setup_credentials")
async def test_stt_speech_api_access_creates_repair(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Create a speech API repair when STT is rejected for this session."""
    entity: stt.SpeechToTextEntity = hass.data[stt.DOMAIN].get_entity(STT_ENTITY)
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_transcribe",
        new_callable=AsyncMock,
        side_effect=SubscriptionNotEntitledError(
            "speech denied",
            context=ErrorContext(operation=Operation.STT),
        ),
    ):
        result = await entity.async_process_audio_stream(
            _metadata(),
            _audio_chunks(b"\x00\x01" * 80),
        )
    assert result.result == stt.SpeechResultState.ERROR
    assert issue_registry.async_get_issue(
        "spacexai", f"speech_api_access_{setup_integration.entry_id}"
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_tts_success(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Synthesize speech through SpaceXAI TTS."""
    assert hass.states.get(TTS_ENTITY) is not None
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_synthesize_speech",
        new_callable=AsyncMock,
        return_value=b"ID3fake-mp3",
    ) as mock_tts:
        extension, data = await entity.async_get_tts_audio(
            "Hello from Grok",
            "en",
            options={tts.ATTR_VOICE: "eve", tts.ATTR_PREFERRED_FORMAT: "mp3"},
        )
    assert extension == "mp3"
    assert data == b"ID3fake-mp3"
    mock_tts.assert_awaited_once()
    assert mock_tts.await_args.kwargs["voice_id"] == "eve"
    assert mock_tts.await_args.kwargs["language"] == "en"


@pytest.mark.usefixtures("setup_credentials")
async def test_tts_provider_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Raise a translated error when TTS fails."""
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_synthesize_speech",
            new_callable=AsyncMock,
            side_effect=RateLimitedError(
                "limited",
                context=ErrorContext(operation=Operation.TTS, model="Grok TTS"),
            ),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await entity.async_get_tts_audio("Hello", "en", options={})
    assert raised.value.translation_key == "rate_limited"


@pytest.mark.usefixtures("setup_credentials")
async def test_stt_declared_audio_support(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Advertise the audio shapes the SpaceXAI STT endpoint accepts."""
    entity: stt.SpeechToTextEntity = hass.data[stt.DOMAIN].get_entity(STT_ENTITY)
    assert "en-US" in entity.supported_languages
    assert stt.AudioFormats.WAV in entity.supported_formats
    assert stt.AudioCodecs.PCM in entity.supported_codecs
    assert stt.AudioBitRates.BITRATE_16 in entity.supported_bit_rates
    assert stt.AudioSampleRates.SAMPLERATE_16000 in entity.supported_sample_rates
    assert stt.AudioChannels.CHANNEL_MONO in entity.supported_channels


@pytest.mark.usefixtures("setup_credentials")
async def test_stt_unexpected_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Report an unexpected transcription failure as an error result."""
    entity: stt.SpeechToTextEntity = hass.data[stt.DOMAIN].get_entity(STT_ENTITY)
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_transcribe",
        new_callable=AsyncMock,
        side_effect=RuntimeError("boom"),
    ):
        result = await entity.async_process_audio_stream(
            _metadata(), _audio_chunks(b"audio")
        )
    assert result.result is stt.SpeechResultState.ERROR


@pytest.mark.usefixtures("setup_credentials")
async def test_tts_voices_and_defaults(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Expose the configured default voice and the supported voice list."""
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    assert entity.default_options[tts.ATTR_VOICE] == DEFAULT_VOICE
    voices = entity.async_get_supported_voices("en")
    assert voices
    assert any(voice.voice_id == DEFAULT_VOICE for voice in voices)


@pytest.mark.usefixtures("setup_credentials")
async def test_tts_unsupported_format_falls_back_to_mp3(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Fall back to MP3 when Home Assistant asks for an unsupported codec."""
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_synthesize_speech",
        new_callable=AsyncMock,
        return_value=b"audio",
    ) as synthesize:
        extension, audio = await entity.async_get_tts_audio(
            "hello", "en", {tts.ATTR_PREFERRED_FORMAT: "flac"}
        )
    assert extension == "mp3"
    assert audio == b"audio"
    assert synthesize.call_args.kwargs["codec"] == "mp3"


@pytest.mark.usefixtures("setup_credentials")
async def test_tts_unexpected_error(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Translate an unexpected synthesis failure."""
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_synthesize_speech",
            new_callable=AsyncMock,
            side_effect=RuntimeError("boom"),
        ),
        pytest.raises(HomeAssistantError) as raised,
    ):
        await entity.async_get_tts_audio("hello", "en", {})
    assert raised.value.translation_key == "unexpected_provider_failure"


@pytest.mark.usefixtures("setup_credentials")
async def test_tts_empty_audio(
    hass: HomeAssistant,
    setup_integration: MockConfigEntry,
) -> None:
    """Reject an empty audio payload from the TTS endpoint."""
    entity = hass.data[tts.DOMAIN].get_entity(TTS_ENTITY)
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_synthesize_speech",
            new_callable=AsyncMock,
            return_value=b"",
        ),
        pytest.raises(HomeAssistantError),
    ):
        await entity.async_get_tts_audio("hello", "en", {})
