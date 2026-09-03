"""Tests for SpaceXAI speech-to-text."""

from collections.abc import AsyncIterable
from unittest.mock import MagicMock, patch

from spacexai_subscription_client import AuthenticationError, SpaceXAISubscriptionError

from homeassistant.components import stt
from homeassistant.core import HomeAssistant

from . import setup_integration

from tests.common import MockConfigEntry


async def _audio_stream(*chunks: bytes) -> AsyncIterable[bytes]:
    """Yield audio chunks."""
    for chunk in chunks:
        yield chunk


def _metadata(
    audio_format: stt.AudioFormats, codec: stt.AudioCodecs
) -> stt.SpeechMetadata:
    """Return supported speech metadata."""
    return stt.SpeechMetadata(
        language="en-US",
        format=audio_format,
        codec=codec,
        bit_rate=stt.AudioBitRates.BITRATE_16,
        sample_rate=stt.AudioSampleRates.SAMPLERATE_16000,
        channel=stt.AudioChannels.CHANNEL_MONO,
    )


def _entity(hass: HomeAssistant) -> stt.SpeechToTextEntity:
    """Return the configured speech-to-text entity."""
    entity = hass.data[stt.DOMAIN].get_entity("stt.grok_speech_to_text")
    assert entity is not None
    return entity


async def test_properties_and_ogg_transcription(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Expose the provider contract and transcribe OGG audio."""
    await setup_integration(hass, mock_config_entry_with_speech)
    entity = _entity(hass)

    assert entity.supported_languages == [
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
    ]
    assert entity.supported_formats == [stt.AudioFormats.WAV, stt.AudioFormats.OGG]
    assert entity.supported_codecs == [stt.AudioCodecs.PCM, stt.AudioCodecs.OPUS]
    assert entity.supported_bit_rates == [stt.AudioBitRates.BITRATE_16]
    assert stt.AudioSampleRates.SAMPLERATE_16000 in entity.supported_sample_rates
    assert entity.supported_channels == [
        stt.AudioChannels.CHANNEL_MONO,
        stt.AudioChannels.CHANNEL_STEREO,
    ]

    result = await entity.async_process_audio_stream(
        _metadata(stt.AudioFormats.OGG, stt.AudioCodecs.OPUS),
        _audio_stream(b"one", b"two"),
    )

    assert result == stt.SpeechResult(
        "Turn on the kitchen light", stt.SpeechResultState.SUCCESS
    )
    mock_spacexai_subscription_client.async_transcribe.assert_awaited_once_with(
        "access-token",
        audio=b"onetwo",
        filename="speech.ogg",
        media_type="audio/ogg",
        language="en",
    )


async def test_wav_transcription_adds_header(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Wrap raw PCM in a WAV container before transcription."""
    await setup_integration(hass, mock_config_entry_with_speech)
    entity = _entity(hass)

    result = await entity.async_process_audio_stream(
        _metadata(stt.AudioFormats.WAV, stt.AudioCodecs.PCM),
        _audio_stream(b"raw-pcm"),
    )

    assert result.result is stt.SpeechResultState.SUCCESS
    audio = mock_spacexai_subscription_client.async_transcribe.await_args.kwargs[
        "audio"
    ]
    assert audio.startswith(b"RIFF")
    assert b"raw-pcm" in audio


async def test_transcription_error(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Return an error result for a client failure."""
    mock_spacexai_subscription_client.async_transcribe.side_effect = (
        SpaceXAISubscriptionError
    )
    await setup_integration(hass, mock_config_entry_with_speech)

    result = await _entity(hass).async_process_audio_stream(
        _metadata(stt.AudioFormats.OGG, stt.AudioCodecs.OPUS),
        _audio_stream(b"audio"),
    )

    assert result == stt.SpeechResult(None, stt.SpeechResultState.ERROR)


async def test_transcription_authentication_error_starts_reauth(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Start reauthentication when speech transcription rejects the token."""
    mock_spacexai_subscription_client.async_transcribe.side_effect = AuthenticationError
    await setup_integration(hass, mock_config_entry_with_speech)

    result = await _entity(hass).async_process_audio_stream(
        _metadata(stt.AudioFormats.OGG, stt.AudioCodecs.OPUS),
        _audio_stream(b"audio"),
    )

    assert result == stt.SpeechResult(None, stt.SpeechResultState.ERROR)
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == "reauth"
    assert flows[0]["step_id"] == "reauth_confirm"


async def test_transcription_rejects_empty_and_oversized_audio(
    hass: HomeAssistant,
    mock_config_entry_with_speech: MockConfigEntry,
    mock_spacexai_subscription_client: MagicMock,
) -> None:
    """Reject invalid audio before calling the service."""
    await setup_integration(hass, mock_config_entry_with_speech)
    entity = _entity(hass)

    empty = await entity.async_process_audio_stream(
        _metadata(stt.AudioFormats.OGG, stt.AudioCodecs.OPUS), _audio_stream()
    )
    with patch("homeassistant.components.spacexai.stt.MAX_STT_SIZE", 4):
        oversized = await entity.async_process_audio_stream(
            _metadata(stt.AudioFormats.OGG, stt.AudioCodecs.OPUS),
            _audio_stream(b"123", b"45"),
        )

    assert empty.result is stt.SpeechResultState.ERROR
    assert oversized.result is stt.SpeechResultState.ERROR
    mock_spacexai_subscription_client.async_transcribe.assert_not_awaited()
