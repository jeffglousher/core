"""Tests for the SpaceXAI config flow."""

import asyncio
from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from spacexai_subscription_client import (
    Account,
    AuthenticationError,
    AuthorizationDeniedError,
    ConnectionFailureError,
    DeviceAuthorization,
    DeviceAuthorizationExpiredError,
    OAuthToken,
    RateLimitError,
    RequestTimeoutError,
    SpaceXAISubscriptionClient,
    SpaceXAISubscriptionError,
)

from homeassistant.components import conversation
from homeassistant.components.spacexai.const import (
    CONF_CODE_INTERPRETER,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.const import (
    ATTR_SUPPORTED_FEATURES,
    CONF_LLM_HASS_API,
    CONF_MODEL,
    CONF_NAME,
    CONF_PROMPT,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from .conftest import ACCESS_TOKEN, REFRESH_TOKEN

from tests.common import MockConfigEntry

TOKEN_RESPONSE = {
    "access_token": ACCESS_TOKEN,
    "refresh_token": REFRESH_TOKEN,
    "expires_in": 3600,
    "token_type": "Bearer",
}
TOKEN_DATA = {**TOKEN_RESPONSE, "expires_at": 1234.0}
DEVICE_AUTHORIZATION = DeviceAuthorization(
    device_code="device-code",
    user_code="ABCD-1234",
    verification_uri="https://accounts.x.ai/oauth2/device",
    verification_uri_complete=(
        "https://accounts.x.ai/oauth2/device?user_code=ABCD-1234"
    ),
    expires_in=1800,
    interval=1,
)


async def _start_flow(hass: HomeAssistant) -> ConfigFlowResult:
    """Start a SpaceXAI user flow."""
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )


async def _finish_device_progress(
    hass: HomeAssistant, mock_flow_client: MagicMock, result: ConfigFlowResult
) -> ConfigFlowResult:
    """Advance a device flow after its polling task completes."""
    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["description_placeholders"] == {
        "user_code": "ABCD-1234",
        "verification_uri": "https://accounts.x.ai/oauth2/device?user_code=ABCD-1234",
    }
    mock_flow_client.poll_event.set()
    await hass.async_block_till_done()
    return await hass.config_entries.flow.async_configure(result["flow_id"])


def _set_successful_poll(mock_flow_client: MagicMock) -> None:
    """Make token polling wait until the progress form has been asserted."""
    mock_flow_client.poll_event = asyncio.Event()

    async def _async_poll(*_args: object) -> OAuthToken:
        await mock_flow_client.poll_event.wait()
        return OAuthToken(TOKEN_DATA)

    mock_flow_client.async_poll_device_token.side_effect = _async_poll


def _set_poll_error(
    mock_flow_client: MagicMock, error: type[SpaceXAISubscriptionError]
) -> None:
    """Make token polling fail after the progress form has been asserted."""
    mock_flow_client.poll_event = asyncio.Event()

    async def _async_poll(*_args: object) -> OAuthToken:
        await mock_flow_client.poll_event.wait()
        raise error

    mock_flow_client.async_poll_device_token.side_effect = _async_poll


@pytest.fixture
def mock_flow_client() -> Generator[MagicMock]:
    """Return a successful mocked client for the config flow."""
    client = MagicMock(spec=SpaceXAISubscriptionClient)
    client.async_request_device_authorization = AsyncMock(
        return_value=DEVICE_AUTHORIZATION
    )
    client.async_poll_device_token = AsyncMock()
    client.async_get_account = AsyncMock(
        return_value=Account("account-123", "Home User", "home@test")
    )
    client.async_list_models = AsyncMock(return_value=("grok-4.5", "grok-4.6"))
    _set_successful_poll(client)
    with patch(
        "homeassistant.components.spacexai.config_flow.create_client",
        return_value=client,
    ):
        yield client


@pytest.mark.usefixtures("mock_setup_entry")
async def test_full_oauth_flow(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Complete device login and create one Conversation subentry."""
    result = await _start_flow(hass)
    result = await _finish_device_progress(hass, mock_flow_client, result)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"
    assert result["data_schema"] is not None
    assert result["data_schema"].schema[CONF_MODEL].config["options"] == [
        "grok-4.5",
        "grok-4.6",
    ]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-4.6",
            CONF_PROMPT: "Be concise.",
            CONF_LLM_HASS_API: [],
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Home User"
    assert result["result"].unique_id == "account-123"
    assert result["data"] == {
        "auth_implementation": DOMAIN,
        "token": TOKEN_DATA,
    }
    subentries = list(result["subentries"])
    assert len(subentries) == 2
    assert subentries[0]["subentry_type"] == "conversation"
    assert subentries[0]["data"] == {
        CONF_MODEL: "grok-4.6",
        CONF_PROMPT: "Be concise.",
    }
    assert subentries[1]["subentry_type"] == "ai_task_data"
    assert subentries[1]["data"] == {CONF_MODEL: "grok-4.6"}


@pytest.mark.usefixtures("mock_setup_entry")
async def test_device_authorization_rejected(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Abort when the OAuth client is rejected."""
    mock_flow_client.async_request_device_authorization.side_effect = (
        AuthenticationError
    )

    result = await _start_flow(hass)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_auth"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_device_authorization_connection_error(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Retry when device authorization cannot be started."""
    mock_flow_client.async_request_device_authorization.side_effect = [
        SpaceXAISubscriptionError,
        DEVICE_AUTHORIZATION,
    ]

    result = await _start_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_connection_error"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    result = await _finish_device_progress(hass, mock_flow_client, result)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"
    assert mock_flow_client.async_request_device_authorization.await_count == 2


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(ConnectionFailureError, id="connection"),
        pytest.param(RateLimitError, id="rate_limit"),
        pytest.param(RequestTimeoutError, id="timeout"),
    ],
)
@pytest.mark.usefixtures("mock_setup_entry")
async def test_device_authorization_transient_poll_error_and_retry(
    hass: HomeAssistant,
    error: type[SpaceXAISubscriptionError],
    mock_flow_client: MagicMock,
) -> None:
    """Retry transient polling failures with the same device authorization."""
    _set_poll_error(mock_flow_client, error)

    result = await _start_flow(hass)
    result = await _finish_device_progress(hass, mock_flow_client, result)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_connection_error"

    _set_successful_poll(mock_flow_client)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    result = await _finish_device_progress(hass, mock_flow_client, result)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"
    mock_flow_client.async_request_device_authorization.assert_awaited_once()


@pytest.mark.parametrize(
    ("error", "step_id"),
    [
        pytest.param(AuthorizationDeniedError, "device_denied", id="denied"),
        pytest.param(DeviceAuthorizationExpiredError, "device_timeout", id="expired"),
        pytest.param(SpaceXAISubscriptionError, "device_connection_error", id="other"),
    ],
)
@pytest.mark.usefixtures("mock_setup_entry")
async def test_device_authorization_terminal_poll_error_and_retry(
    hass: HomeAssistant,
    error: type[SpaceXAISubscriptionError],
    mock_flow_client: MagicMock,
    step_id: str,
) -> None:
    """Request a new device authorization after a terminal polling failure."""
    _set_poll_error(mock_flow_client, error)

    result = await _start_flow(hass)
    result = await _finish_device_progress(hass, mock_flow_client, result)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == step_id

    _set_successful_poll(mock_flow_client)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    result = await _finish_device_progress(hass, mock_flow_client, result)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"
    assert mock_flow_client.async_request_device_authorization.await_count == 2


@pytest.mark.usefixtures("mock_setup_entry")
async def test_device_authorization_poll_authentication_error(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Abort when device token polling rejects the OAuth client."""
    _set_poll_error(mock_flow_client, AuthenticationError)

    result = await _start_flow(hass)
    result = await _finish_device_progress(hass, mock_flow_client, result)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_auth"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_account_validation_authentication_error(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Abort when the approved account rejects the access token."""
    mock_flow_client.async_get_account.side_effect = AuthenticationError

    result = await _finish_device_progress(
        hass, mock_flow_client, await _start_flow(hass)
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "invalid_auth"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_account_validation_connection_error_and_retry(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Retry account validation without repeating device authorization."""
    mock_flow_client.async_get_account.side_effect = SpaceXAISubscriptionError

    result = await _finish_device_progress(
        hass, mock_flow_client, await _start_flow(hass)
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_validation_error"

    mock_flow_client.async_get_account.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"
    mock_flow_client.async_request_device_authorization.assert_awaited_once()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_account_has_no_models(
    hass: HomeAssistant,
    mock_flow_client: MagicMock,
) -> None:
    """Retry validation when the approved account has no available models."""
    mock_flow_client.async_list_models.return_value = ()

    result = await _finish_device_progress(
        hass, mock_flow_client, await _start_flow(hass)
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "device_validation_error"

    mock_flow_client.async_list_models.return_value = ("grok-4.5",)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "conversation"


@pytest.mark.usefixtures("mock_spacexai_subscription_client")
async def test_create_conversation_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Create another conversation agent with opt-in provider tools."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"] is not None
    assert result["data_schema"].schema[CONF_MODEL].config["options"] == ["grok-4.6"]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Research Grok",
            CONF_MODEL: "grok-4.6",
            CONF_PROMPT: "Cite sources.",
            CONF_LLM_HASS_API: [],
            CONF_WEB_SEARCH: True,
            CONF_X_SEARCH: True,
            CONF_CODE_INTERPRETER: False,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Research Grok"
    assert result["data"] == {
        CONF_MODEL: "grok-4.6",
        CONF_PROMPT: "Cite sources.",
        CONF_WEB_SEARCH: True,
        CONF_X_SEARCH: True,
    }
    await hass.async_block_till_done()
    assert hass.states.get("conversation.research_grok") is not None


@pytest.mark.parametrize("enable_assist", [True])
@pytest.mark.usefixtures("mock_spacexai_subscription_client")
async def test_reconfigure_conversation_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reconfigure a conversation agent and remove disabled options."""
    await setup_integration(hass, mock_config_entry)
    subentry = next(iter(mock_config_entry.subentries.values()))
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert (
        state.attributes[ATTR_SUPPORTED_FEATURES]
        == conversation.ConversationEntityFeature.CONTROL
    )

    result = await mock_config_entry.start_subentry_reconfigure_flow(
        hass, subentry.subentry_id
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    updated = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODEL: "grok-4.6",
            CONF_PROMPT: "Use calculations.",
            CONF_LLM_HASS_API: [],
            CONF_WEB_SEARCH: False,
            CONF_X_SEARCH: False,
            CONF_CODE_INTERPRETER: True,
        },
    )
    await hass.async_block_till_done()

    assert updated["type"] is FlowResultType.ABORT
    assert updated["reason"] == "reconfigure_successful"
    assert subentry.data == {
        CONF_MODEL: "grok-4.6",
        CONF_PROMPT: "Use calculations.",
        CONF_CODE_INTERPRETER: True,
    }
    state = hass.states.get("conversation.grok")
    assert state is not None
    assert state.attributes[ATTR_SUPPORTED_FEATURES] == 0


async def test_create_conversation_subentry_not_loaded(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reject adding a conversation agent while the account is disabled."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "conversation"),
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "entry_not_loaded"


@pytest.mark.usefixtures("mock_spacexai_subscription_client")
async def test_create_ai_task_subentry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Create an AI Task subentry."""
    await setup_integration(hass, mock_config_entry)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "ai_task_data"),
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["data_schema"] is not None
    assert result["data_schema"].schema[CONF_MODEL].config["options"] == ["grok-4.6"]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_NAME: "Automation Grok", CONF_MODEL: "grok-4.6"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Automation Grok"
    assert result["data"] == {CONF_MODEL: "grok-4.6"}


async def test_create_ai_task_subentry_not_loaded(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Reject adding an AI Task entity while the account is disabled."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.subentries.async_init(
        (mock_config_entry.entry_id, "ai_task_data"),
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "entry_not_loaded"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_duplicate_account(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_flow_client: MagicMock,
) -> None:
    """Abort when the signed-in account is already configured."""
    mock_config_entry.add_to_hass(hass)
    result = await _start_flow(hass)
    result = await _finish_device_progress(hass, mock_flow_client, result)

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    mock_flow_client.async_list_models.assert_not_awaited()
