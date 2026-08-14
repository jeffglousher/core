"""The SpaceXAI integration."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import cast

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigSubentry
from homeassistant.const import CONF_MODEL, CONF_PROMPT, Platform
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryError,
    ConfigEntryNotReady,
    HomeAssistantError,
    ServiceValidationError,
)
from homeassistant.helpers import (
    config_validation as cv,
    entity_platform,
    issue_registry as ir,
)
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
    LocalOAuth2Implementation,
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.helpers.json import json_dumps
from homeassistant.helpers.service import async_register_admin_service
from homeassistant.helpers.typing import ConfigType

from .client import (
    OAuthAccessTokenProvider,
    ProviderSnapshot,
    SpaceXAIClient,
    StaticAccessTokenProvider,
)
from .const import (
    CONF_DEFAULT_ASSIST,
    CONF_TTS_SPEED,
    CONF_VOICE,
    DEFAULT_MODEL_PLACEHOLDER,
    DEFAULT_STT_NAME,
    DEFAULT_TTS_NAME,
    DEFAULT_TTS_SPEED,
    DEFAULT_VIDEO_MODEL,
    DEFAULT_VOICE,
    DOMAIN,
    ISSUE_MODEL_NOT_ENTITLED,
    LOGGER,
    SERVICE_GENERATE_VIDEO,
)
from .errors import (
    AccountMismatchError,
    AuthenticationRejectedError,
    ConnectionFailureError,
    ErrorContext,
    ModelNotEntitledError,
    NoConversationModelsError,
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
from .issue import (
    async_create_model_not_entitled_issue,
    async_create_subscription_issue,
    async_delete_model_not_entitled_issue,
    async_delete_subscription_issue,
)

PLATFORMS = (Platform.AI_TASK, Platform.CONVERSATION, Platform.STT, Platform.TTS)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

SERVICE_GENERATE_VIDEO_SCHEMA = vol.Schema(
    {
        vol.Required("config_entry"): cv.string,
        vol.Required(CONF_PROMPT): cv.string,
        vol.Optional(CONF_MODEL, default=DEFAULT_VIDEO_MODEL): cv.string,
        vol.Optional("image_url"): cv.string,
        vol.Optional("duration"): vol.All(vol.Coerce(int), vol.Range(min=1, max=15)),
    }
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up SpaceXAI services."""

    async def async_generate_video(call: ServiceCall) -> ServiceResponse:
        """Generate a video with Imagine and return the provider URL."""
        entry_id = call.data["config_entry"]
        entry = hass.config_entries.async_get_entry(entry_id)
        if (
            entry is None
            or entry.domain != DOMAIN
            or not isinstance(entry.runtime_data, SpaceXAIData)
        ):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_config_entry",
                translation_placeholders={"config_entry": entry_id},
            )

        model = cast(str, call.data[CONF_MODEL])
        if not entry.runtime_data.snapshot.has_video_model(model):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="model_not_entitled",
                translation_placeholders={"model": model},
            )

        try:
            generated = await entry.runtime_data.client.async_generate_video(
                model=model,
                prompt=call.data[CONF_PROMPT],
                image_url=call.data.get("image_url"),
                duration=call.data.get("duration"),
            )
        except SpaceXAIError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key=err.category.value,
                translation_placeholders={"model": err.context.model or model},
            ) from err

        return {
            "url": generated.url,
            "model": generated.model,
        }

    async_register_admin_service(
        hass,
        DOMAIN,
        SERVICE_GENERATE_VIDEO,
        async_generate_video,
        schema=SERVICE_GENERATE_VIDEO_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
    return True


@dataclass(slots=True)
class SpaceXAIData:
    """Runtime data for one SpaceXAI account."""

    client: SpaceXAIClient
    snapshot: ProviderSnapshot
    subentries: tuple[tuple[str, str, str], ...]
    subscription_epoch: int = 0
    catalog_epoch: int = 0


type SpaceXAIConfigEntry = ConfigEntry[SpaceXAIData]


async def async_setup_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> bool:
    """Set up SpaceXAI from a config entry."""
    if _async_update_entry not in entry.update_listeners:
        entry.add_update_listener(_async_update_entry)
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
        snapshot = await client.async_validate(expected_subject=entry.unique_id)
        if snapshot.account.subject != entry.unique_id:
            raise AccountMismatchError(
                "Authenticated account does not match this config entry",
                context=ErrorContext(operation=Operation.ACCOUNT),
            )
    except AccountMismatchError as err:
        raise ConfigEntryAuthFailed(
            translation_domain=DOMAIN,
            translation_key="account_mismatch",
        ) from err
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
        async_create_subscription_issue(hass, entry)
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="subscription_not_entitled",
        ) from err
    except NoConversationModelsError as err:
        raise ConfigEntryError(
            translation_domain=DOMAIN,
            translation_key="no_conversation_models",
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

    entry.runtime_data = SpaceXAIData(
        client=client,
        snapshot=snapshot,
        subentries=_subentry_fingerprint(entry),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    async_clear_orphaned_model_repairs(hass, entry)
    async_reconcile_snapshot(hass, entry, snapshot)
    from .assist import async_setup_assist_pipeline  # noqa: PLC0415

    set_preferred = entry.data.get(CONF_DEFAULT_ASSIST) is True
    try:
        applied = await async_setup_assist_pipeline(
            hass,
            entry,
            set_preferred=set_preferred,
            create_if_missing=set_preferred,
        )
    except HomeAssistantError:
        LOGGER.exception("Unable to configure Assist pipeline for SpaceXAI")
    else:
        if set_preferred and applied:
            new_data = {
                key: value
                for key, value in entry.data.items()
                if key != CONF_DEFAULT_ASSIST
            }
            hass.config_entries.async_update_entry(entry, data=new_data)

    return True


async def async_migrate_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> bool:
    """Migrate older SpaceXAI config entries."""
    LOGGER.debug("Migrating from version %s:%s", entry.version, entry.minor_version)

    if entry.version > 1:
        return False

    if entry.version == 1 and entry.minor_version < 2:
        _ensure_speech_subentries(hass, entry)
        hass.config_entries.async_update_entry(entry, minor_version=2)

    LOGGER.debug(
        "Migration to version %s:%s successful", entry.version, entry.minor_version
    )
    return True


def _ensure_speech_subentries(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> None:
    """Add STT/TTS subentries when an older install omitted them."""
    existing = {subentry.subentry_type for subentry in entry.subentries.values()}
    if "stt" not in existing:
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType({}),
                subentry_type="stt",
                title=DEFAULT_STT_NAME,
                unique_id=None,
            ),
        )
    if "tts" not in existing:
        hass.config_entries.async_add_subentry(
            entry,
            ConfigSubentry(
                data=MappingProxyType(
                    {
                        CONF_VOICE: DEFAULT_VOICE,
                        CONF_TTS_SPEED: DEFAULT_TTS_SPEED,
                    }
                ),
                subentry_type="tts",
                title=DEFAULT_TTS_NAME,
                unique_id=None,
            ),
        )


async def async_unload_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> bool:
    """Unload a SpaceXAI config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> None:
    """Revoke the OAuth refresh token when an entry is removed."""
    async_delete_subscription_issue(hass, entry.entry_id)
    for subentry in entry.subentries.values():
        async_delete_model_not_entitled_issue(hass, subentry.subentry_id)
    async_clear_orphaned_model_repairs(hass, entry, include_current=True)

    token = entry.data.get("token")
    if not isinstance(token, dict) or not isinstance(
        refresh_token := token.get("refresh_token"), str
    ):
        LOGGER.warning(
            "Unable to revoke SpaceXAI OAuth token: reason=missing_refresh_token"
        )
        return

    try:
        implementation = await async_get_config_entry_implementation(hass, entry)
    except ImplementationUnavailableError, ValueError:
        LOGGER.warning(
            "Unable to revoke SpaceXAI OAuth token: reason=implementation_unavailable"
        )
        return
    if not isinstance(implementation, LocalOAuth2Implementation):
        LOGGER.warning(
            "Unable to revoke SpaceXAI OAuth token: reason=foreign_implementation"
        )
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


@callback
def async_begin_catalog_refresh(entry: SpaceXAIConfigEntry) -> int:
    """Advance the catalog generation for an in-flight snapshot refresh."""
    entry.runtime_data.catalog_epoch += 1
    return entry.runtime_data.catalog_epoch


@callback
def async_capture_availability_epochs(
    hass: HomeAssistant, entry: SpaceXAIConfigEntry
) -> dict[str, int]:
    """Capture entity availability generations before a catalog refresh."""
    epochs: dict[str, int] = {}
    for platform in entity_platform.async_get_platforms(hass, DOMAIN):
        for entity in platform.entities.values():
            if getattr(entity, "entry", None) is not entry:
                continue
            subentry = getattr(entity, "subentry", None)
            epoch = getattr(entity, "_availability_epoch", None)
            if subentry is None or not isinstance(epoch, int):
                continue
            epochs[subentry.subentry_id] = epoch
    return epochs


@callback
def async_mark_subscription_not_entitled(
    hass: HomeAssistant,
    entry: SpaceXAIConfigEntry,
    *,
    operation: Operation = Operation.MODELS,
) -> None:
    """Create the subscription repair and mark loaded conversation entities down."""
    entry.runtime_data.subscription_epoch += 1
    async_create_subscription_issue(hass, entry)
    err = SubscriptionNotEntitledError(
        "Account is not entitled for subscription-backed Grok access",
        context=ErrorContext(operation=operation),
    )
    for platform in entity_platform.async_get_platforms(hass, DOMAIN):
        for entity in platform.entities.values():
            if getattr(entity, "entry", None) is not entry:
                continue
            mark = getattr(entity, "_mark_unavailable", None)
            if mark is None:
                continue
            mark(err, account_wide=True)


@callback
def async_reconcile_snapshot(
    hass: HomeAssistant,
    entry: SpaceXAIConfigEntry,
    snapshot: ProviderSnapshot,
    *,
    availability_epochs: Mapping[str, int] | None = None,
    subscription_epoch: int | None = None,
    catalog_epoch: int | None = None,
) -> None:
    """Apply a fresh snapshot to repairs and loaded conversation entities."""
    if catalog_epoch is not None and catalog_epoch != entry.runtime_data.catalog_epoch:
        return
    entry.runtime_data.snapshot = snapshot
    if (
        subscription_epoch is None
        or subscription_epoch == entry.runtime_data.subscription_epoch
    ):
        async_delete_subscription_issue(hass, entry.entry_id)
    for subentry in entry.subentries.values():
        if CONF_MODEL not in subentry.data:
            continue
        model = cast(str, subentry.data[CONF_MODEL])
        if snapshot.has_model(model):
            if (
                availability_epochs is None
                or subentry.subentry_id not in availability_epochs
            ):
                async_delete_model_not_entitled_issue(
                    hass, subentry.subentry_id, catalog_only=True
                )
        else:
            async_create_model_not_entitled_issue(
                hass,
                entry,
                subentry_id=subentry.subentry_id,
                model=model,
            )

    for platform in entity_platform.async_get_platforms(hass, DOMAIN):
        for entity in platform.entities.values():
            apply = getattr(entity, "async_apply_model_entitlement", None)
            if apply is None or getattr(entity, "entry", None) is not entry:
                continue
            epoch: int | None = None
            entity_subentry = getattr(entity, "subentry", None)
            if availability_epochs is not None and entity_subentry is not None:
                epoch = availability_epochs.get(entity_subentry.subentry_id)
            apply(epoch)


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


@callback
def async_clear_orphaned_model_repairs(
    hass: HomeAssistant,
    entry: SpaceXAIConfigEntry,
    *,
    include_current: bool = False,
) -> None:
    """Delete model repairs whose subentry is no longer on this entry."""
    current_ids: set[str] = set() if include_current else set(entry.subentries)
    for issue in list(ir.async_get(hass).issues.values()):
        if issue.domain != DOMAIN or not issue.issue_id.startswith(
            f"{ISSUE_MODEL_NOT_ENTITLED}_"
        ):
            continue
        data = issue.data or {}
        if data.get("entry_id") != entry.entry_id:
            continue
        if data.get("subentry_id") in current_ids:
            continue
        ir.async_delete_issue(hass, DOMAIN, issue.issue_id)


async def _async_update_entry(hass: HomeAssistant, entry: SpaceXAIConfigEntry) -> None:
    """Clear removed-subentry repairs and reload when loaded config changes."""
    async_clear_orphaned_model_repairs(hass, entry)
    if entry.state is not ConfigEntryState.LOADED:
        return
    if _subentry_fingerprint(entry) == entry.runtime_data.subentries:
        return
    await hass.config_entries.async_reload(entry.entry_id)
