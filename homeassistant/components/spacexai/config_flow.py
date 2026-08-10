"""Config flow for SpaceXAI."""

import asyncio
from collections.abc import Mapping
from logging import Logger
from typing import Any, cast, override

import voluptuous as vol

from homeassistant.config_entries import (
    SOURCE_REAUTH,
    ConfigEntryState,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_LLM_HASS_API, CONF_MODEL, CONF_PROMPT
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import llm
from homeassistant.helpers.config_entry_oauth2_flow import (
    AbstractOAuth2FlowHandler,
    ImplementationUnavailableError,
    LocalOAuth2Implementation,
    async_get_implementations,
)
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    TemplateSelector,
)
from homeassistant.loader import async_get_application_credentials

from . import SpaceXAIConfigEntry
from .client import ProviderSnapshot, SpaceXAIClient, StaticAccessTokenProvider
from .const import (
    CONF_CODE_INTERPRETER,
    CONF_MAX_OUTPUT_TOKENS,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CODE_INTERPRETER,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_WEB_SEARCH,
    DEFAULT_X_SEARCH,
    DOMAIN,
    GROK_CLI_OAUTH_CLIENT_ID,
    LOGGER,
)
from .errors import (
    AuthenticationRejectedError,
    ConnectionFailureError,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    PermanentProviderError,
    QuotaLimitedError,
    RateLimitedError,
    RequestTimeoutError,
    SpaceXAIError,
    SubscriptionNotEntitledError,
    TransientProviderError,
)
from .oauth_device import (
    DeviceAuthorization,
    async_poll_device_token,
    async_request_device_authorization,
)


class SpaceXAIConfigFlow(AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle SpaceXAI OAuth configuration."""

    DOMAIN = DOMAIN

    def __init__(self) -> None:
        """Initialize the flow."""
        super().__init__()
        self._oauth_data: dict[str, Any] | None = None
        self._snapshot: ProviderSnapshot | None = None
        self._device_authorization: DeviceAuthorization | None = None
        self._device_login_task: asyncio.Task[dict[str, Any]] | None = None

    @property
    @override
    def logger(self) -> Logger:
        """Return the logger used by the OAuth flow."""
        return LOGGER

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start device-code OAuth after Application Credentials exist.

        Device code is the supported path for the public Grok CLI OAuth client
        (Hermes/OpenCode). Browser redirect is kept for HA-owned clients that
        register a Home Assistant redirect URI.
        """
        if err := await self._async_ensure_oauth_implementation():
            return err
        assert isinstance(self.flow_impl, LocalOAuth2Implementation)
        if self.flow_impl.client_id == GROK_CLI_OAUTH_CLIENT_ID:
            return await self.async_step_device()
        return self.async_show_menu(
            step_id="user",
            menu_options=["device", "browser"],
        )

    async def async_step_browser(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Use Authorization Code + PKCE through the Home Assistant redirect."""
        if err := await self._async_ensure_oauth_implementation():
            return err
        assert isinstance(self.flow_impl, LocalOAuth2Implementation)
        if self.flow_impl.client_id == GROK_CLI_OAUTH_CLIENT_ID:
            # Public Grok CLI client has no HA redirect URI registered.
            return await self.async_step_device()
        return await self.async_step_pick_implementation(user_input)

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Authorize with SpaceXAI using the RFC 8628 device code grant."""
        assert isinstance(self.flow_impl, LocalOAuth2Implementation)

        if self._device_authorization is None:
            try:
                self._device_authorization = await async_request_device_authorization(
                    self.hass,
                    client_id=self.flow_impl.client_id,
                )
            except AuthenticationRejectedError:
                return self.async_abort(reason="oauth_unauthorized")
            except (
                ConnectionFailureError,
                RateLimitedError,
                RequestTimeoutError,
                TransientProviderError,
            ):
                return self.async_abort(reason="cannot_connect")
            except MalformedProviderResponseError:
                return self.async_abort(reason="malformed_provider_response")
            except PermanentProviderError, SpaceXAIError:
                LOGGER.exception("SpaceXAI device authorization failed to start")
                return self.async_abort(reason="oauth_error")

        authorization = self._device_authorization

        async def _wait_for_device_approval() -> dict[str, Any]:
            return await async_poll_device_token(
                self.hass,
                client_id=cast(LocalOAuth2Implementation, self.flow_impl).client_id,
                device_code=authorization.device_code,
                expires_in=authorization.expires_in,
                interval=authorization.interval,
            )

        if self._device_login_task is None:
            self._device_login_task = self.hass.async_create_task(
                _wait_for_device_approval()
            )

        if self._device_login_task.done():
            if exception := self._device_login_task.exception():
                self._device_login_task = None
                self._device_authorization = None
                if isinstance(exception, AuthenticationRejectedError):
                    return self.async_show_progress_done(next_step_id="device_denied")
                if isinstance(
                    exception,
                    (
                        ConnectionFailureError,
                        RateLimitedError,
                        TransientProviderError,
                    ),
                ):
                    return self.async_show_progress_done(
                        next_step_id="device_connection_error"
                    )
                if isinstance(exception, RequestTimeoutError):
                    return self.async_show_progress_done(next_step_id="device_timeout")
                LOGGER.exception("SpaceXAI device authorization polling failed")
                return self.async_show_progress_done(next_step_id="device_failed")
            return self.async_show_progress_done(next_step_id="device_finish")

        return self.async_show_progress(
            step_id="device",
            progress_action="wait_for_device",
            description_placeholders={
                "user_code": authorization.user_code,
                "verification_uri": authorization.verification_uri_complete,
                "expires_minutes": str(max(1, authorization.expires_in // 60)),
            },
            progress_task=self._device_login_task,
        )

    async def async_step_device_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create the OAuth entry after device approval."""
        assert self._device_login_task is not None
        assert isinstance(self.flow_impl, LocalOAuth2Implementation)
        token = self._device_login_task.result()
        self._device_login_task = None
        self._device_authorization = None
        return await self.async_oauth_create_entry(
            {
                "auth_implementation": self.flow_impl.domain,
                "token": token,
            }
        )

    async def async_step_device_timeout(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after the device code expired."""
        if user_input is None:
            return self.async_show_form(step_id="device_timeout")
        return await self.async_step_device()

    async def async_step_device_denied(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after the user denied device authorization."""
        if user_input is None:
            return self.async_show_form(step_id="device_denied")
        return await self.async_step_device()

    async def async_step_device_connection_error(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after a transient device-authorization failure."""
        if user_input is None:
            return self.async_show_form(step_id="device_connection_error")
        return await self.async_step_device()

    async def async_step_device_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Abort when device authorization failed unexpectedly."""
        return self.async_abort(reason="oauth_error")

    async def _async_ensure_oauth_implementation(self) -> ConfigFlowResult | None:
        """Resolve Application Credentials into the active OAuth implementation."""
        try:
            implementations = await async_get_implementations(self.hass, self.DOMAIN)
        except ImplementationUnavailableError:
            return self.async_abort(reason="oauth_implementation_unavailable")
        if not implementations:
            if self.DOMAIN in await async_get_application_credentials(self.hass):
                return self.async_abort(reason="missing_credentials")
            return self.async_abort(reason="missing_configuration")
        self.flow_impl = next(iter(implementations.values()))
        return None

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication for an invalid OAuth session."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm that the user wants to sign in again."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    @override
    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Validate the OAuth account before creating an entry."""
        self._oauth_data = data
        return await self.async_step_validate()

    async def async_step_validate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate identity and available language models."""
        assert self._oauth_data is not None

        token_data = self._oauth_data.get("token")
        if (
            not isinstance(token_data, Mapping)
            or not isinstance(access_token := token_data.get("access_token"), str)
            or not access_token
            or not isinstance(token_data.get("refresh_token"), str)
            or not token_data["refresh_token"]
        ):
            return self.async_abort(reason="oauth_error")

        client = SpaceXAIClient(
            self.hass,
            StaticAccessTokenProvider(access_token),
            runtime_session=False,
        )
        try:
            self._snapshot = await client.async_validate()
        except AuthenticationRejectedError:
            return self.async_abort(reason="oauth_unauthorized")
        except SubscriptionNotEntitledError:
            return self.async_abort(reason="subscription_not_entitled")
        except ModelNotEntitledError:
            return self.async_abort(reason="model_not_entitled")
        except QuotaLimitedError:
            return self.async_abort(reason="quota_limited")
        except (
            ConnectionFailureError,
            RateLimitedError,
            RequestTimeoutError,
            TransientProviderError,
        ) as err:
            LOGGER.warning(
                "Unable to validate SpaceXAI account: category=%s operation=%s "
                "status=%s request_id=%s retryable=%s",
                err.category,
                err.context.operation,
                err.context.status,
                err.context.request_id,
                err.retryable,
            )
            return self.async_show_form(
                step_id="validate",
                data_schema=vol.Schema({}),
                errors={"base": "cannot_connect"},
            )
        except MalformedProviderResponseError:
            return self.async_abort(reason="malformed_provider_response")
        except SpaceXAIError:
            LOGGER.exception("Unexpected classified SpaceXAI setup failure")
            return self.async_abort(reason="unknown")

        await self.async_set_unique_id(self._snapshot.account.subject)
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="account_mismatch")
            entry = self._get_reauth_entry()
            result = self.async_update_and_abort(
                entry,
                data=self._oauth_data,
            )
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return result

        self._abort_if_unique_id_configured()
        return await self.async_step_conversation()

    async def async_step_conversation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the initial Grok conversation entity."""
        assert self._snapshot is not None
        assert self._oauth_data is not None

        if user_input is not None:
            return self.async_create_entry(
                title=self._snapshot.account.display_name,
                data=self._oauth_data,
                subentries=[
                    {
                        "subentry_type": "conversation",
                        "data": user_input,
                        "title": DEFAULT_CONVERSATION_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "ai_task_data",
                        "data": {
                            CONF_MODEL: user_input[CONF_MODEL],
                            CONF_MAX_OUTPUT_TOKENS: user_input[CONF_MAX_OUTPUT_TOKENS],
                        },
                        "title": DEFAULT_AI_TASK_NAME,
                        "unique_id": None,
                    },
                ],
            )

        return self.async_show_form(
            step_id="conversation",
            data_schema=_conversation_schema(
                self._snapshot,
                _llm_api_options(self.hass),
                user_input,
            ),
        )

    @classmethod
    @callback
    @override
    def async_get_supported_subentry_types(
        cls, config_entry: SpaceXAIConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return supported subentry flow handlers."""
        return {
            "conversation": SpaceXAIConversationSubentryFlow,
            "ai_task_data": SpaceXAIAITaskSubentryFlow,
        }


class SpaceXAIConversationSubentryFlow(ConfigSubentryFlow):
    """Add or reconfigure a SpaceXAI conversation entity."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a conversation subentry."""
        return await self._async_configure(user_input, is_new=True)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a conversation subentry."""
        return await self._async_configure(user_input, is_new=False)

    async def _async_configure(
        self,
        user_input: dict[str, Any] | None,
        *,
        is_new: bool,
    ) -> SubentryFlowResult:
        """Create or update a conversation subentry."""
        entry = self._get_entry()
        if entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        snapshot = entry.runtime_data.snapshot
        if user_input is not None:
            if is_new:
                return self.async_create_entry(
                    title=DEFAULT_CONVERSATION_NAME,
                    data=user_input,
                )
            return self.async_update_and_abort(
                entry,
                self._get_reconfigure_subentry(),
                data=user_input,
            )

        suggested = None if is_new else dict(self._get_reconfigure_subentry().data)
        return self.async_show_form(
            step_id="user" if is_new else "reconfigure",
            data_schema=_conversation_schema(
                snapshot,
                _llm_api_options(self.hass),
                user_input or suggested,
            ),
        )


class SpaceXAIAITaskSubentryFlow(ConfigSubentryFlow):
    """Add or reconfigure a SpaceXAI AI Task entity."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add an AI Task subentry."""
        return await self._async_configure(user_input, is_new=True)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure an AI Task subentry."""
        return await self._async_configure(user_input, is_new=False)

    async def _async_configure(
        self,
        user_input: dict[str, Any] | None,
        *,
        is_new: bool,
    ) -> SubentryFlowResult:
        """Create or update an AI Task subentry."""
        entry = self._get_entry()
        if entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        snapshot = entry.runtime_data.snapshot
        if user_input is not None:
            if is_new:
                return self.async_create_entry(
                    title=DEFAULT_AI_TASK_NAME,
                    data=user_input,
                )
            return self.async_update_and_abort(
                entry,
                self._get_reconfigure_subentry(),
                data=user_input,
            )

        suggested = None if is_new else dict(self._get_reconfigure_subentry().data)
        return self.async_show_form(
            step_id="user" if is_new else "reconfigure",
            data_schema=_ai_task_schema(snapshot, user_input or suggested),
        )


def _model_selector_defaults(
    snapshot: ProviderSnapshot,
    suggested: Mapping[str, Any] | None,
) -> tuple[str, int, list[SelectOptionDict]]:
    """Return default model, token limit, and model options."""
    model_ids = {
        model_id for model in snapshot.models for model_id in model.selectable_ids
    }
    # Subscription OAuth often returns a sparse /models catalog; keep grok-4.5
    # as a selectable fallback so setup can finish without discovery metadata.
    default_model = DEFAULT_MODEL
    if DEFAULT_MODEL not in model_ids and snapshot.models:
        default_model = snapshot.models[0].selectable_ids[0]
    suggested_max_tokens = DEFAULT_MAX_OUTPUT_TOKENS
    if suggested is not None:
        if (
            isinstance(suggested_model := suggested.get(CONF_MODEL), str)
            and (suggested_model in model_ids or suggested_model == DEFAULT_MODEL)
        ):
            default_model = suggested_model
        suggested_max_tokens = int(
            suggested.get(CONF_MAX_OUTPUT_TOKENS, DEFAULT_MAX_OUTPUT_TOKENS)
        )
    options = [
        SelectOptionDict(value=model_id, label=model_id)
        for model in snapshot.models
        for model_id in model.selectable_ids
    ]
    if DEFAULT_MODEL not in model_ids:
        options.append(SelectOptionDict(value=DEFAULT_MODEL, label=DEFAULT_MODEL))
    return default_model, suggested_max_tokens, options


def _conversation_schema(
    snapshot: ProviderSnapshot,
    llm_apis: list[SelectOptionDict],
    suggested: Mapping[str, Any] | None,
) -> vol.Schema:
    """Build the conversation configuration schema."""
    default_model, suggested_max_tokens, model_options = _model_selector_defaults(
        snapshot, suggested
    )
    if suggested is not None:
        suggested_apis = suggested.get(CONF_LLM_HASS_API, [llm.LLM_API_ASSIST])
        suggested_prompt = suggested.get(CONF_PROMPT)
        suggested_web_search = bool(suggested.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH))
        suggested_x_search = bool(suggested.get(CONF_X_SEARCH, DEFAULT_X_SEARCH))
        suggested_code_interpreter = bool(
            suggested.get(CONF_CODE_INTERPRETER, DEFAULT_CODE_INTERPRETER)
        )
    else:
        suggested_apis = [llm.LLM_API_ASSIST]
        suggested_prompt = None
        suggested_web_search = DEFAULT_WEB_SEARCH
        suggested_x_search = DEFAULT_X_SEARCH
        suggested_code_interpreter = DEFAULT_CODE_INTERPRETER

    return vol.Schema(
        {
            vol.Required(CONF_MODEL, default=default_model): SelectSelector(
                SelectSelectorConfig(options=model_options)
            ),
            vol.Optional(
                CONF_LLM_HASS_API,
                default=suggested_apis,
            ): SelectSelector(SelectSelectorConfig(options=llm_apis, multiple=True)),
            vol.Optional(
                CONF_PROMPT,
                description={"suggested_value": suggested_prompt},
            ): TemplateSelector(),
            vol.Required(
                CONF_WEB_SEARCH,
                default=suggested_web_search,
            ): BooleanSelector(),
            vol.Required(
                CONF_X_SEARCH,
                default=suggested_x_search,
            ): BooleanSelector(),
            vol.Required(
                CONF_CODE_INTERPRETER,
                default=suggested_code_interpreter,
            ): BooleanSelector(),
            **_max_output_tokens_schema(suggested_max_tokens),
        }
    )


def _ai_task_schema(
    snapshot: ProviderSnapshot,
    suggested: Mapping[str, Any] | None,
) -> vol.Schema:
    """Build the AI Task configuration schema."""
    default_model, suggested_max_tokens, model_options = _model_selector_defaults(
        snapshot, suggested
    )
    return vol.Schema(
        {
            vol.Required(CONF_MODEL, default=default_model): SelectSelector(
                SelectSelectorConfig(options=model_options)
            ),
            **_max_output_tokens_schema(suggested_max_tokens),
        }
    )


def _max_output_tokens_schema(default: int) -> dict[Any, Any]:
    """Return the shared max-output-tokens field schema."""
    return {
        vol.Required(
            CONF_MAX_OUTPUT_TOKENS,
            default=default,
        ): vol.All(
            NumberSelector(
                NumberSelectorConfig(
                    min=1,
                    max=131072,
                    step=1,
                    mode=NumberSelectorMode.BOX,
                )
            ),
            vol.Coerce(int),
        )
    }


@callback
def _llm_api_options(hass: HomeAssistant) -> list[SelectOptionDict]:
    """Return currently registered Home Assistant LLM APIs."""
    return [
        SelectOptionDict(value=api.id, label=api.name)
        for api in llm.async_get_apis(hass)
    ]
