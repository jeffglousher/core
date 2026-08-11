"""Tests for the SpaceXAI config flow."""

import asyncio
from http import HTTPStatus
from typing import Any
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
)
from homeassistant.components.spacexai import (
    async_begin_catalog_refresh,
    async_mark_subscription_not_entitled,
)
from homeassistant.components.spacexai.client import (
    AccountInfo,
    ModelInfo,
    ProviderSnapshot,
)
from homeassistant.components.spacexai.const import (
    CONF_CODE_INTERPRETER,
    CONF_IMAGE_MODEL,
    CONF_MAX_OUTPUT_TOKENS,
    CONF_TTS_SPEED,
    CONF_VOICE,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    DEFAULT_CODE_INTERPRETER,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_STT_NAME,
    DEFAULT_VOICE,
    DEFAULT_WEB_SEARCH,
    DEFAULT_X_SEARCH,
    DOMAIN,
    OAUTH_SCOPES,
    TOKEN_URL,
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
    PermanentProviderError,
    QuotaLimitedError,
    ReauthenticationRequiredError,
    RefreshRejectedError,
    RequestTimeoutError,
    SubscriptionNotEntitledError,
)
from homeassistant.components.spacexai.oauth_device import DeviceAuthorization
from homeassistant.const import (
    CONF_LLM_HASS_API,
    CONF_MODEL,
    CONF_PROMPT,
    STATE_UNAVAILABLE,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er, issue_registry as ir, llm
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)
from homeassistant.setup import async_setup_component

from . import AGENT_ID, conversation_subentry
from .conftest import ACCESS_TOKEN, ACCOUNT_ID

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator

REDIRECT_URI = "https://example.com/auth/external/callback"
CONVERSATION_DATA = {
    CONF_MODEL: DEFAULT_MODEL,
    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
    CONF_PROMPT: "Be concise.",
    CONF_WEB_SEARCH: DEFAULT_WEB_SEARCH,
    CONF_X_SEARCH: DEFAULT_X_SEARCH,
    CONF_CODE_INTERPRETER: DEFAULT_CODE_INTERPRETER,
    CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
}


async def _start_flow(hass: HomeAssistant) -> config_entries.ConfigFlowResult:
    """Start a user OAuth flow."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def _start_browser_flow(hass: HomeAssistant) -> config_entries.ConfigFlowResult:
    """Start the browser Authorization Code path from the auth menu."""
    result = await _start_flow(hass)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["device", "browser"]
    return await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "browser"}
    )


async def _complete_oauth(
    hass: HomeAssistant,
    result: config_entries.ConfigFlowResult,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    token_response: dict[str, object] | None = None,
) -> config_entries.ConfigFlowResult:
    """Complete the browser callback and exchange the authorization code."""
    query = parse_qs(urlparse(result["url"]).query)
    client = await hass_client_no_auth()
    response = await client.get(
        f"/auth/external/callback?code=authorization-code&state={query['state'][0]}"
    )
    assert response.status == HTTPStatus.OK
    aioclient_mock.post(
        TOKEN_URL,
        json=token_response
        or {
            "access_token": ACCESS_TOKEN,
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
        },
    )
    return await hass.config_entries.flow.async_configure(result["flow_id"])


async def test_missing_credentials(hass: HomeAssistant) -> None:
    """Abort when SpaceXAI has not issued a Home Assistant OAuth identity."""
    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    result = await _start_flow(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "missing_credentials"


@pytest.mark.usefixtures("setup_credentials")
async def test_oauth_implementation_unavailable(hass: HomeAssistant) -> None:
    """Abort when Application Credentials cannot resolve an OAuth implementation."""
    with patch(
        "homeassistant.components.spacexai.config_flow.async_get_implementations",
        side_effect=ImplementationUnavailableError,
    ):
        result = await _start_flow(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "oauth_implementation_unavailable"


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
) -> None:
    """Complete Authorization Code + PKCE and configure Grok."""
    result = await _start_browser_flow(hass)
    assert result["type"] is FlowResultType.EXTERNAL_STEP

    parsed = urlparse(result["url"])
    query = {key: value[0] for key, value in parse_qs(parsed.query).items()}
    assert parsed.geturl().startswith("https://auth.x.ai/oauth2/authorize")
    assert query["client_id"] == "home-assistant-client"
    assert query["redirect_uri"] == REDIRECT_URI
    assert query["scope"] == " ".join(OAUTH_SCOPES)
    assert query["plan"] == "generic"
    assert query["referrer"] == "home-assistant"
    assert query["code_challenge_method"] == "S256"
    assert "code_challenge" in query

    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONVERSATION_DATA
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home User"
    assert result["result"].unique_id == ACCOUNT_ID
    assert result["data"]["token"]["access_token"] == ACCESS_TOKEN
    subentries = list(result["result"].subentries.values())
    assert len(subentries) == 4
    conversation = next(
        subentry for subentry in subentries if subentry.subentry_type == "conversation"
    )
    ai_task = next(
        subentry for subentry in subentries if subentry.subentry_type == "ai_task_data"
    )
    assert conversation.data == CONVERSATION_DATA
    assert ai_task.data == {
        CONF_MODEL: CONVERSATION_DATA[CONF_MODEL],
        CONF_MAX_OUTPUT_TOKENS: CONVERSATION_DATA[CONF_MAX_OUTPUT_TOKENS],
        CONF_IMAGE_MODEL: DEFAULT_IMAGE_MODEL,
    }
    assert mock_validate.await_count == 2


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_initial_conversation_rejects_withdrawn_model(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
) -> None:
    """Abort create_entry when the selected model disappears before save."""
    result = await _start_browser_flow(hass)
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"

    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-fresh", "xai"),),
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONVERSATION_DATA
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "model_not_entitled"


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_initial_conversation_refresh_cannot_connect(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
) -> None:
    """Abort create_entry when the pre-save catalog refresh cannot connect."""
    result = await _start_browser_flow(hass)
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"

    mock_validate.side_effect = ConnectionFailureError(
        "offline",
        context=ErrorContext(operation=Operation.MODELS),
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], CONVERSATION_DATA
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
@pytest.mark.parametrize(
    "token_response",
    [
        pytest.param(
            {
                "refresh_token": "refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer",
            },
            id="access-token",
        ),
        pytest.param(
            {
                "access_token": ACCESS_TOKEN,
                "expires_in": 3600,
                "token_type": "Bearer",
            },
            id="refresh-token",
        ),
    ],
)
async def test_oauth_token_missing_required_token(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    token_response: dict[str, object],
) -> None:
    """Abort if the provider token response violates the OAuth contract."""
    result = await _start_browser_flow(hass)
    result = await _complete_oauth(
        hass,
        result,
        hass_client_no_auth,
        aioclient_mock,
        token_response,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "oauth_error"


@pytest.mark.usefixtures(
    "current_request_with_host",
    "setup_credentials",
    "mock_setup_entry",
    "mock_validate",
)
async def test_duplicate_account(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reject a duplicate account."""
    result = await _start_browser_flow(hass)
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        pytest.param(
            AuthenticationRejectedError(
                "rejected",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            id="authentication",
        ),
        pytest.param(
            SubscriptionNotEntitledError(
                "not entitled",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "subscription_not_entitled",
            id="subscription",
        ),
        pytest.param(
            QuotaLimitedError(
                "quota",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "quota_limited",
            id="quota",
        ),
        pytest.param(
            MalformedProviderResponseError(
                "malformed",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "malformed_provider_response",
            id="malformed",
        ),
        pytest.param(
            ModelNotEntitledError(
                "no models",
                context=ErrorContext(operation=Operation.MODELS, model="Grok"),
            ),
            "model_not_entitled",
            id="models",
        ),
        pytest.param(
            NoConversationModelsError(
                "none",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "no_conversation_models",
            id="no-conversation-models",
        ),
        pytest.param(
            PermanentProviderError(
                "permanent",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "unknown",
            id="unexpected-classified",
        ),
    ],
)
@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_validation_abort(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
    error: Exception,
    reason: str,
) -> None:
    """Map permanent account validation failures to translated aborts."""
    mock_validate.side_effect = error
    result = await _start_browser_flow(hass)
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == reason


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_validation_recovers(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
    provider_snapshot: ProviderSnapshot,
) -> None:
    """Allow retrying a transient provider validation failure."""
    mock_validate.side_effect = [
        ConnectionFailureError(
            "offline",
            context=ErrorContext(operation=Operation.MODELS),
        ),
        provider_snapshot,
    ]
    result = await _start_browser_flow(hass)
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "validate"
    assert result["errors"] == {"base": "cannot_connect"}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"


@pytest.mark.usefixtures(
    "current_request_with_host",
    "setup_credentials",
    "mock_setup_entry",
    "mock_validate",
)
async def test_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Update OAuth tokens after reauthentication."""
    result = await mock_config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.EXTERNAL_STEP
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data["token"]["access_token"] == ACCESS_TOKEN


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_reauth_account_mismatch(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reject reauthentication with a different account before model discovery."""
    mock_validate.side_effect = AccountMismatchError(
        "mismatch",
        context=ErrorContext(operation=Operation.ACCOUNT),
    )
    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "account_mismatch"
    mock_validate.assert_awaited()
    assert mock_validate.await_args.kwargs.get("expected_subject") == ACCOUNT_ID


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_reauth_subscription_failure_creates_repair(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Create the entry-scoped subscription repair when reauth is denied."""
    mock_validate.side_effect = SubscriptionNotEntitledError(
        "not entitled",
        context=ErrorContext(operation=Operation.MODELS),
    )
    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "subscription_not_entitled"
    assert issue_registry.async_get_issue(
        DOMAIN, f"subscription_not_entitled_{mock_config_entry.entry_id}"
    )


@pytest.mark.usefixtures("current_request_with_host", "setup_credentials")
async def test_reauth_subscription_failure_marks_loaded_entities(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
    mock_config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Mark loaded conversation entities unavailable on reauth subscription denial."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    mock_validate.side_effect = SubscriptionNotEntitledError(
        "not entitled",
        context=ErrorContext(operation=Operation.MODELS),
    )
    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "subscription_not_entitled"
    assert issue_registry.async_get_issue(
        DOMAIN, f"subscription_not_entitled_{mock_config_entry.entry_id}"
    )
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_reauth_with_withdrawn_model(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Complete reauthentication even when a configured model was withdrawn."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert mock_config_entry.data["token"]["access_token"] == ACCESS_TOKEN


@pytest.mark.usefixtures("setup_credentials", "mock_validate")
async def test_creating_conversation_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Create an additional conversation subentry with its own entity."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    original_subentry = conversation_subentry(mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-4.3",
            CONF_MAX_OUTPUT_TOKENS: 1024,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(mock_config_entry.subentries) == 5
    added_subentry = next(
        subentry
        for subentry in mock_config_entry.subentries.values()
        if subentry.subentry_type == "conversation"
        and subentry.subentry_id != original_subentry.subentry_id
    )
    assert added_subentry.title == "Grok"
    assert added_subentry.data == {
        CONF_MODEL: "grok-4.3",
        CONF_MAX_OUTPUT_TOKENS: 1024,
        CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
        CONF_WEB_SEARCH: False,
        CONF_X_SEARCH: False,
        CONF_CODE_INTERPRETER: False,
    }
    await hass.async_block_till_done()
    assert {
        entity.config_subentry_id
        for entity in er.async_entries_for_config_entry(
            entity_registry, mock_config_entry.entry_id
        )
    } == {subentry.subentry_id for subentry in mock_config_entry.subentries.values()}


@pytest.mark.usefixtures("setup_credentials")
async def test_reconfigure_conversation_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Update model settings on an existing conversation subentry."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    subentry = conversation_subentry(mock_config_entry)
    mock_validate.reset_mock()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    assert mock_validate.await_args.kwargs.get("expected_subject") == ACCOUNT_ID
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-4.3",
            CONF_MAX_OUTPUT_TOKENS: 4096,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert subentry.data[CONF_MAX_OUTPUT_TOKENS] == 4096


@pytest.mark.usefixtures("setup_credentials")
async def test_reconfigure_withdrawn_model(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Allow model replacement while the configured model is unavailable."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-other", "xai"),),
    )
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    subentry = conversation_subentry(mock_config_entry)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-other",
            CONF_MAX_OUTPUT_TOKENS: 2048,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert subentry.data[CONF_MODEL] == "grok-other"
    await hass.async_block_till_done()
    assert not issue_registry.async_get_issue(
        DOMAIN, f"model_not_entitled_{subentry.subentry_id}"
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_subentry_refreshes_model_catalog(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Refresh the provider model catalog before showing the subentry form."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-fresh", "xai"),),
    )
    mock_validate.reset_mock()

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    mock_validate.assert_awaited()
    assert mock_config_entry.runtime_data.snapshot.has_model("grok-fresh")
    model_options = result["data_schema"].schema[CONF_MODEL].config["options"]
    assert {option["value"] for option in model_options} == {"grok-fresh"}


@pytest.mark.usefixtures("setup_credentials")
@pytest.mark.parametrize(
    ("error", "reason", "starts_reauth"),
    [
        pytest.param(
            ConnectionFailureError(
                "offline",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "cannot_connect",
            False,
            id="cannot-connect",
        ),
        pytest.param(
            ReauthenticationRequiredError(
                "reauth",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            True,
            id="reauth-required",
        ),
        pytest.param(
            RefreshRejectedError(
                "refresh",
                context=ErrorContext(operation=Operation.REFRESH),
            ),
            "oauth_unauthorized",
            True,
            id="refresh-rejected",
        ),
        pytest.param(
            AccountMismatchError(
                "mismatch",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            True,
            id="account-mismatch",
        ),
        pytest.param(
            SubscriptionNotEntitledError(
                "sub",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "subscription_not_entitled",
            False,
            id="subscription",
        ),
        pytest.param(
            NoConversationModelsError(
                "none",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "no_conversation_models",
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
            id="quota",
        ),
        pytest.param(
            ModelNotEntitledError(
                "model",
                context=ErrorContext(operation=Operation.MODELS, model="grok-old"),
            ),
            "model_not_entitled",
            False,
            id="model-not-entitled",
        ),
        pytest.param(
            MalformedProviderResponseError(
                "bad",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "malformed_provider_response",
            False,
            id="malformed",
        ),
        pytest.param(
            PermanentProviderError(
                "denied",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "unknown",
            False,
            id="unknown",
        ),
    ],
)
async def test_subentry_aborts_when_catalog_refresh_fails(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    error: Exception,
    reason: str,
    starts_reauth: bool,
) -> None:
    """Abort subentry configuration with the classified catalog-refresh reason."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    mock_validate.side_effect = error
    with patch.object(mock_config_entry, "async_start_reauth") as start_reauth:
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "conversation"),
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == reason
    assert start_reauth.called is starts_reauth


@pytest.mark.usefixtures("setup_credentials")
@pytest.mark.parametrize(
    ("error", "reason"),
    [
        pytest.param(
            ReauthenticationRequiredError(
                "expired",
                context=ErrorContext(operation=Operation.ACCOUNT),
            ),
            "oauth_unauthorized",
            id="reauth",
        ),
        pytest.param(
            SubscriptionNotEntitledError(
                "no_plan",
                context=ErrorContext(operation=Operation.MODELS),
            ),
            "subscription_not_entitled",
            id="subscription",
        ),
    ],
)
async def test_subentry_ignores_stale_catalog_refresh_side_effects(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
    error: Exception,
    reason: str,
) -> None:
    """A superseded catalog refresh must not start reauth or create a subscription issue."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)

    async def _fail(*_args: object, **_kwargs: object) -> ProviderSnapshot:
        async_begin_catalog_refresh(mock_config_entry)
        raise error

    mock_validate.side_effect = _fail
    with patch.object(mock_config_entry, "async_start_reauth") as start_reauth:
        result = await hass.config_entries.subentries.async_init(
            (mock_config_entry.entry_id, "conversation"),
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == reason
    start_reauth.assert_not_called()
    assert (
        issue_registry.async_get_issue(
            DOMAIN, f"subscription_not_entitled_{mock_config_entry.entry_id}"
        )
        is None
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_subentry_subscription_failure_creates_repair(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Surface a subscription repair when subentry catalog refresh is denied."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    mock_validate.side_effect = SubscriptionNotEntitledError(
        "sub",
        context=ErrorContext(operation=Operation.MODELS),
    )
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "subscription_not_entitled"
    assert issue_registry.async_get_issue(
        DOMAIN, f"subscription_not_entitled_{mock_config_entry.entry_id}"
    )
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("setup_credentials")
async def test_subentry_submit_rejects_withdrawn_model(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Abort when a submitted model disappears from the refreshed catalog."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM

    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo("grok-fresh", "xai"),),
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: DEFAULT_MODEL,
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
            CONF_PROMPT: "Be concise.",
            CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "model_not_entitled"


@pytest.mark.usefixtures("setup_credentials")
async def test_subentry_submit_uses_current_catalog_snapshot(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Reject a submit whose catalog refresh lost to a newer snapshot."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM

    async def _stale_snapshot(**_kwargs: Any) -> ProviderSnapshot:
        mock_config_entry.runtime_data.catalog_epoch += 1
        mock_config_entry.runtime_data.snapshot = ProviderSnapshot(
            account=AccountInfo(ACCOUNT_ID, "Home User", None),
            models=(ModelInfo("grok-fresh", "xai"),),
        )
        return ProviderSnapshot(
            account=AccountInfo(ACCOUNT_ID, "Home User", None),
            models=(ModelInfo(DEFAULT_MODEL, "xai"),),
        )

    mock_validate.side_effect = _stale_snapshot
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: DEFAULT_MODEL,
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
            CONF_PROMPT: "Be concise.",
            CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "model_not_entitled"


@pytest.mark.usefixtures("setup_credentials")
async def test_successful_subentry_refresh_clears_subscription_repair(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
) -> None:
    """Clear a stale subscription repair after a successful catalog snapshot."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    issue_id = f"subscription_not_entitled_{mock_config_entry.entry_id}"
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key="subscription_not_entitled",
    )
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo(ACCOUNT_ID, "Home User", None),
        models=(ModelInfo(DEFAULT_MODEL, "xai"),),
    )
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert not issue_registry.async_get_issue(DOMAIN, issue_id)


@pytest.mark.usefixtures("setup_credentials")
async def test_subentry_refresh_keeps_newer_subscription_repair(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    issue_registry: ir.IssueRegistry,
    provider_snapshot: ProviderSnapshot,
) -> None:
    """Do not clear a subscription repair created while catalog refresh ran."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    issue_id = f"subscription_not_entitled_{mock_config_entry.entry_id}"

    async def _validate_then_runtime_denial(
        **_kwargs: Any,
    ) -> ProviderSnapshot:
        async_mark_subscription_not_entitled(hass, mock_config_entry)
        return provider_snapshot

    mock_validate.side_effect = _validate_then_runtime_denial
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert issue_registry.async_get_issue(DOMAIN, issue_id)
    state = hass.states.get(AGENT_ID)
    assert state is not None
    assert state.state == STATE_UNAVAILABLE


@pytest.mark.usefixtures("setup_credentials", "mock_validate")
async def test_reconfigure_filters_stale_llm_apis(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Drop stored LLM API ids that are no longer registered."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    subentry = conversation_subentry(mock_config_entry)
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={
            **subentry.data,
            CONF_LLM_HASS_API: [llm.LLM_API_ASSIST, "missing-api"],
        },
    )
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    llm_key = next(
        key for key in result["data_schema"].schema if key == CONF_LLM_HASS_API
    )
    assert llm_key.default() == [llm.LLM_API_ASSIST]


@pytest.mark.usefixtures("setup_credentials", "mock_validate")
async def test_reconfigure_preserves_cleared_llm_api(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Do not re-select Assist when the stored subentry has no LLM APIs."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    subentry = conversation_subentry(mock_config_entry)
    data = dict(subentry.data)
    data.pop(CONF_LLM_HASS_API)
    hass.config_entries.async_update_subentry(mock_config_entry, subentry, data=data)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    llm_key = next(
        key for key in result["data_schema"].schema if key == CONF_LLM_HASS_API
    )
    assert llm_key.default() == []


@pytest.mark.parametrize("subentry_type", ["conversation", "ai_task_data"])
async def test_subentry_requires_loaded_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    subentry_type: str,
) -> None:
    """Abort subentry changes while the parent entry is not loaded."""
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, subentry_type),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "entry_not_loaded"


@pytest.mark.usefixtures("setup_credentials", "mock_validate")
@pytest.mark.parametrize(
    ("stored_api", "expected"),
    [
        pytest.param(llm.LLM_API_ASSIST, [llm.LLM_API_ASSIST], id="string"),
        pytest.param(1, [], id="non-list"),
    ],
)
async def test_reconfigure_defaults_non_list_llm_api(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    stored_api: str | int,
    expected: list[str],
) -> None:
    """Normalize stored LLM API values that are not a list of ids."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    subentry = conversation_subentry(mock_config_entry)
    hass.config_entries.async_update_subentry(
        mock_config_entry,
        subentry,
        data={
            **subentry.data,
            CONF_LLM_HASS_API: stored_api,
        },
    )
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": "reconfigure", "subentry_id": subentry.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    llm_key = next(
        key for key in result["data_schema"].schema if key == CONF_LLM_HASS_API
    )
    assert llm_key.default() == expected


async def test_missing_configuration(hass: HomeAssistant) -> None:
    """Abort when the integration exposes no Application Credentials platform."""
    assert await async_setup_component(hass, APPLICATION_CREDENTIALS_DOMAIN, {})
    with patch(
        "homeassistant.components.spacexai.config_flow.async_get_application_credentials",
        return_value=[],
    ):
        result = await _start_flow(hass)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "missing_configuration"


@pytest.mark.usefixtures("setup_credentials")
async def test_ai_task_subentry_add(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Add an AI Task subentry without Assist tools."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "ai_task_data"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-4.3",
            CONF_MAX_OUTPUT_TOKENS: 512,
            CONF_IMAGE_MODEL: DEFAULT_IMAGE_MODEL,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    added = next(
        subentry
        for subentry in mock_config_entry.subentries.values()
        if subentry.title == "Grok AI Task"
        and subentry.data.get(CONF_MODEL) == "grok-4.3"
    )
    assert CONF_LLM_HASS_API not in added.data
    assert any(
        entity.config_subentry_id == added.subentry_id
        for entity in er.async_entries_for_config_entry(
            entity_registry, mock_config_entry.entry_id
        )
    )


@pytest.mark.usefixtures("setup_credentials")
async def test_ai_task_subentry_reconfigure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Reconfigure an AI Task subentry model and token limit."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    subentry = next(
        entry
        for entry in mock_config_entry.subentries.values()
        if entry.subentry_type == "ai_task_data"
    )
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "ai_task_data"),
        context={
            "source": "reconfigure",
            "subentry_id": subentry.subentry_id,
        },
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-4.3",
            CONF_MAX_OUTPUT_TOKENS: 1024,
            CONF_IMAGE_MODEL: DEFAULT_IMAGE_MODEL,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert subentry.data[CONF_MODEL] == "grok-4.3"
    assert subentry.data[CONF_MAX_OUTPUT_TOKENS] == 1024
    assert subentry.data[CONF_IMAGE_MODEL] == DEFAULT_IMAGE_MODEL


def _device_authorization(*, user_code: str = "ABCD-1234") -> DeviceAuthorization:
    """Build a device authorization payload for flow tests."""
    return DeviceAuthorization(
        device_code=f"device-code-{user_code}",
        user_code=user_code,
        verification_uri="https://accounts.x.ai/oauth2/device",
        verification_uri_complete=(
            f"https://accounts.x.ai/oauth2/device?user_code={user_code}"
        ),
        expires_in=1800,
        interval=5,
    )


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_device_code_flow(
    hass: HomeAssistant,
    mock_validate: AsyncMock,
) -> None:
    """Complete device-code login and configure Grok."""

    async def _poll(*args: object, **kwargs: object) -> dict[str, object]:
        await asyncio.sleep(0.05)
        return {
            "access_token": ACCESS_TOKEN,
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "expires_at": 9999999999,
            "token_type": "Bearer",
            "scope": " ".join(OAUTH_SCOPES),
        }

    with (
        patch(
            "homeassistant.components.spacexai.config_flow.async_request_device_authorization",
            new_callable=AsyncMock,
            return_value=_device_authorization(),
        ),
        patch(
            "homeassistant.components.spacexai.config_flow.async_poll_device_token",
            new=_poll,
        ),
    ):
        result = await _start_flow(hass)
        assert result["type"] is FlowResultType.MENU
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "device"}
        )
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["progress_action"] == "wait_for_device"
        assert result["description_placeholders"] == {
            "user_code": "ABCD-1234",
            "verification_uri": (
                "https://accounts.x.ai/oauth2/device?user_code=ABCD-1234"
            ),
            "expires_minutes": "30",
        }

        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "conversation"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONVERSATION_DATA
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].unique_id == ACCOUNT_ID
        assert result["data"]["token"]["access_token"] == ACCESS_TOKEN
        assert result["data"]["token"]["refresh_token"] == "refresh-token"


@pytest.mark.usefixtures("setup_credentials")
async def test_device_code_denied(hass: HomeAssistant) -> None:
    """Show a retry form after the account denies device authorization."""

    async def _poll(*args: object, **kwargs: object) -> dict[str, object]:
        await asyncio.sleep(0.05)
        raise AuthenticationRejectedError(
            "denied",
            context=ErrorContext(operation=Operation.DEVICE_AUTH),
        )

    with (
        patch(
            "homeassistant.components.spacexai.config_flow.async_request_device_authorization",
            new_callable=AsyncMock,
            return_value=_device_authorization(),
        ),
        patch(
            "homeassistant.components.spacexai.config_flow.async_poll_device_token",
            new=_poll,
        ),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "device"}
        )
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "device_denied"


@pytest.mark.usefixtures("setup_credentials")
async def test_device_code_invalid_client(hass: HomeAssistant) -> None:
    """Abort when SpaceXAI rejects the Application Credentials client ID."""
    with patch(
        "homeassistant.components.spacexai.config_flow.async_request_device_authorization",
        new_callable=AsyncMock,
        side_effect=AuthenticationRejectedError(
            "invalid client",
            context=ErrorContext(operation=Operation.DEVICE_AUTH),
        ),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "device"}
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "oauth_unauthorized"


@pytest.mark.usefixtures("setup_credentials")
@pytest.mark.parametrize(
    ("error", "abort_reason"),
    [
        pytest.param(
            ConnectionFailureError(
                "offline",
                context=ErrorContext(operation=Operation.DEVICE_AUTH),
            ),
            "cannot_connect",
            id="connection",
        ),
        pytest.param(
            MalformedProviderResponseError(
                "bad",
                context=ErrorContext(operation=Operation.DEVICE_AUTH),
            ),
            "malformed_provider_response",
            id="malformed",
        ),
        pytest.param(
            PermanentProviderError(
                "rejected",
                context=ErrorContext(operation=Operation.DEVICE_AUTH),
            ),
            "oauth_error",
            id="permanent",
        ),
    ],
)
async def test_device_code_start_failures(
    hass: HomeAssistant,
    error: Exception,
    abort_reason: str,
) -> None:
    """Abort when device authorization cannot be started."""
    with patch(
        "homeassistant.components.spacexai.config_flow.async_request_device_authorization",
        new_callable=AsyncMock,
        side_effect=error,
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "device"}
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == abort_reason


@pytest.mark.usefixtures("setup_credentials")
@pytest.mark.parametrize(
    ("error", "step_id"),
    [
        pytest.param(
            RequestTimeoutError(
                "expired",
                context=ErrorContext(operation=Operation.DEVICE_AUTH),
            ),
            "device_timeout",
            id="timeout",
        ),
        pytest.param(
            ConnectionFailureError(
                "offline",
                context=ErrorContext(operation=Operation.DEVICE_AUTH),
            ),
            "device_connection_error",
            id="connection",
        ),
    ],
)
async def test_device_code_poll_failures(
    hass: HomeAssistant,
    error: Exception,
    step_id: str,
) -> None:
    """Map retryable device polling failures to retry forms."""

    async def _poll(*args: object, **kwargs: object) -> dict[str, object]:
        await asyncio.sleep(0.05)
        raise error

    with (
        patch(
            "homeassistant.components.spacexai.config_flow.async_request_device_authorization",
            new_callable=AsyncMock,
            return_value=_device_authorization(),
        ),
        patch(
            "homeassistant.components.spacexai.config_flow.async_poll_device_token",
            new=_poll,
        ),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "device"}
        )
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == step_id
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.SHOW_PROGRESS


@pytest.mark.usefixtures("setup_credentials")
async def test_device_code_poll_failed(hass: HomeAssistant) -> None:
    """Abort when device polling fails unexpectedly."""

    async def _poll(*args: object, **kwargs: object) -> dict[str, object]:
        await asyncio.sleep(0.05)
        raise PermanentProviderError(
            "rejected",
            context=ErrorContext(operation=Operation.DEVICE_AUTH),
        )

    with (
        patch(
            "homeassistant.components.spacexai.config_flow.async_request_device_authorization",
            new_callable=AsyncMock,
            return_value=_device_authorization(),
        ),
        patch(
            "homeassistant.components.spacexai.config_flow.async_poll_device_token",
            new=_poll,
        ),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "device"}
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "oauth_error"


@pytest.mark.usefixtures("setup_credentials")
async def test_device_code_denied_retry(hass: HomeAssistant) -> None:
    """Restart device authorization after denial."""
    requests = AsyncMock(
        side_effect=[
            _device_authorization(user_code="AAAA-1111"),
            _device_authorization(user_code="BBBB-2222"),
        ]
    )

    async def _poll(*args: object, **kwargs: object) -> dict[str, object]:
        await asyncio.sleep(0.05)
        raise AuthenticationRejectedError(
            "denied",
            context=ErrorContext(operation=Operation.DEVICE_AUTH),
        )

    with (
        patch(
            "homeassistant.components.spacexai.config_flow.async_request_device_authorization",
            new=requests,
        ),
        patch(
            "homeassistant.components.spacexai.config_flow.async_poll_device_token",
            new=_poll,
        ),
    ):
        result = await _start_flow(hass)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "device"}
        )
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["step_id"] == "device_denied"
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        assert result["type"] is FlowResultType.SHOW_PROGRESS
        assert result["description_placeholders"]["user_code"] == "BBBB-2222"


@pytest.mark.usefixtures("setup_credentials")
async def test_stt_subentry_add_and_reconfigure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Add and reconfigure a speech-to-text subentry."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "stt"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_STT_NAME

    existing = next(
        subentry
        for subentry in mock_config_entry.subentries.values()
        if subentry.subentry_type == "stt"
    )
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "stt"),
        context={"source": "reconfigure", "subentry_id": existing.subentry_id},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"


@pytest.mark.usefixtures("setup_credentials")
async def test_tts_subentry_add_and_reconfigure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
) -> None:
    """Add and reconfigure a text-to-speech subentry."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "tts"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_VOICE: "rex", CONF_TTS_SPEED: 1.2}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_VOICE: "rex", CONF_TTS_SPEED: 1.2}

    existing = next(
        subentry
        for subentry in mock_config_entry.subentries.values()
        if subentry.subentry_type == "tts"
        and subentry.data.get(CONF_VOICE) == DEFAULT_VOICE
    )
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "tts"),
        context={"source": "reconfigure", "subentry_id": existing.subentry_id},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_VOICE: "luna", CONF_TTS_SPEED: 0.9}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert existing.data == {CONF_VOICE: "luna", CONF_TTS_SPEED: 0.9}


@pytest.mark.parametrize("subentry_type", ["stt", "tts"])
@pytest.mark.usefixtures("setup_credentials")
async def test_speech_subentry_requires_loaded_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    subentry_type: str,
) -> None:
    """Abort speech subentry changes while the parent entry is not loaded."""
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, subentry_type),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "entry_not_loaded"
