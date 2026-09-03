"""Text-to-speech support for SpaceXAI."""

from collections.abc import Mapping
from typing import Any, override

from propcache.api import cached_property
from spacexai_subscription_client import (
    AuthenticationError,
    InvalidResponseError,
    SpaceXAISubscriptionError,
)

from homeassistant.components.tts import (
    ATTR_VOICE,
    TextToSpeechEntity,
    TtsAudioType,
    Voice,
)
from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_TTS_SPEED, DOMAIN, RECOMMENDED_TTS_SPEED
from .entity import SpaceXAISpeechEntity
from .models import SpaceXAIConfigEntry

PARALLEL_UPDATES = 0

SUPPORTED_LANGUAGES = [
    "auto",
    "en",
    "ar-EG",
    "ar-SA",
    "ar-AE",
    "bn",
    "zh",
    "fr",
    "de",
    "hi",
    "id",
    "it",
    "ja",
    "ko",
    "pt-BR",
    "pt-PT",
    "ru",
    "es-MX",
    "es-ES",
    "tr",
    "vi",
]
SUPPORTED_VOICES = [
    Voice(voice, voice.title())
    for voice in (
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
    )
]


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SpaceXAIConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpaceXAI text-to-speech entities."""
    for subentry in config_entry.subentries.values():
        if subentry.subentry_type != "tts":
            continue
        async_add_entities(
            [SpaceXAITtsEntity(config_entry, subentry)],
            config_subentry_id=subentry.subentry_id,
        )


class SpaceXAITtsEntity(TextToSpeechEntity, SpaceXAISpeechEntity):
    """SpaceXAI text-to-speech entity."""

    _attr_default_language = "en"
    _attr_supported_languages = SUPPORTED_LANGUAGES
    _attr_supported_options = [ATTR_VOICE]
    _attr_translation_key = "spacexai_tts"

    def __init__(self, entry: SpaceXAIConfigEntry, subentry: ConfigSubentry) -> None:
        """Initialize the text-to-speech entity."""
        super().__init__(entry, subentry, "Text to Speech")

    @callback
    @override
    def async_get_supported_voices(self, language: str) -> list[Voice]:
        """Return supported voices."""
        return SUPPORTED_VOICES

    @cached_property
    @override
    def default_options(self) -> Mapping[str, Any]:
        """Return default text-to-speech options."""
        return {ATTR_VOICE: "eve"}

    @override
    async def async_get_tts_audio(
        self, message: str, language: str, options: dict[str, Any]
    ) -> TtsAudioType:
        """Generate speech audio."""
        try:
            audio = await self.entry.runtime_data.client.async_synthesize_speech(
                await self._async_access_token(),
                text=message,
                voice_id=options.get(ATTR_VOICE, "eve"),
                language=language,
                speed=self.subentry.data.get(CONF_TTS_SPEED, RECOMMENDED_TTS_SPEED),
            )
        except AuthenticationError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
            ) from err
        except InvalidResponseError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="invalid_response",
            ) from err
        except SpaceXAISubscriptionError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="api_error",
            ) from err

        return "mp3", audio
