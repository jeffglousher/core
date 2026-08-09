"""Tests for SpaceXAI setup and lifecycle."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from homeassistant.components.spacexai import async_remove_entry
from homeassistant.components.spacexai.client import (
    AccountInfo,
    ModelInfo,
    ProviderSnapshot,
)
from homeassistant.components.spacexai.errors import (
    AuthenticationRejectedError,
    ConnectionFailureError,
    ErrorContext,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    Operation,
    PermanentProviderError,
    QuotaLimitedError,
    RateLimitedError,
    ReauthenticationRequiredError,
    RefreshRejectedError,
    RequestTimeoutError,
    SubscriptionNotEntitledError,
    TransientProviderError,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from .conftest import ACCOUNT_ID

from tests.common import MockConfigEntry


@pytest.mark.usefixtures("setup_credentials")
async def test_setup_and_unload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Set up and unload Conversation and AI Task platforms."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get("conversation.grok") is not None
    assert hass.states.get("ai_task.grok_ai_task") is not None

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("setup_credentials")
async def test_oauth_token_update_does_not_reload(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Do not reload entities for normal OAuth refresh-token rotation."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={
            **mock_config_entry.data,
            "token": {
                **mock_config_entry.data["token"],
                "access_token": "rotated-access-token",
                "refresh_token": "rotated-refresh-token",
            },
        },
    )
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.LOADED
    mock_validate.assert_awaited_once()


@pytest.mark.parametrize(
    ("error", "expected_state"),
    [
        pytest.param(
            ReauthenticationRequiredError(
                "expired",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            ConfigEntryState.SETUP_ERROR,
            id="reauthentication",
        ),
        pytest.param(
            AuthenticationRejectedError(
                "rejected",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            ConfigEntryState.SETUP_ERROR,
            id="authentication_rejected",
        ),
        pytest.param(
            RefreshRejectedError(
                "refresh rejected",
                context=ErrorContext(operation=Operation.REFRESH),
            ),
            ConfigEntryState.SETUP_ERROR,
            id="refresh_rejected",
        ),
        pytest.param(
            ConnectionFailureError(
                "offline",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            ConfigEntryState.SETUP_RETRY,
            id="connection",
        ),
        pytest.param(
            RateLimitedError(
                "limited",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            ConfigEntryState.SETUP_RETRY,
            id="rate_limited",
        ),
        pytest.param(
            RequestTimeoutError(
                "timeout",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            ConfigEntryState.SETUP_RETRY,
            id="timeout",
        ),
        pytest.param(
            TransientProviderError(
                "transient",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            ConfigEntryState.SETUP_RETRY,
            id="transient",
        ),
        pytest.param(
            SubscriptionNotEntitledError(
                "not entitled",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            ConfigEntryState.SETUP_ERROR,
            id="subscription",
        ),
        pytest.param(
            QuotaLimitedError(
                "quota",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            ConfigEntryState.SETUP_ERROR,
            id="quota",
        ),
        pytest.param(
            PermanentProviderError(
                "denied",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            ConfigEntryState.SETUP_ERROR,
            id="permanent",
        ),
    ],
)
@pytest.mark.usefixtures("setup_credentials")
async def test_setup_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    error: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Map provider failures into config-entry setup behavior."""
    mock_validate.side_effect = error
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is expected_state


@pytest.mark.usefixtures("setup_credentials")
async def test_setup_account_mismatch(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    provider_snapshot: ProviderSnapshot,
) -> None:
    """Reject a runtime OAuth account mismatch."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo("different", "Other", None),
        models=provider_snapshot.models,
    )
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


@pytest.mark.usefixtures("setup_credentials")
async def test_setup_model_not_entitled(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Load with a repair so the user can select a replacement model."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert state.state == STATE_UNAVAILABLE
    subentry = next(
        entry
        for entry in mock_config_entry.subentries.values()
        if entry.subentry_type == "conversation"
    )
    assert issue_registry.async_get_issue(
        "spacexai", f"model_not_entitled_{subentry.subentry_id}"
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_remove_revokes_refresh_token(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Revoke the provider refresh token on entry removal."""
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_revoke",
        new_callable=AsyncMock,
    ) as revoke:
        await async_remove_entry(hass, mock_config_entry)
    revoke.assert_awaited_once_with("refresh-token", "home-assistant-client", "")


async def test_setup_without_oauth_implementation(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Retry setup until the configured OAuth implementation is available."""
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(
            ModelNotEntitledError(
                "model",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            id="model",
        ),
        pytest.param(
            MalformedProviderResponseError(
                "malformed",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            id="malformed",
        ),
    ],
)
@pytest.mark.usefixtures("setup_credentials")
async def test_additional_setup_errors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    error: Exception,
) -> None:
    """Map remaining typed validation failures to setup errors."""
    mock_validate.side_effect = error
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR


async def test_remove_without_refresh_token(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Skip revocation if OAuth did not issue a refresh token."""
    hass.config_entries.async_update_entry(
        mock_config_entry,
        data={**mock_config_entry.data, "token": {"access_token": "token"}},
    )
    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_revoke",
        new_callable=AsyncMock,
    ) as revoke:
        await async_remove_entry(hass, mock_config_entry)
    revoke.assert_not_awaited()


async def test_remove_without_oauth_implementation(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Skip revocation if application credentials were removed first."""
    await async_remove_entry(hass, mock_config_entry)


@pytest.mark.usefixtures("setup_credentials")
async def test_remove_cleans_account_repairs(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Remove only the repair issues belonging to the removed account."""
    subentry = next(
        entry
        for entry in mock_config_entry.subentries.values()
        if entry.subentry_type == "conversation"
    )
    subscription_issue = f"subscription_not_entitled_{mock_config_entry.entry_id}"
    model_issue = f"model_not_entitled_{subentry.subentry_id}"
    ir.async_create_issue(
        hass,
        "spacexai",
        subscription_issue,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key="subscription_not_entitled",
    )
    ir.async_create_issue(
        hass,
        "spacexai",
        model_issue,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key="model_not_entitled",
        translation_placeholders={"model": "grok-old"},
    )

    with patch(
        "homeassistant.components.spacexai.client.SpaceXAIClient.async_revoke",
        new_callable=AsyncMock,
    ):
        await async_remove_entry(hass, mock_config_entry)
    assert not issue_registry.async_get_issue("spacexai", subscription_issue)
    assert not issue_registry.async_get_issue("spacexai", model_issue)


@pytest.mark.usefixtures("setup_credentials")
async def test_remove_logs_revocation_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Do not block removal when provider revocation fails."""
    error = ConnectionFailureError(
        "offline",
        context=ErrorContext(operation=Operation.REVOCATION),
    )
    with (
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_revoke",
            new_callable=AsyncMock,
            side_effect=error,
        ),
        caplog.at_level("WARNING"),
    ):
        await async_remove_entry(hass, mock_config_entry)
    assert "category=connection_failure" in caplog.text


@pytest.mark.usefixtures("setup_credentials")
async def test_subscription_repair_issue(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
    provider_snapshot: ProviderSnapshot,
) -> None:
    """Create an actionable repair for an ineligible subscription."""
    mock_validate.side_effect = SubscriptionNotEntitledError(
        "not entitled",
        context=ErrorContext(operation=Operation.MODELS),
    )
    assert not await hass.config_entries.async_setup(mock_config_entry.entry_id)
    issue_id = f"subscription_not_entitled_{mock_config_entry.entry_id}"
    other_issue_id = "subscription_not_entitled_other-entry"
    issue = issue_registry.async_get_issue("spacexai", issue_id)
    assert issue is not None
    assert issue.learn_more_url == "https://console.x.ai/"
    ir.async_create_issue(
        hass,
        "spacexai",
        other_issue_id,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key="subscription_not_entitled",
    )

    mock_validate.side_effect = None
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo("healthy-account", "Healthy", None),
        models=provider_snapshot.models,
    )
    healthy_entry = MockConfigEntry(
        domain="spacexai",
        title="Healthy",
        unique_id="healthy-account",
        data=dict(mock_config_entry.data),
    )
    healthy_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(healthy_entry.entry_id)
    assert issue_registry.async_get_issue("spacexai", issue_id)
    assert issue_registry.async_get_issue("spacexai", other_issue_id)


@pytest.mark.usefixtures("setup_credentials")
async def test_remove_skips_revocation_for_foreign_implementation(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Skip token revocation when the implementation is not a local OAuth client."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    with (
        patch(
            "homeassistant.components.spacexai.async_get_config_entry_implementation",
            return_value=MagicMock(),
        ),
        patch(
            "homeassistant.components.spacexai.client.SpaceXAIClient.async_revoke",
            new_callable=AsyncMock,
        ) as revoke,
    ):
        assert await hass.config_entries.async_remove(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    revoke.assert_not_called()
