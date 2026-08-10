"""The SpaceXAI integration."""

from dataclasses import dataclass
from typing import cast

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MODEL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
    LocalOAuth2Implementation,
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.json import json_dumps

from .client import (
    OAuthAccessTokenProvider,
    ProviderSnapshot,
    SpaceXAIClient,
    StaticAccessTokenProvider,
)
from .const import CONF_DEFAULT_ASSIST, DEFAULT_MODEL_PLACEHOLDER, DOMAIN, LOGGER
from .errors import (
    AccountMismatchError,
    AuthenticationRejectedError,
    ConnectionFailureError,
    ErrorContext,
    ModelNotEntitledError,
    Operation,
    PermanentProviderError,
    QuotaLimitedError,
    RateLimitedError,
    ReauthenticationRequiredError,
    RefreshRejectedError,
    RequestTimeoutError,
    SpaceXAIError,
    SubscriptionNotEntitledError,
    TransientProviderError,
)

PLATFORMS = (Platform.AI_TASK, Platform.CONVERSATION, Platform.STT, Platform.TTS)
ISSUE_SUBSCRIPTION_NOT_ENTITLED = "subscription_not_entitled"
ISSUE_MODEL_NOT_ENTITLED = "model_not_entitled"


@dataclass(slots=True)
class SpaceXAIData:
    """Runtime data for one SpaceXAI account."""

    client: SpaceXAIClient
    snapshot: ProviderSnapshot
    subentries: tuple[tuple[str, str, str], ...]


type SpaceXAIConfigEntry = ConfigEntry[SpaceXAIData]


async def async_setup_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> bool:
    """Set up SpaceXAI from a config entry."""
    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except (ImplementationUnavailableError, ValueError) as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="oauth_implementation_unavailable",
        ) from err

    client = SpaceXAIClient(
        hass,
        OAuthAccessTokenProvider(OAuth2Session(hass, entry, implementation)),
        runtime_session=True,
    )
    try:
        snapshot = await client.async_validate()
    except (
        AuthenticationRejectedError,
        ReauthenticationRequiredError,
        RefreshRejectedError,
    ) as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="reauthentication_required",
        ) from err
    except (
        ConnectionFailureError,
        RateLimitedError,
        RequestTimeoutError,
        TransientProviderError,
    ) as err:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="provider_unavailable",
        ) from err
    except SubscriptionNotEntitledError as err:
        ir.async_create_issue(
            hass,
            DOMAIN,
            _subscription_issue_id(entry),
            is_fixable=False,
            learn_more_url="https://console.x.ai/",
            severity=ir.IssueSeverity.ERROR,
            translation_key=ISSUE_SUBSCRIPTION_NOT_ENTITLED,
        )
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="subscription_not_entitled",
        ) from err
    except QuotaLimitedError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="quota_limited",
            translation_placeholders={"model": DEFAULT_MODEL_PLACEHOLDER},
        ) from err
    except ModelNotEntitledError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="model_not_entitled",
            translation_placeholders={
                "model": err.context.model or DEFAULT_MODEL_PLACEHOLDER
            },
        ) from err
    except PermanentProviderError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="permanent_provider_failure",
            translation_placeholders={
                "model": err.context.model or DEFAULT_MODEL_PLACEHOLDER
            },
        ) from err
    except SpaceXAIError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="malformed_provider_response",
            translation_placeholders={"model": DEFAULT_MODEL_PLACEHOLDER},
        ) from err

    if entry.unique_id != snapshot.account.subject:
        error = AccountMismatchError(
            "OAuth account does not match the config entry",
            context=ErrorContext(operation=Operation.ACCOUNT),
        )
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="account_mismatch",
        ) from error

    for subentry in entry.subentries.values():
        if CONF_MODEL not in subentry.data:
            continue
        model = cast(str, subentry.data[CONF_MODEL])
        issue_id = f"{ISSUE_MODEL_NOT_ENTITLED}_{subentry.subentry_id}"
        if snapshot.has_model(model):
            ir.async_delete_issue(hass, DOMAIN, issue_id)
        else:
            ir.async_create_issue(
                hass,
                DOMAIN,
                issue_id,
                is_fixable=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=ISSUE_MODEL_NOT_ENTITLED,
                translation_placeholders={"model": model},
            )

    entry.runtime_data = SpaceXAIData(
        client=client,
        snapshot=snapshot,
        subentries=_subentry_fingerprint(entry),
    )
    entry.async_on_unload(entry.add_update_listener(_async_update_entry))
    ir.async_delete_issue(hass, DOMAIN, _subscription_issue_id(entry))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Install-time Assist wiring only. Clearing the flag after success means reloads
    # keep re-forcing the preferred Assist pipeline.
    if entry.data.get(CONF_DEFAULT_ASSIST) is True:
        from .assist import async_setup_assist_pipeline  # noqa: PLC0415

        try:
            applied = await async_setup_assist_pipeline(hass, entry, set_preferred=True)
        except HomeAssistantError:
            LOGGER.exception("Unable to configure Assist pipeline for SpaceXAI")
        else:
            if applied:
                new_data = {
                    key: value
                    for key, value in entry.data.items()
                    if key != CONF_DEFAULT_ASSIST
                }
                hass.config_entries.async_update_entry(entry, data=new_data)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> bool:
    """Unload a SpaceXAI config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> None:
    """Revoke the OAuth refresh token when an entry is removed."""
    ir.async_delete_issue(hass, DOMAIN, _subscription_issue_id(entry))
    for subentry in entry.subentries.values():
        ir.async_delete_issue(
            hass,
            DOMAIN,
            f"{ISSUE_MODEL_NOT_ENTITLED}_{subentry.subentry_id}",
        )

    token = entry.data.get("token")
    if not isinstance(token, dict) or not isinstance(
        refresh_token := token.get("refresh_token"), str
    ):
        return

    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError, ValueError:
        return
    if not isinstance(implementation, LocalOAuth2Implementation):
        return

    client = SpaceXAIClient(
        hass,
        StaticAccessTokenProvider(""),
        runtime_session=False,
    )
    try:
        await client.async_revoke(
            refresh_token,
            implementation.client_id,
            implementation.client_secret,
        )
    except SpaceXAIError as err:
        LOGGER.warning(
            "Unable to revoke SpaceXAI OAuth token: category=%s operation=%s "
            "status=%s request_id=%s retryable=%s",
            err.category,
            err.context.operation,
            err.context.status,
            err.context.request_id,
            err.retryable,
        )


def _subscription_issue_id(entry: SpaceXAIConfigEntry) -> str:
    """Return an account-specific subscription repair ID."""
    return f"{ISSUE_SUBSCRIPTION_NOT_ENTITLED}_{entry.entry_id}"


def _subentry_fingerprint(
    entry: SpaceXAIConfigEntry,
) -> tuple[tuple[str, str, str], ...]:
    """Return the stored subentry configuration fingerprint."""
    return tuple(
        sorted(
            (
                subentry.subentry_id,
                subentry.title,
                json_dumps(dict(subentry.data)),
            )
            for subentry in entry.subentries.values()
        )
    )


async def _async_update_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> None:
    """Reload only when subentry configuration changes."""
    if _subentry_fingerprint(entry) == entry.runtime_data.subentries:
        return
    await hass.config_entries.async_reload(entry.entry_id)
