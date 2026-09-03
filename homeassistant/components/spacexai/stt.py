"""Speech-to-text support for SpaceXAI."""

from collections.abc import AsyncIterable
import io
from typing import override
import wave

from spacexai_subscription_client import SpaceXAISubscriptionError

from homeassistant.components import stt
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SpaceXAIConfigEntry
from .const import LOGGER
from .entity import SpaceXAISpeechEntity

PARALLEL_UPDATES = 0
MAX_STT_SIZE = 25 * 1024 * 1024

SUPPORTED_LANGUAGES = [
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


def _add_wav_header(audio: bytes, metadata: stt.SpeechMetadata) -> bytes:
    """Add a WAV header to raw PCM audio."""
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(metadata.channel.value)
        wav_file.setsampwidth(metadata.bit_rate.value // 8)
        wav_file.setframerate(metadata.sample_rate.value)
        wav_file.writeframes(audio)
    return wav_buffer.getvalue()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SpaceXAIConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpaceXAI speech-to-text entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "stt":
            continue
        async_add_entities(
            [SpaceXAISttEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class SpaceXAISttEntity(stt.SpeechToTextEntity, SpaceXAISpeechEntity):
    """SpaceXAI speech-to-text entity."""

    _attr_name = None

    def __init__(self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the speech-to-text entity."""
        super().__init__(entry, subentry, "Speech to Text")

    @property
    @override
    def supported_languages(self) -> list[str]:
        """Return supported languages."""
        return SUPPORTED_LANGUAGES

    @property
    @override
    def supported_formats(self) -> list[stt.AudioFormats]:
        """Return supported audio formats."""
        return [stt.AudioFormats.WAV, stt.AudioFormats.OGG]

    @property
    @override
    def supported_codecs(self) -> list[stt.AudioCodecs]:
        """Return supported audio codecs."""
        return [stt.AudioCodecs.PCM, stt.AudioCodecs.OPUS]

    @property
    @override
    def supported_bit_rates(self) -> list[stt.AudioBitRates]:
        """Return supported audio bit rates."""
        return [stt.AudioBitRates.BITRATE_16]

    @property
    @override
    def supported_sample_rates(self) -> list[stt.AudioSampleRates]:
        """Return supported audio sample rates."""
        return [
            stt.AudioSampleRates.SAMPLERATE_8000,
            stt.AudioSampleRates.SAMPLERATE_16000,
            stt.AudioSampleRates.SAMPLERATE_44100,
            stt.AudioSampleRates.SAMPLERATE_48000,
        ]

    @property
    @override
    def supported_channels(self) -> list[stt.AudioChannels]:
        """Return supported channel counts."""
        return [stt.AudioChannels.CHANNEL_MONO, stt.AudioChannels.CHANNEL_STEREO]

    @override
    async def async_process_audio_stream(
        self, metadata: stt.SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> stt.SpeechResult:
        """Transcribe an audio stream."""
        audio = bytearray()
        async for chunk in stream:
            if len(audio) + len(chunk) > MAX_STT_SIZE:
                LOGGER.error("Speech-to-text audio exceeds the 25 MiB limit")
                return stt.SpeechResult(None, stt.SpeechResultState.ERROR)
            audio.extend(chunk)

        if not audio:
            LOGGER.error("Speech-to-text audio is empty")
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

        audio_data = bytes(audio)
        if metadata.format is stt.AudioFormats.WAV:
            audio_data = await self.hass.async_add_executor_job(
                _add_wav_header, audio_data, metadata
            )

        try:
            text = await self.entry.runtime_data.client.async_transcribe(
                await self._async_access_token(),
                audio=audio_data,
                filename=f"speech.{metadata.format.value}",
                media_type=f"audio/{metadata.format.value}",
                language=metadata.language.split("-", 1)[0],
            )
        except (HomeAssistantError, SpaceXAISubscriptionError) as err:
            LOGGER.error("Error during speech-to-text processing: %s", err)
            return stt.SpeechResult(None, stt.SpeechResultState.ERROR)

        return stt.SpeechResult(text, stt.SpeechResultState.SUCCESS)
