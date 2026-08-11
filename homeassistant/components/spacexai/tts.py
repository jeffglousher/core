"""Text-to-speech support for SpaceXAI."""

from collections.abc import Mapping
from typing import Any, override

from propcache.api import cached_property

from homeassistant.components.tts import (
    ATTR_PREFERRED_FORMAT,
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import SpaceXAIConfigEntry
from .const import (
    CONF_TTS_SPEED,
    CONF_VOICE,
    DEFAULT_TTS_SPEED,
    DEFAULT_VOICE,
    DOMAIN,
    TTS_LANGUAGES,
    TTS_VOICES,
)
from .entity import SpaceXAIBaseLLMEntity
from .errors import SpaceXAIError

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SpaceXAIConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpaceXAI TTS entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "tts":
            continue
        async_add_entities(
            [SpaceXAITTSEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class SpaceXAITTSEntity(TextToSpeechEntity, SpaceXAIBaseLLMEntity):
    """SpaceXAI text-to-speech entity."""

    _attr_supported_options = [ATTR_VOICE, ATTR_PREFERRED_FORMAT]
    _attr_supported_languages = list(TTS_LANGUAGES)
    _attr_default_language = "en"
    _attr_has_entity_name = False
    _attr_translation_key = "tts"
    _supported_voices = [Voice(voice_id, name) for voice_id, name in TTS_VOICES]
    _supported_formats = ("mp3", "wav", "pcm")

    def __init__(self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the entity."""
        super().__init__(entry, subentry)
        self._attr_name = subentry.title

    @callback
    @override
    def async_get_supported_voices(self, language: str) -> list[Voice]:
        """Return a list of supported voices for a language."""
        return self._supported_voices

    @cached_property
    @override
    def default_options(self) -> Mapping[str, Any]:
        """Return a mapping with the default options."""
        return {
            ATTR_VOICE: self.subentry.data.get(CONF_VOICE, DEFAULT_VOICE),
            ATTR_PREFERRED_FORMAT: "mp3",
        }

    @override
    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Load TTS audio from SpaceXAI."""
        merged = {**self.subentry.data, **options}
        response_format = merged.get(ATTR_PREFERRED_FORMAT, "mp3")
        if response_format not in self._supported_formats:
            response_format = "mp3"
        voice_id = merged.get(ATTR_VOICE, DEFAULT_VOICE)
        speed = float(merged.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED))

        try:
            audio = await self.entry.runtime_data.client.async_synthesize_speech(
                text=message,
                voice_id=voice_id,
                language=language,
                speed=speed,
                codec=response_format,
            )
        except SpaceXAIError as err:
            self._raise_provider_home_assistant_error(err)
        except Exception as err:  # noqa: BLE001
            self._raise_unexpected_provider_failure(err)

        self._mark_available()
        if not audio:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="malformed_provider_response",
                translation_placeholders={"model": "Grok TTS"},
            )
        return response_format, audio
