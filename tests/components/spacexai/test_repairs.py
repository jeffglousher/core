"""Tests for SpaceXAI repair flows."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.components.spacexai import async_begin_catalog_refresh
from homeassistant.components.spacexai.client import (
    AccountInfo,
    ModelInfo,
    ProviderSnapshot,
)
from homeassistant.components.spacexai.const import (
    CONF_MAX_OUTPUT_TOKENS,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL,
    DOMAIN,
)
from homeassistant.components.spacexai.errors import (
    AccountMismatchError,
    AuthenticationRejectedError,
    ConnectionFailureError,
    ErrorContext,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    NoConversationModelsError,
    Operation,
    QuotaLimitedError,
    RateLimitedError,
    ReauthenticationRequiredError,
    RefreshRejectedError,
    RequestTimeoutError,
    SubscriptionNotEntitledError,
    TransientProviderError,
)
from homeassistant.components.spacexai.issue import MODEL_ISSUE_ORIGIN_RESPONSE
from homeassistant.components.spacexai.repairs import async_create_fix_flow
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    CONF_LLM_HASS_API,
    CONF_MODEL,
    CONF_PROMPT,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir, llm
from homeassistant.setup import async_setup_component

from . import AGENT_ID, conversation_subentry, converse
from .conftest import ACCOUNT_ID

from tests.common import MockConfigEntry
from tests.components.repairs import process_repair_fix_flow, start_repair_fix_flow
from tests.typing import ClientSessionGenerator


@pytest.mark.usefixtures("setup_credentials")
async def test_model_not_entitled_repair_replaces_model(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Replace a withdrawn model through the fixable repair flow."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    subentry = conversation_subentry(mock_config_entry)
    issue_id = f"model_not_entitled_{subentry.subentry_id}"
    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.is_fixable is True
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "replace_model"

    result = await process_repair_fix_flow(
        client,
        result["flow_id"],
        json={
            CONF_MODEL: "grok-other",
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
            CONF_PROMPT: "Be terse",
            CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    updated = conversation_subentry(mock_config_entry)
    assert updated.data[CONF_MODEL] == "grok-other"
    assert updated.data[CONF_PROMPT] == "Be terse"
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE


@pytest.mark.usefixtures("setup_credentials")
async def test_model_not_entitled_repair_clears_optional_fields(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Drop prompt/API selections omitted from the repair submission."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    subentry = conversation_subentry(mock_config_entry)
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={
            **subentry.data,
            CONF_PROMPT: "Old prompt",
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
        },
    )
    issue_id = f"model_not_entitled_{subentry.subentry_id}"
    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.FORM

    result = await process_repair_fix_flow(
        client,
        result["flow_id"],
        json={
            CONF_MODEL: "grok-other",
            CONF_LLM_HASS_API: [],
            CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
        },
    )
    assert result["type"] == FlowResultType.CREATE_ENTRY
    updated = conversation_subentry(mock_config_entry)
    assert updated.data[CONF_MODEL] == "grok-other"
    assert CONF_PROMPT not in updated.data
    assert CONF_LLM_HASS_API not in updated.data


@pytest.mark.usefixtures("setup_credentials")
async def test_model_not_entitled_repair_rejects_withdrawn_selection(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Abort when the submitted replacement disappears before save."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    subentry = conversation_subentry(mock_config_entry)
    issue_id = f"model_not_entitled_{subentry.subentry_id}"

    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.FORM

    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-fresh", "xai"),),
    )
    result = await process_repair_fix_flow(
        client,
        result["flow_id"],
        json={
            CONF_MODEL: "grok-other",
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
            CONF_PROMPT: "Be terse",
            CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
        },
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "model_not_entitled"
    assert conversation_subentry(mock_config_entry).data[CONF_MODEL] == DEFAULT_MODEL


@pytest.mark.usefixtures("setup_credentials")
async def test_model_not_entitled_repair_clears_when_catalog_restores_model(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
    provider_snapshot: ProviderSnapshot,
) -> None:
    """Finish the repair without edits when the original model returns."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    subentry = conversation_subentry(mock_config_entry)
    issue_id = f"model_not_entitled_{subentry.subentry_id}"
    assert issue_registry.async_get_issue(DOMAIN, issue_id)

    mock_validate.return_value = provider_snapshot
    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)


@pytest.mark.usefixtures("setup_credentials")
async def test_response_model_repair_stays_open_when_catalog_lists_model(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    mock_stream: AsyncMock,
    issue_registry: ir.IssueRegistry,
    provider_snapshot: ProviderSnapshot,
) -> None:
    """Keep a runtime model denial repair open until a different model is saved."""
    mock_validate.return_value = provider_snapshot
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    subentry = conversation_subentry(mock_config_entry)
    issue_id = f"model_not_entitled_{subentry.subentry_id}"
    mock_stream.side_effect = ModelNotEntitledError(
        "gone",
        context=ErrorContext(operation=Operation.RESPONSE, model=DEFAULT_MODEL),
    )
    await converse(hass, "Hello")
    issue = issue_registry.async_get_issue(DOMAIN, issue_id)
    assert issue is not None
    assert issue.data["origin"] == MODEL_ISSUE_ORIGIN_RESPONSE

    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "replace_model"
    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE

    result = await process_repair_fix_flow(
        client,
        result["flow_id"],
        json={
            CONF_MODEL: DEFAULT_MODEL,
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
            CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
        },
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "model_not_entitled"}
    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("setup_credentials")
@pytest.mark.parametrize(
    ("error", "reason", "starts_reauth", "creates_subscription_issue"),
    [
        pytest.param(
            ReauthenticationRequiredError(
                "reauth",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            True,
            False,
            id="reauth",
        ),
        pytest.param(
            AuthenticationRejectedError(
                "auth",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            True,
            False,
            id="auth-rejected",
        ),
        pytest.param(
            RefreshRejectedError(
                "refresh",
                context=ErrorContext(operation=Operation.REFRESH),
            ),
            "oauth_unauthorized",
            True,
            False,
            id="refresh-rejected",
        ),
        pytest.param(
            AccountMismatchError(
                "mismatch",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            True,
            False,
            id="account-mismatch",
        ),
        pytest.param(
            SubscriptionNotEntitledError(
                "sub",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "subscription_not_entitled",
            False,
            True,
            id="subscription",
        ),
        pytest.param(
            NoConversationModelsError(
                "none",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "no_conversation_models",
            False,
            False,
            id="no-models",
        ),
        pytest.param(
            QuotaLimitedError(
                "quota",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "quota_limited",
            False,
            False,
            id="quota",
        ),
        pytest.param(
            ConnectionFailureError(
                "offline",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "cannot_connect",
            False,
            False,
            id="cannot-connect",
        ),
        pytest.param(
            RateLimitedError(
                "limited",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "cannot_connect",
            False,
            False,
            id="rate-limited",
        ),
        pytest.param(
            RequestTimeoutError(
                "timeout",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "cannot_connect",
            False,
            False,
            id="timeout",
        ),
        pytest.param(
            TransientProviderError(
                "transient",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "cannot_connect",
            False,
            False,
            id="transient",
        ),
        pytest.param(
            MalformedProviderResponseError(
                "bad",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "unknown",
            False,
            False,
            id="malformed",
        ),
        pytest.param(
            ModelNotEntitledError(
                "model",
                context=ErrorContext(operation=Operation.MODELS, model="grok-old"),
            ),
            "unknown",
            False,
            False,
            id="model-not-entitled",
        ),
    ],
)
async def test_model_not_entitled_repair_aborts_on_catalog_failure(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
    error: Exception,
    reason: str,
    starts_reauth: bool,
    creates_subscription_issue: bool,
) -> None:
    """Abort the repair flow with the classified catalog-refresh reason."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    issue_id = (
        f"model_not_entitled_{conversation_subentry(mock_config_entry).subentry_id}"
    )
    assert issue_registry.async_get_issue(DOMAIN, issue_id)

    mock_validate.side_effect = error
    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    with patch.object(mock_config_entry, "async_start_reauth") as start_reauth:
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == reason
    assert start_reauth.called is starts_reauth
    subscription_issue = f"subscription_not_entitled_{mock_config_entry.entry_id}"
    assert (
        issue_registry.async_get_issue(DOMAIN, subscription_issue) is not None
    ) is creates_subscription_issue
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("setup_credentials")
@pytest.mark.parametrize(
    ("error", "reason"),
    [
        pytest.param(
            ReauthenticationRequiredError(
                "reauth",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            id="reauth",
        ),
        pytest.param(
            SubscriptionNotEntitledError(
                "sub",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "subscription_not_entitled",
            id="subscription",
        ),
    ],
)
async def test_model_not_entitled_repair_ignores_stale_catalog_side_effects(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
    error: Exception,
    reason: str,
) -> None:
    """A superseded catalog refresh must not start reauth or create a subscription issue."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    issue_id = (
        f"model_not_entitled_{conversation_subentry(mock_config_entry).subentry_id}"
    )
    assert issue_registry.async_get_issue(DOMAIN, issue_id)

    async def _fail(*_args: object, **_kwargs: object) -> ProviderSnapshot:
        async_begin_catalog_refresh(mock_config_entry)
        raise error

    mock_validate.side_effect = _fail
    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    with patch.object(mock_config_entry, "async_start_reauth") as start_reauth:
        result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == reason
    start_reauth.assert_not_called()
    assert (
        issue_registry.async_get_issue(
            DOMAIN, f"subscription_not_entitled_{mock_config_entry.entry_id}"
        )
        is None
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_model_not_entitled_repair_requires_loaded_entry(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Abort repairs when the SpaceXAI entry is no longer loaded."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    subentry = conversation_subentry(mock_config_entry)
    issue_id = f"model_not_entitled_{subentry.subentry_id}"
    assert issue_registry.async_get_issue(DOMAIN, issue_id)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED
    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "entry_not_loaded"


@pytest.mark.usefixtures(
    "setup_credentials", "mock_validate", "provider_snapshot", "issue_registry"
)
async def test_model_not_entitled_repair_unknown_subentry(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Abort when the repair points at a removed conversation subentry."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    issue_id = "model_not_entitled_missing-subentry"
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=True,
        severity=ir.IssueSeverity.ERROR,
        translation_key="model_not_entitled",
        translation_placeholders={"model": "grok-old"},
        data={
            "entry_id": mock_config_entry.entry_id,
            "subentry_id": "missing-subentry",
        },
    )
    assert await async_setup_component(hass, "repairs", {})
    client = await hass_client()
    result = await start_repair_fix_flow(client, DOMAIN, issue_id)
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "unknown"


@pytest.mark.usefixtures("setup_credentials")
async def test_create_fix_flow_validates_issue_payload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reject repair flow creation without usable issue data."""
    with pytest.raises(ValueError, match="Repair data is required"):
        await async_create_fix_flow(hass, "model_not_entitled_x", None)
    with pytest.raises(ValueError, match="Unknown repair issue"):
        await async_create_fix_flow(
            hass,
            "subscription_not_entitled_x",
            {"entry_id": mock_config_entry.entry_id, "subentry_id": "sub"},
        )
    with pytest.raises(ValueError, match="not available"):
        await async_create_fix_flow(
            hass,
            "model_not_entitled_x",
            {"entry_id": "missing-entry", "subentry_id": "sub"},
        )
