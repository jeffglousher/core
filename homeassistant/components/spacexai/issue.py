"""Repair issue helpers for the SpaceXAI integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN, ISSUE_MODEL_NOT_ENTITLED, ISSUE_SUBSCRIPTION_NOT_ENTITLED

MODEL_ISSUE_ORIGIN_CATALOG = "catalog"
MODEL_ISSUE_ORIGIN_RESPONSE = "response"


@callback
def async_create_model_not_entitled_issue(
    hass: HomeAssistant,
    entry: ConfigEntry,
    *,
    subentry_id: str,
    model: str,
    origin: str = MODEL_ISSUE_ORIGIN_CATALOG,
) -> None:
    """Create a fixable repair for a withdrawn conversation model."""
    issue_id = f"{ISSUE_MODEL_NOT_ENTITLED}_{subentry_id}"
    existing = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
    if (
        existing is not None
        and (existing.data or {}).get("origin") == MODEL_ISSUE_ORIGIN_RESPONSE
        and origin == MODEL_ISSUE_ORIGIN_CATALOG
    ):
        origin = MODEL_ISSUE_ORIGIN_RESPONSE
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key=ISSUE_MODEL_NOT_ENTITLED,
        translation_placeholders={"model": model},
        data={
            "entry_id": entry.entry_id,
            "subentry_id": subentry_id,
            "origin": origin,
        },
    )


@callback
def async_create_subscription_issue(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Create an account-scoped subscription entitlement repair."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"{ISSUE_SUBSCRIPTION_NOT_ENTITLED}_{entry.entry_id}",
        is_fixable=False,
        learn_more_url="https://console.x.ai/",
        severity=ir.IssueSeverity.ERROR,
        translation_key=ISSUE_SUBSCRIPTION_NOT_ENTITLED,
    )


@callback
def async_delete_model_not_entitled_issue(
    hass: HomeAssistant,
    subentry_id: str,
    *,
    catalog_only: bool = False,
) -> None:
    """Delete the model-not-entitled repair for a subentry if present."""
    issue_id = f"{ISSUE_MODEL_NOT_ENTITLED}_{subentry_id}"
    if catalog_only:
        issue = ir.async_get(hass).async_get_issue(DOMAIN, issue_id)
        if issue is None:
            return
        origin = (issue.data or {}).get("origin", MODEL_ISSUE_ORIGIN_CATALOG)
        if origin == MODEL_ISSUE_ORIGIN_RESPONSE:
            return
    ir.async_delete_issue(hass, DOMAIN, issue_id)


@callback
def async_delete_subscription_issue(hass: HomeAssistant, entry_id: str) -> None:
    """Delete the subscription-not-entitled repair for an entry if present."""
    ir.async_delete_issue(hass, DOMAIN, f"{ISSUE_SUBSCRIPTION_NOT_ENTITLED}_{entry_id}")


@callback
def async_model_issue_is_response_originated(
    hass: HomeAssistant, subentry_id: str
) -> bool:
    """Return whether the model repair came from a runtime inference denial."""
    issue = ir.async_get(hass).async_get_issue(
        DOMAIN, f"{ISSUE_MODEL_NOT_ENTITLED}_{subentry_id}"
    )
    if issue is None:
        return False
    return (issue.data or {}).get("origin") == MODEL_ISSUE_ORIGIN_RESPONSE
