"""Speech-to-text support for SpaceXAI."""

from collections.abc import AsyncIterable
import io
from typing import override
import wave

from homeassistant.components import stt
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SpaceXAIConfigEntry
from .const import STT_LANGUAGES
from .entity import SpaceXAIBaseLLMEntity
from .errors import SpaceXAIError

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SpaceXAIConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpaceXAI STT entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "stt":
            continue
        async_add_entities(
            [SpaceXAISTTEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class SpaceXAISTTEntity(stt.SpeechToTextEntity, SpaceXAIBaseLLMEntity):
    """SpaceXAI speech-to-text entity."""

    _attr_translation_key = "stt"

    @property
    @override
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return list(STT_LANGUAGES)

    @property
    @override
    def supported_formats(self) -> list[stt.AudioFormats]:
        """Return a list of supported formats."""
        return [stt.AudioFormats.WAV, stt.AudioFormats.OGG]

    @property
    @override
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        """Return a list of supported codecs."""
        return [stt.AudioCodecs.PCM, stt.AudioCodecs.OPUS]

    @property
    @override
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        """Return a list of supported bit rates."""
        return [
            stt.AudioBitRates.BITRATE_8,
            stt.AudioBitRates.BITRATE_16,
            stt.AudioBitRates.BITRATE_24,
            stt.AudioBitRates.BITRATE_32,
        ]

    @property
    @override
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        """Return a list of supported sample rates."""
        return [
            stt.AudioSampleRates.SAMPLERATE_8000,
            stt.AudioSampleRates.SAMPLERATE_16000,
            stt.AudioSampleRates.SAMPLERATE_22000,
            stt.AudioSampleRates.SAMPLERATE_44100,
            stt.AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    @override
    def supported_channels(self) -> list[stt.AudioChannels]:
        """Return a list of supported channels."""
        return [stt.AudioChannels.CHANNEL_MONO, stt.AudioChannels.CHANNEL_STEREO]

    @override
    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Process an audio stream with SpaceXAI STT."""
        audio_bytes = bytearray()
        async for chunk in stream:
            audio_bytes.extend(chunk)
        audio_data = bytes(audio_bytes)
        content_type = "audio/ogg"
        filename = "audio.ogg"
        if metadata.format == stt.AudioFormats.WAV:
            # Dictation can be several megabytes, so keep the loop free.
            audio_data = await self.hass.async_add_executor_job(
                _wrap_pcm_in_wav, audio_data, metadata
            )
            content_type = "audio/wav"
            filename = "audio.wav"

        try:
            text = await self.entry.runtime_data.client.async_transcribe(
                audio=audio_data,
                filename=filename,
                content_type=content_type,
                language=metadata.language.split("-", maxsplit=1)[0],
            )
        except SpaceXAIError as err:
            self._handle_provider_error(err)
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
        except Exception:  # noqa: BLE001
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

        self._mark_available()
        return stt.SpeechResult(text, stt.SpeechResultState.SUCCESS)


def _wrap_pcm_in_wav(audio_data: bytes, metadata: stt.SpeechMetadata) -> bytes:
    """Wrap raw PCM frames in a WAV container."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(metadata.channel.value)
        wav_file.setsampwidth(metadata.bit_rate.value // 8)
        wav_file.setframerate(metadata.sample_rate.value)
        wav_file.writeframes(audio_data)
    return wav_buffer.getvalue()
