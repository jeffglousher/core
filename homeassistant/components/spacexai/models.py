"""Data models for the SpaceXAI integration."""

from dataclasses import dataclass

from spacexai_subscription_client import SpaceXAISubscriptionClient

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session


@dataclass(slots=True)
class SpaceXAIData:
    """Runtime data for a SpaceXAI account."""

    oauth_session: OAuth2Session
    client: SpaceXAISubscriptionClient
    models: tuple[str, ...]


type SpaceXAIConfigEntry = ConfigEntry[SpaceXAIData]
