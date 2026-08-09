"""Tests for the SpaceXAI config flow."""

from http import HTTPStatus
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from homeassistant import config_entries
from homeassistant.components.application_credentials import (
    DOMAIN as APPLICATION_CREDENTIALS_DOMAIN,
)
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
    OAUTH_SCOPES,
    TOKEN_URL,
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
    SubscriptionNotEntitledError,
)
from homeassistant.const import CONF_LLM_HASS_API, CONF_MODEL, CONF_PROMPT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er, issue_registry as ir, llm
from homeassistant.helpers.config_entry_oauth2_flow import (
    ImplementationUnavailableError,
)
from homeassistant.setup import async_setup_component

from .conftest import ACCESS_TOKEN, ACCOUNT_ID

from tests.common import MockConfigEntry
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator

REDIRECT_URI = "https://example.com/auth/external/callback"
CONVERSATION_DATA = {
    CONF_MODEL: DEFAULT_MODEL,
    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
    CONF_PROMPT: "Be concise.",
    CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
}


async def _start_flow(hass: HomeAssistant) -> config_entries.ConfigFlowResult:
    """Start a user OAuth flow."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def _start_browser_flow(hass: HomeAssistant) -> config_entries.ConfigFlowResult:
    """Start the Authorization Code + PKCE path."""
    return await _start_flow(hass)


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
    assert len(subentries) == 1
    assert subentries[0].subentry_type == "conversation"
    assert subentries[0].data == CONVERSATION_DATA
    mock_validate.assert_awaited_once()


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
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_duplicate_account(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
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
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
async def test_reauth(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_validate: AsyncMock,
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
    provider_snapshot: ProviderSnapshot,
) -> None:
    """Reject reauthentication with a different account."""
    mock_validate.return_value = ProviderSnapshot(
        account=AccountInfo("different-account", "Other", None),
        models=provider_snapshot.models,
    )
    result = await mock_config_entry.start_reauth_flow(hass)
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await _complete_oauth(hass, result, hass_client_no_auth, aioclient_mock)
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "account_mismatch"


@pytest.mark.usefixtures(
    "current_request_with_host", "setup_credentials", "mock_setup_entry"
)
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


@pytest.mark.usefixtures("setup_credentials")
async def test_subentry_add_and_reconfigure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_validate: AsyncMock,
    entity_registry: er.EntityRegistry,
) -> None:
    """Add and reconfigure conversation subentries."""
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    original_subentry = next(
        subentry
        for subentry in mock_config_entry.subentries.values()
        if subentry.subentry_type == "conversation"
    )

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
    assert len(mock_config_entry.subentries) == 2
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
    }
    await hass.async_block_till_done()
    assert {
        entity.config_subentry_id
        for entity in er.async_entries_for_config_entry(
            entity_registry, mock_config_entry.entry_id
        )
    } == {subentry.subentry_id for subentry in mock_config_entry.subentries.values()}

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={
            "source": "reconfigure",
            "subentry_id": original_subentry.subentry_id,
        },
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-4.3",
            CONF_MAX_OUTPUT_TOKENS: 4096,
        },
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert original_subentry.data[CONF_MAX_OUTPUT_TOKENS] == 4096


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
    subentry = next(
        entry
        for entry in mock_config_entry.subentries.values()
        if entry.subentry_type == "conversation"
    )
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


async def test_subentry_requires_loaded_entry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Abort subentry changes while the parent entry is not loaded."""
    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "entry_not_loaded"


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
