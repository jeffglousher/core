"""Repairs flows for SpaceXAI."""

from typing import Any, cast

from homeassistant.components.repairs import RepairsFlow, RepairsFlowResult
from homeassistant.config_entries import ConfigEntryState, ConfigSubentry
from homeassistant.const import CONF_LLM_HASS_API, CONF_MODEL, CONF_PROMPT
from homeassistant.core import HomeAssistant

from . import (
    SpaceXAIConfigEntry,
    async_begin_catalog_refresh,
    async_capture_availability_epochs,
    async_mark_subscription_not_entitled,
    async_reconcile_snapshot,
)
from .client import ProviderSnapshot
from .config_flow import _llm_api_options, _repair_conversation_schema
from .const import CONF_MAX_OUTPUT_TOKENS, DOMAIN, ISSUE_MODEL_NOT_ENTITLED
from .errors import (
    AccountMismatchError,
    AuthenticationRejectedError,
    ConnectionFailureError,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    NoConversationModelsError,
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
    async_delete_model_not_entitled_issue,
    async_model_issue_is_response_originated,
)


class ModelNotEntitledRepairFlow(RepairsFlow):
    """Replace a withdrawn conversation model from a repair issue."""

    def __init__(self, entry: SpaceXAIConfigEntry, subentry_id: str) -> None:
        """Initialize the repair flow."""
        self.entry = entry
        self.subentry_id = subentry_id
        self._snapshot: ProviderSnapshot | None = None

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Handle the first step of a fix flow."""
        return await self.async_step_replace_model()

    async def async_step_replace_model(
        self, user_input: dict[str, Any] | None = None
    ) -> RepairsFlowResult:
        """Select a currently entitled replacement model."""
        if self.entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        subentry = self.entry.subentries.get(self.subentry_id)
        if subentry is None:
            return self.async_abort(reason="unknown")

        availability_epochs = async_capture_availability_epochs(self.hass, self.entry)
        subscription_epoch = self.entry.runtime_data.subscription_epoch
        catalog_epoch = async_begin_catalog_refresh(self.entry)
        try:
            self._snapshot = await self.entry.runtime_data.client.async_validate(
                expected_subject=self.entry.unique_id
            )
        except (
            AccountMismatchError,
            AuthenticationRejectedError,
            ReauthenticationRequiredError,
            RefreshRejectedError,
        ):
            if catalog_epoch == self.entry.runtime_data.catalog_epoch:
                self.entry.async_start_reauth(self.hass)
            return self.async_abort(reason="oauth_unauthorized")
        except SubscriptionNotEntitledError:
            if catalog_epoch == self.entry.runtime_data.catalog_epoch:
                async_mark_subscription_not_entitled(self.hass, self.entry)
            return self.async_abort(reason="subscription_not_entitled")
        except NoConversationModelsError:
            return self.async_abort(reason="no_conversation_models")
        except QuotaLimitedError:
            return self.async_abort(reason="quota_limited")
        except (
            ConnectionFailureError,
            RateLimitedError,
            RequestTimeoutError,
            TransientProviderError,
        ):
            return self.async_abort(reason="cannot_connect")
        except ModelNotEntitledError, MalformedProviderResponseError, SpaceXAIError:
            return self.async_abort(reason="unknown")

        assert self._snapshot is not None
        async_reconcile_snapshot(
            self.hass,
            self.entry,
            self._snapshot,
            availability_epochs=availability_epochs,
            subscription_epoch=subscription_epoch,
            catalog_epoch=catalog_epoch,
        )
        if catalog_epoch != self.entry.runtime_data.catalog_epoch:
            self._snapshot = self.entry.runtime_data.snapshot

        if user_input is not None and CONF_MODEL in user_input:
            selected = user_input[CONF_MODEL]
            if not any(
                selected in item.selectable_ids for item in self._snapshot.models
            ):
                return self.async_abort(reason="model_not_entitled")
            if selected == subentry.data[
                CONF_MODEL
            ] and async_model_issue_is_response_originated(
                self.hass, subentry.subentry_id
            ):
                return self._async_replace_model_form(
                    subentry, errors={"base": "model_not_entitled"}
                )
            new_data = {
                **dict(subentry.data),
                CONF_MODEL: user_input[CONF_MODEL],
                CONF_MAX_OUTPUT_TOKENS: user_input[CONF_MAX_OUTPUT_TOKENS],
            }
            if user_input.get(CONF_LLM_HASS_API):
                new_data[CONF_LLM_HASS_API] = user_input[CONF_LLM_HASS_API]
            else:
                new_data.pop(CONF_LLM_HASS_API, None)
            if user_input.get(CONF_PROMPT):
                new_data[CONF_PROMPT] = user_input[CONF_PROMPT]
            else:
                new_data.pop(CONF_PROMPT, None)
            self.hass.config_entries.async_update_subentry(
                self.entry,
                subentry,
                data=new_data,
            )
            async_delete_model_not_entitled_issue(self.hass, subentry.subentry_id)
            async_reconcile_snapshot(
                self.hass,
                self.entry,
                self._snapshot,
                availability_epochs=availability_epochs,
                subscription_epoch=subscription_epoch,
                catalog_epoch=catalog_epoch,
            )
            return self.async_create_entry(data={})

        if self._snapshot.has_model(cast(str, subentry.data[CONF_MODEL])):
            if async_model_issue_is_response_originated(
                self.hass, subentry.subentry_id
            ):
                return self._async_replace_model_form(subentry)
            return self.async_create_entry(data={})

        return self._async_replace_model_form(subentry)

    def _async_replace_model_form(
        self,
        subentry: ConfigSubentry,
        *,
        errors: dict[str, str] | None = None,
    ) -> RepairsFlowResult:
        """Show the replacement-model form for the current snapshot."""
        assert self._snapshot is not None
        return self.async_show_form(
            step_id="replace_model",
            data_schema=_repair_conversation_schema(
                self._snapshot,
                _llm_api_options(self.hass),
                dict(subentry.data),
            ),
            errors=errors,
            description_placeholders={"model": cast(str, subentry.data[CONF_MODEL])},
        )


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a repair flow for a SpaceXAI issue."""
    if data is None:
        raise ValueError("Repair data is required")
    if not issue_id.startswith(f"{ISSUE_MODEL_NOT_ENTITLED}_"):
        raise ValueError(f"Unknown repair issue: {issue_id}")
    entry_id = cast(str, data["entry_id"])
    subentry_id = cast(str, data["subentry_id"])
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is None or entry.domain != DOMAIN:
        raise ValueError(f"Config entry {entry_id} is not available")
    return ModelNotEntitledRepairFlow(cast(SpaceXAIConfigEntry, entry), subentry_id)
