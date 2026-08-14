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
    ConfigSubentryData,
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
    DateSelector,
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
    TextSelector,
    TextSelectorConfig,
)
from homeassistant.loader import async_get_application_credentials

from . import (
    SpaceXAIConfigEntry,
    async_begin_catalog_refresh,
    async_capture_availability_epochs,
    async_create_subscription_issue,
    async_mark_subscription_not_entitled,
    async_reconcile_snapshot,
)
from .client import ProviderSnapshot, SpaceXAIClient, StaticAccessTokenProvider
from .const import (
    CONF_ALLOW_CONTROL_WITH_PROVIDER_TOOLS,
    CONF_CODE_INTERPRETER,
    CONF_CREATE_STT,
    CONF_CREATE_TTS,
    CONF_DEFAULT_ASSIST,
    CONF_IMAGE_ASPECT_RATIO,
    CONF_IMAGE_GENERATION,
    CONF_IMAGE_GENERATION_ACTION,
    CONF_IMAGE_MODEL,
    CONF_IMAGE_RESOLUTION,
    CONF_MAX_OUTPUT_TOKENS,
    CONF_MODEL_CUSTOM,
    CONF_RECOMMENDED,
    CONF_SERVICE_TIER,
    CONF_STORE_RESPONSES,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    CONF_TTS_SPEED,
    CONF_VOICE,
    CONF_WEB_SEARCH,
    CONF_WEB_SEARCH_ALLOWED_DOMAINS,
    CONF_WEB_SEARCH_EXCLUDED_DOMAINS,
    CONF_WEB_SEARCH_IMAGE_SEARCH,
    CONF_WEB_SEARCH_IMAGE_UNDERSTANDING,
    CONF_X_SEARCH,
    CONF_X_SEARCH_ALLOWED_HANDLES,
    CONF_X_SEARCH_EXCLUDED_HANDLES,
    CONF_X_SEARCH_FROM_DATE,
    CONF_X_SEARCH_IMAGE_UNDERSTANDING,
    CONF_X_SEARCH_TO_DATE,
    CONF_X_SEARCH_VIDEO_UNDERSTANDING,
    DEFAULT_AI_TASK_MAX_OUTPUT_TOKENS,
    DEFAULT_AI_TASK_NAME,
    DEFAULT_AI_TASK_SERVICE_TIER,
    DEFAULT_ALLOW_CONTROL_WITH_PROVIDER_TOOLS,
    DEFAULT_CODE_INTERPRETER,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_CREATE_STT,
    DEFAULT_CREATE_TTS,
    DEFAULT_DEFAULT_ASSIST,
    DEFAULT_IMAGE_ASPECT_RATIO,
    DEFAULT_IMAGE_GENERATION,
    DEFAULT_IMAGE_GENERATION_ACTION,
    DEFAULT_IMAGE_MODEL,
    DEFAULT_IMAGE_RESOLUTION,
    DEFAULT_MAX_OUTPUT_TOKENS,
    DEFAULT_MODEL,
    DEFAULT_SERVICE_TIER,
    DEFAULT_STORE_RESPONSES,
    DEFAULT_STT_NAME,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_TTS_NAME,
    DEFAULT_TTS_SPEED,
    DEFAULT_VOICE,
    DEFAULT_WEB_SEARCH,
    DEFAULT_WEB_SEARCH_IMAGE_SEARCH,
    DEFAULT_X_SEARCH,
    DEFAULT_X_SEARCH_VIDEO_UNDERSTANDING,
    DOMAIN,
    GROK_CLI_OAUTH_CLIENT_ID,
    IMAGE_ASPECT_RATIOS,
    IMAGE_GENERATION_ACTIONS,
    IMAGE_MODELS,
    IMAGE_RESOLUTIONS,
    LOGGER,
    MODEL_CUSTOM_OPTION,
    SERVICE_TIERS,
    TTS_VOICES,
)
from .errors import (
    AccountMismatchError,
    AuthenticationRejectedError,
    ConnectionFailureError,
    MalformedProviderResponseError,
    ModelNotEntitledError,
    NoConversationModelsError,
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
from .oauth_device import (
    DeviceAuthorization,
    async_poll_device_token,
    async_request_device_authorization,
)


class SpaceXAIConfigFlow(AbstractOAuth2FlowHandler, domain=DOMAIN):
    """Handle SpaceXAI OAuth configuration."""

    DOMAIN = DOMAIN
    VERSION = 1
    MINOR_VERSION = 2

    def __init__(self) -> None:
        """Initialize the flow."""
        super().__init__()
        self._oauth_data: dict[str, Any] | None = None
        self._snapshot: ProviderSnapshot | None = None
        self._device_authorization: DeviceAuthorization | None = None
        self._device_login_task: asyncio.Task[dict[str, Any]] | None = None
        self._last_rendered_recommended = True
        self._last_rendered_custom_model = False

    @property
    @override
    def logger(self) -> Logger:
        """Return the logger used by the OAuth flow."""
        return LOGGER

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose device-code or browser OAuth after Application Credentials exist."""
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
            return await self.async_step_device()
        return await self.async_step_pick_implementation(user_input)

    def _cancel_device_login_task(self) -> None:
        """Cancel unfinished device login wait and clear authorization refs."""
        if self._device_login_task is not None:
            if not self._device_login_task.done():
                self._device_login_task.cancel()
            self._device_login_task = None
        self._device_authorization = None

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
        self._cancel_device_login_task()
        return await self.async_step_device()

    async def async_step_device_denied(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after the user denied device authorization."""
        if user_input is None:
            return self.async_show_form(step_id="device_denied")
        self._cancel_device_login_task()
        return await self.async_step_device()

    async def async_step_device_connection_error(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after a transient device-authorization failure."""
        if user_input is None:
            return self.async_show_form(step_id="device_connection_error")
        self._cancel_device_login_task()
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

    async def _async_refresh_snapshot(
        self, *, retry_step: str | None
    ) -> ConfigFlowResult | None:
        """Validate with the current OAuth token and store a fresh snapshot."""
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
        expected_subject = (
            self._get_reauth_entry().unique_id if self.source == SOURCE_REAUTH else None
        )
        try:
            self._snapshot = await client.async_validate(
                expected_subject=expected_subject
            )
        except AccountMismatchError:
            return self.async_abort(reason="account_mismatch")
        except AuthenticationRejectedError:
            return self.async_abort(reason="oauth_unauthorized")
        except SubscriptionNotEntitledError:
            if self.source == SOURCE_REAUTH:
                entry = self._get_reauth_entry()
                if entry.state is ConfigEntryState.LOADED:
                    async_mark_subscription_not_entitled(self.hass, entry)
                else:
                    async_create_subscription_issue(self.hass, entry)
            return self.async_abort(reason="subscription_not_entitled")
        except NoConversationModelsError:
            return self.async_abort(reason="no_conversation_models")
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
            if retry_step is None:
                return self.async_abort(reason="cannot_connect")
            return self.async_show_form(
                step_id=retry_step,
                data_schema=vol.Schema({}),
                errors={"base": "cannot_connect"},
            )
        except MalformedProviderResponseError:
            return self.async_abort(reason="malformed_provider_response")
        except SpaceXAIError as err:
            LOGGER.warning(
                "Unexpected classified SpaceXAI setup failure: category=%s "
                "operation=%s status=%s request_id=%s retryable=%s",
                err.category,
                err.context.operation,
                err.context.status,
                err.context.request_id,
                err.retryable,
            )
            return self.async_abort(reason="unknown")
        return None

    async def async_step_validate(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate identity and available language models."""
        if err := await self._async_refresh_snapshot(retry_step="validate"):
            return err
        assert self._snapshot is not None
        assert self._oauth_data is not None

        await self.async_set_unique_id(self._snapshot.account.subject)
        if self.source == SOURCE_REAUTH:
            self._abort_if_unique_id_mismatch(reason="account_mismatch")
            entry = self._get_reauth_entry()
            # Merge tokens into existing entry data so install flags (e.g.
            # default_assist) and other non-OAuth keys are preserved.
            result = self.async_update_and_abort(
                entry,
                data_updates=self._oauth_data,
            )
            self.hass.config_entries.async_schedule_reload(entry.entry_id)
            return result

        self._abort_if_unique_id_configured()
        return await self.async_step_setup_mode()

    async def async_step_setup_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose recommended setup or full customization."""
        return self.async_show_menu(
            step_id="setup_mode",
            menu_options=["recommended", "customize"],
        )

    async def async_step_recommended(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Finish with recommended defaults (conversation, AI task, STT, TTS)."""
        assert self._snapshot is not None
        if user_input is None:
            return self.async_show_form(
                step_id="recommended",
                data_schema=vol.Schema(
                    {
                        vol.Required(
                            CONF_DEFAULT_ASSIST, default=DEFAULT_DEFAULT_ASSIST
                        ): BooleanSelector(),
                    }
                ),
            )

        options = _recommended_conversation_defaults(self._snapshot)
        options[CONF_DEFAULT_ASSIST] = bool(
            user_input.get(CONF_DEFAULT_ASSIST, DEFAULT_DEFAULT_ASSIST)
        )
        options[CONF_CREATE_STT] = True
        options[CONF_CREATE_TTS] = True
        return self._async_create_conversation_entry(options)

    async def async_step_customize(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Customize models/tools during initial install."""
        return await self.async_step_conversation(user_input)

    async def async_step_conversation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the initial Grok conversation entity (customize path)."""
        assert self._snapshot is not None
        assert self._oauth_data is not None

        errors: dict[str, str] = {}
        if user_input is None:
            options = _recommended_conversation_defaults(self._snapshot)
            options[CONF_RECOMMENDED] = False
            options[CONF_DEFAULT_ASSIST] = DEFAULT_DEFAULT_ASSIST
            self._last_rendered_custom_model = False
        else:
            options = dict(user_input)
            options[CONF_RECOMMENDED] = False
            custom_selected = options.get(CONF_MODEL) == MODEL_CUSTOM_OPTION
            if custom_selected != self._last_rendered_custom_model:
                self._last_rendered_custom_model = custom_selected
            else:
                errors = _finalize_conversation_input(options, self._snapshot)
                if not errors:
                    options.setdefault(CONF_CREATE_STT, DEFAULT_CREATE_STT)
                    options.setdefault(CONF_CREATE_TTS, DEFAULT_CREATE_TTS)
                    options.setdefault(CONF_DEFAULT_ASSIST, DEFAULT_DEFAULT_ASSIST)
                    return self._async_create_conversation_entry(options)

        return self.async_show_form(
            step_id="conversation",
            data_schema=_conversation_schema(
                self._snapshot,
                _llm_api_options(self.hass),
                options,
                include_install_options=True,
                include_assist_option=True,
                force_custom=True,
            ),
            errors=errors,
        )

    def _async_create_conversation_entry(
        self, user_input: dict[str, Any]
    ) -> ConfigFlowResult:
        """Create the config entry and default subentries."""
        assert self._snapshot is not None
        assert self._oauth_data is not None
        create_stt = user_input.pop(CONF_CREATE_STT, DEFAULT_CREATE_STT)
        create_tts = user_input.pop(CONF_CREATE_TTS, DEFAULT_CREATE_TTS)
        default_assist = bool(
            user_input.pop(CONF_DEFAULT_ASSIST, DEFAULT_DEFAULT_ASSIST)
        )
        user_input.pop(CONF_MODEL_CUSTOM, None)
        if user_input.get(CONF_MODEL) == MODEL_CUSTOM_OPTION:
            user_input[CONF_MODEL] = DEFAULT_MODEL
        entry_data = {
            **self._oauth_data,
            CONF_DEFAULT_ASSIST: default_assist,
        }
        subentries: list[ConfigSubentryData] = [
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
                    CONF_MAX_OUTPUT_TOKENS: DEFAULT_AI_TASK_MAX_OUTPUT_TOKENS,
                    CONF_TEMPERATURE: user_input.get(
                        CONF_TEMPERATURE, DEFAULT_TEMPERATURE
                    ),
                    CONF_TOP_P: user_input.get(CONF_TOP_P, DEFAULT_TOP_P),
                    CONF_SERVICE_TIER: DEFAULT_AI_TASK_SERVICE_TIER,
                    CONF_STORE_RESPONSES: DEFAULT_STORE_RESPONSES,
                    CONF_IMAGE_MODEL: DEFAULT_IMAGE_MODEL,
                    CONF_IMAGE_ASPECT_RATIO: DEFAULT_IMAGE_ASPECT_RATIO,
                    CONF_IMAGE_RESOLUTION: DEFAULT_IMAGE_RESOLUTION,
                },
                "title": DEFAULT_AI_TASK_NAME,
                "unique_id": None,
            },
        ]
        if create_stt:
            subentries.append(
                {
                    "subentry_type": "stt",
                    "data": {},
                    "title": DEFAULT_STT_NAME,
                    "unique_id": None,
                }
            )
        if create_tts:
            subentries.append(
                {
                    "subentry_type": "tts",
                    "data": {
                        CONF_VOICE: DEFAULT_VOICE,
                        CONF_TTS_SPEED: DEFAULT_TTS_SPEED,
                    },
                    "title": DEFAULT_TTS_NAME,
                    "unique_id": None,
                }
            )
        return self.async_create_entry(
            title=self._snapshot.account.display_name,
            data=entry_data,
            subentries=subentries,
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
            "stt": SpaceXAISTTSubentryFlow,
            "tts": SpaceXAITTSSubentryFlow,
        }


class SpaceXAIConversationSubentryFlow(ConfigSubentryFlow):
    """Add or reconfigure a SpaceXAI conversation entity."""

    _last_rendered_recommended = True
    _last_rendered_custom_model = False

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
        errors: dict[str, str] = {}
        if user_input is None:
            options = (
                _recommended_conversation_defaults(snapshot)
                if is_new
                else dict(self._get_reconfigure_subentry().data)
            )
            # New agents default to recommended (minimal UI). Reconfigure of
            # older subentries without the flag shows the full form.
            options.setdefault(CONF_RECOMMENDED, is_new)
            self._last_rendered_recommended = bool(options[CONF_RECOMMENDED])
            current_model = options.get(CONF_MODEL)
            self._last_rendered_custom_model = current_model == MODEL_CUSTOM_OPTION or (
                isinstance(current_model, str)
                and current_model
                not in {
                    *_discovered_model_ids(snapshot),
                    DEFAULT_MODEL,
                }
                and bool(current_model)
            )
            if (
                self._last_rendered_custom_model
                and current_model != MODEL_CUSTOM_OPTION
            ):
                options[CONF_MODEL_CUSTOM] = current_model
                options[CONF_MODEL] = MODEL_CUSTOM_OPTION
        else:
            options = dict(user_input)
            recommended = bool(options.get(CONF_RECOMMENDED, True))
            custom_selected = options.get(CONF_MODEL) == MODEL_CUSTOM_OPTION
            schema_changed = (
                recommended != self._last_rendered_recommended
                or custom_selected != self._last_rendered_custom_model
            )
            if schema_changed:
                self._last_rendered_recommended = recommended
                self._last_rendered_custom_model = custom_selected
            else:
                if recommended:
                    options = {
                        **_recommended_conversation_defaults(snapshot),
                        CONF_RECOMMENDED: True,
                    }
                errors = _finalize_conversation_input(options, snapshot)
                if not errors:
                    options.pop(CONF_MODEL_CUSTOM, None)
                    if is_new:
                        return self.async_create_entry(
                            title=DEFAULT_CONVERSATION_NAME,
                            data=options,
                        )
                    return self.async_update_and_abort(
                        entry,
                        self._get_reconfigure_subentry(),
                        data=options,
                    )

        return self.async_show_form(
            step_id="user" if is_new else "reconfigure",
            data_schema=_conversation_schema(
                snapshot,
                _llm_api_options(self.hass),
                options,
            ),
            errors=errors,
        )


class SpaceXAIAITaskSubentryFlow(ConfigSubentryFlow):
    """Add or reconfigure a SpaceXAI AI Task entity."""

    _last_rendered_custom_model = False

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
        errors: dict[str, str] = {}
        if user_input is None:
            options = (
                {
                    CONF_MODEL: _default_chat_model(snapshot),
                    CONF_MAX_OUTPUT_TOKENS: DEFAULT_AI_TASK_MAX_OUTPUT_TOKENS,
                    CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
                    CONF_TOP_P: DEFAULT_TOP_P,
                    CONF_SERVICE_TIER: DEFAULT_AI_TASK_SERVICE_TIER,
                    CONF_STORE_RESPONSES: DEFAULT_STORE_RESPONSES,
                    CONF_IMAGE_MODEL: DEFAULT_IMAGE_MODEL,
                    CONF_IMAGE_ASPECT_RATIO: DEFAULT_IMAGE_ASPECT_RATIO,
                    CONF_IMAGE_RESOLUTION: DEFAULT_IMAGE_RESOLUTION,
                }
                if is_new
                else dict(self._get_reconfigure_subentry().data)
            )
            current_model = options.get(CONF_MODEL)
            self._last_rendered_custom_model = current_model == MODEL_CUSTOM_OPTION or (
                isinstance(current_model, str)
                and current_model
                not in {*_discovered_model_ids(snapshot), DEFAULT_MODEL}
                and bool(current_model)
            )
            if (
                self._last_rendered_custom_model
                and current_model != MODEL_CUSTOM_OPTION
            ):
                options[CONF_MODEL_CUSTOM] = current_model
                options[CONF_MODEL] = MODEL_CUSTOM_OPTION
        else:
            options = dict(user_input)
            custom_selected = options.get(CONF_MODEL) == MODEL_CUSTOM_OPTION
            if custom_selected != self._last_rendered_custom_model:
                self._last_rendered_custom_model = custom_selected
            else:
                errors = _finalize_model_input(options, snapshot)
                if not errors:
                    options.pop(CONF_MODEL_CUSTOM, None)
                    if is_new:
                        return self.async_create_entry(
                            title=DEFAULT_AI_TASK_NAME,
                            data=options,
                        )
                    return self.async_update_and_abort(
                        entry,
                        self._get_reconfigure_subentry(),
                        data=options,
                    )

        return self.async_show_form(
            step_id="user" if is_new else "reconfigure",
            data_schema=_ai_task_schema(snapshot, options),
            errors=errors,
        )


class SpaceXAISTTSubentryFlow(ConfigSubentryFlow):
    """Add or reconfigure a SpaceXAI STT entity."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add an STT subentry."""
        return await self._async_configure(user_input, is_new=True)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure an STT subentry."""
        return await self._async_configure(user_input, is_new=False)

    async def _async_configure(
        self,
        user_input: dict[str, Any] | None,
        *,
        is_new: bool,
    ) -> SubentryFlowResult:
        """Create or update an STT subentry."""
        entry = self._get_entry()
        if entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        if user_input is not None:
            if is_new:
                return self.async_create_entry(title=DEFAULT_STT_NAME, data={})
            return self.async_update_and_abort(
                entry,
                self._get_reconfigure_subentry(),
                data={},
            )

        return self.async_show_form(
            step_id="user" if is_new else "reconfigure",
            data_schema=vol.Schema({}),
        )


class SpaceXAITTSSubentryFlow(ConfigSubentryFlow):
    """Add or reconfigure a SpaceXAI TTS entity."""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a TTS subentry."""
        return await self._async_configure(user_input, is_new=True)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a TTS subentry."""
        return await self._async_configure(user_input, is_new=False)

    async def _async_configure(
        self,
        user_input: dict[str, Any] | None,
        *,
        is_new: bool,
    ) -> SubentryFlowResult:
        """Create or update a TTS subentry."""
        entry = self._get_entry()
        if entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        suggested = {} if is_new else dict(self._get_reconfigure_subentry().data)
        if user_input is not None:
            data = {
                CONF_VOICE: user_input[CONF_VOICE],
                CONF_TTS_SPEED: user_input[CONF_TTS_SPEED],
            }
            if is_new:
                return self.async_create_entry(title=DEFAULT_TTS_NAME, data=data)
            return self.async_update_and_abort(
                entry,
                self._get_reconfigure_subentry(),
                data=data,
            )

        return self.async_show_form(
            step_id="user" if is_new else "reconfigure",
            data_schema=_tts_schema(suggested),
        )


def _discovered_model_ids(snapshot: ProviderSnapshot) -> list[str]:
    """Return discovered chat model ids in display order."""
    return [model_id for model in snapshot.models for model_id in model.selectable_ids]


def _default_chat_model(_snapshot: ProviderSnapshot) -> str:
    """Return the preferred chat model for recommended setup (grok-4.5)."""
    return DEFAULT_MODEL


def _model_selector_defaults(
    snapshot: ProviderSnapshot,
    suggested: Mapping[str, Any] | None,
) -> tuple[str, int, list[SelectOptionDict], str | None]:
    """Return default model, token limit, labeled options, and custom value.

    Always surfaces discovered models and the grok-4.5 fallback as distinct
    choices, plus a Custom option for a manual model id string.
    """
    discovered = _discovered_model_ids(snapshot)
    discovered_set = set(discovered)
    default_model = _default_chat_model(snapshot)
    suggested_max_tokens = DEFAULT_MAX_OUTPUT_TOKENS
    custom_model: str | None = None
    if suggested is not None:
        if isinstance(suggested_model := suggested.get(CONF_MODEL), str):
            if suggested_model in discovered_set or suggested_model == DEFAULT_MODEL:
                default_model = suggested_model
            elif suggested_model:
                default_model = MODEL_CUSTOM_OPTION
                custom_model = suggested_model
        if isinstance(suggested_custom := suggested.get(CONF_MODEL_CUSTOM), str):
            custom_model = suggested_custom
        suggested_max_tokens = int(
            suggested.get(CONF_MAX_OUTPUT_TOKENS, DEFAULT_MAX_OUTPUT_TOKENS)
        )

    # Discovered models first; always include grok-4.5 as the sole fallback.
    options: list[SelectOptionDict] = [
        SelectOptionDict(value=model_id, label=f"{model_id} · discovered")
        for model_id in discovered
        if model_id != DEFAULT_MODEL
    ]
    if DEFAULT_MODEL in discovered_set:
        options.insert(
            0,
            SelectOptionDict(
                value=DEFAULT_MODEL,
                label=f"{DEFAULT_MODEL} · discovered / fallback",
            ),
        )
    else:
        options.append(
            SelectOptionDict(
                value=DEFAULT_MODEL,
                label=f"{DEFAULT_MODEL} · fallback",
            )
        )
    options.append(
        SelectOptionDict(
            value=MODEL_CUSTOM_OPTION,
            label="Custom model ID…",
        )
    )
    return default_model, suggested_max_tokens, options, custom_model


def _recommended_conversation_defaults(
    snapshot: ProviderSnapshot,
) -> dict[str, Any]:
    """Return the minimal recommended conversation settings."""
    return {
        CONF_RECOMMENDED: True,
        CONF_MODEL: _default_chat_model(snapshot),
        CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
        CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
        CONF_WEB_SEARCH: DEFAULT_WEB_SEARCH,
        CONF_WEB_SEARCH_IMAGE_UNDERSTANDING: False,
        CONF_WEB_SEARCH_IMAGE_SEARCH: DEFAULT_WEB_SEARCH_IMAGE_SEARCH,
        CONF_WEB_SEARCH_ALLOWED_DOMAINS: [],
        CONF_WEB_SEARCH_EXCLUDED_DOMAINS: [],
        CONF_X_SEARCH: DEFAULT_X_SEARCH,
        CONF_X_SEARCH_IMAGE_UNDERSTANDING: False,
        CONF_X_SEARCH_VIDEO_UNDERSTANDING: DEFAULT_X_SEARCH_VIDEO_UNDERSTANDING,
        CONF_X_SEARCH_ALLOWED_HANDLES: [],
        CONF_X_SEARCH_EXCLUDED_HANDLES: [],
        CONF_CODE_INTERPRETER: DEFAULT_CODE_INTERPRETER,
        CONF_IMAGE_GENERATION: DEFAULT_IMAGE_GENERATION,
        CONF_IMAGE_GENERATION_ACTION: DEFAULT_IMAGE_GENERATION_ACTION,
        CONF_ALLOW_CONTROL_WITH_PROVIDER_TOOLS: (
            DEFAULT_ALLOW_CONTROL_WITH_PROVIDER_TOOLS
        ),
        CONF_MAX_OUTPUT_TOKENS: DEFAULT_MAX_OUTPUT_TOKENS,
        CONF_TEMPERATURE: DEFAULT_TEMPERATURE,
        CONF_TOP_P: DEFAULT_TOP_P,
        CONF_SERVICE_TIER: DEFAULT_SERVICE_TIER,
        CONF_STORE_RESPONSES: DEFAULT_STORE_RESPONSES,
    }


def _finalize_model_input(
    user_input: dict[str, Any],
    snapshot: ProviderSnapshot,
) -> dict[str, str]:
    """Resolve Custom model ID selection into a concrete model string."""
    selected = user_input.get(CONF_MODEL)
    custom = str(user_input.get(CONF_MODEL_CUSTOM, "") or "").strip()
    if selected == MODEL_CUSTOM_OPTION:
        if not custom or custom == MODEL_CUSTOM_OPTION:
            return {CONF_MODEL_CUSTOM: "custom_model_required"}
        user_input[CONF_MODEL] = custom
    elif not isinstance(selected, str) or not selected:
        user_input[CONF_MODEL] = _default_chat_model(snapshot)
    user_input.pop(CONF_MODEL_CUSTOM, None)
    if user_input.get(CONF_MODEL) == MODEL_CUSTOM_OPTION:
        return {CONF_MODEL_CUSTOM: "custom_model_required"}
    if CONF_MAX_OUTPUT_TOKENS not in user_input:
        user_input[CONF_MAX_OUTPUT_TOKENS] = DEFAULT_MAX_OUTPUT_TOKENS
    if CONF_TEMPERATURE not in user_input:
        user_input[CONF_TEMPERATURE] = DEFAULT_TEMPERATURE
    if CONF_TOP_P not in user_input:
        user_input[CONF_TOP_P] = DEFAULT_TOP_P
    if CONF_STORE_RESPONSES not in user_input:
        user_input[CONF_STORE_RESPONSES] = DEFAULT_STORE_RESPONSES
    if (
        CONF_SERVICE_TIER not in user_input
        or user_input[CONF_SERVICE_TIER] not in SERVICE_TIERS
    ):
        user_input[CONF_SERVICE_TIER] = DEFAULT_SERVICE_TIER
    return {}


def _finalize_conversation_input(
    user_input: dict[str, Any],
    snapshot: ProviderSnapshot,
) -> dict[str, str]:
    """Resolve model selection and validate conversation options.

    Install-only toggles (STT/TTS/Assist) stay on user_input until
    ``_async_create_conversation_entry`` pops them into entry data.
    """
    if errors := _finalize_model_input(user_input, snapshot):
        return errors
    return _validate_conversation_input(user_input)


def _csv_suggested_value(value: Any) -> str | None:
    """Convert a stored list or string into a comma-separated form value."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return ", ".join(str(item) for item in value if str(item).strip())
    return str(value)


def _parse_csv_list(value: Any, *, limit: int) -> list[str]:
    """Parse a comma-separated string or list into a capped list of items."""
    if value is None:
        return []
    if isinstance(value, list):
        items = [str(item).strip() for item in value]
    else:
        items = [part.strip() for part in str(value).split(",")]
    return [item for item in items if item][:limit]


def _validate_conversation_input(user_input: dict[str, Any]) -> dict[str, str]:
    """Validate conversation options and normalize list fields in place."""
    errors: dict[str, str] = {}

    allowed_domains = _parse_csv_list(
        user_input.get(CONF_WEB_SEARCH_ALLOWED_DOMAINS), limit=5
    )
    excluded_domains = _parse_csv_list(
        user_input.get(CONF_WEB_SEARCH_EXCLUDED_DOMAINS), limit=5
    )
    allowed_handles = _parse_csv_list(
        user_input.get(CONF_X_SEARCH_ALLOWED_HANDLES), limit=20
    )
    excluded_handles = _parse_csv_list(
        user_input.get(CONF_X_SEARCH_EXCLUDED_HANDLES), limit=20
    )
    user_input[CONF_WEB_SEARCH_ALLOWED_DOMAINS] = allowed_domains
    user_input[CONF_WEB_SEARCH_EXCLUDED_DOMAINS] = excluded_domains
    user_input[CONF_X_SEARCH_ALLOWED_HANDLES] = allowed_handles
    user_input[CONF_X_SEARCH_EXCLUDED_HANDLES] = excluded_handles

    if allowed_domains and excluded_domains:
        errors[CONF_WEB_SEARCH_EXCLUDED_DOMAINS] = "web_search_domain_filters"

    provider_tools_enabled = any(
        (
            user_input.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH),
            user_input.get(CONF_X_SEARCH, DEFAULT_X_SEARCH),
            user_input.get(CONF_CODE_INTERPRETER, DEFAULT_CODE_INTERPRETER),
            user_input.get(CONF_IMAGE_GENERATION, DEFAULT_IMAGE_GENERATION),
        )
    )
    hass_apis = user_input.get(CONF_LLM_HASS_API) or []
    allow_control = user_input.get(
        CONF_ALLOW_CONTROL_WITH_PROVIDER_TOOLS,
        DEFAULT_ALLOW_CONTROL_WITH_PROVIDER_TOOLS,
    )
    if provider_tools_enabled and hass_apis and not allow_control:
        errors[CONF_ALLOW_CONTROL_WITH_PROVIDER_TOOLS] = "control_with_provider_tools"

    return errors


def _conversation_schema(
    snapshot: ProviderSnapshot,
    llm_apis: list[SelectOptionDict],
    suggested: Mapping[str, Any] | None,
    *,
    include_install_options: bool = False,
    include_assist_option: bool = False,
    force_custom: bool = False,
) -> vol.Schema:
    """Build the conversation configuration schema with progressive disclosure."""
    defaults = suggested or _recommended_conversation_defaults(snapshot)
    recommended = False if force_custom else bool(defaults.get(CONF_RECOMMENDED, True))
    schema: dict[Any, Any] = {}
    if not force_custom:
        schema[vol.Required(CONF_RECOMMENDED, default=recommended)] = BooleanSelector()
        if recommended:
            return vol.Schema(schema)

    (
        default_model,
        suggested_max_tokens,
        model_options,
        custom_model,
    ) = _model_selector_defaults(snapshot, defaults)
    suggested_apis = defaults.get(CONF_LLM_HASS_API, [llm.LLM_API_ASSIST])
    suggested_prompt = defaults.get(CONF_PROMPT)
    suggested_web_search = bool(defaults.get(CONF_WEB_SEARCH, DEFAULT_WEB_SEARCH))
    suggested_x_search = bool(defaults.get(CONF_X_SEARCH, DEFAULT_X_SEARCH))
    suggested_code_interpreter = bool(
        defaults.get(CONF_CODE_INTERPRETER, DEFAULT_CODE_INTERPRETER)
    )
    suggested_image_generation = bool(
        defaults.get(CONF_IMAGE_GENERATION, DEFAULT_IMAGE_GENERATION)
    )
    suggested_image_generation_action = defaults.get(
        CONF_IMAGE_GENERATION_ACTION, DEFAULT_IMAGE_GENERATION_ACTION
    )
    suggested_allow_control = bool(
        defaults.get(
            CONF_ALLOW_CONTROL_WITH_PROVIDER_TOOLS,
            DEFAULT_ALLOW_CONTROL_WITH_PROVIDER_TOOLS,
        )
    )
    suggested_web_image_understanding = bool(
        defaults.get(CONF_WEB_SEARCH_IMAGE_UNDERSTANDING, False)
    )
    suggested_web_image_search = bool(
        defaults.get(CONF_WEB_SEARCH_IMAGE_SEARCH, DEFAULT_WEB_SEARCH_IMAGE_SEARCH)
    )
    suggested_x_image_understanding = bool(
        defaults.get(CONF_X_SEARCH_IMAGE_UNDERSTANDING, False)
    )
    suggested_x_video_understanding = bool(
        defaults.get(
            CONF_X_SEARCH_VIDEO_UNDERSTANDING, DEFAULT_X_SEARCH_VIDEO_UNDERSTANDING
        )
    )
    suggested_allowed_domains = _csv_suggested_value(
        defaults.get(CONF_WEB_SEARCH_ALLOWED_DOMAINS)
    )
    suggested_excluded_domains = _csv_suggested_value(
        defaults.get(CONF_WEB_SEARCH_EXCLUDED_DOMAINS)
    )
    suggested_allowed_handles = _csv_suggested_value(
        defaults.get(CONF_X_SEARCH_ALLOWED_HANDLES)
    )
    suggested_excluded_handles = _csv_suggested_value(
        defaults.get(CONF_X_SEARCH_EXCLUDED_HANDLES)
    )
    suggested_x_from_date = defaults.get(CONF_X_SEARCH_FROM_DATE)
    suggested_x_to_date = defaults.get(CONF_X_SEARCH_TO_DATE)
    suggested_create_stt = bool(defaults.get(CONF_CREATE_STT, DEFAULT_CREATE_STT))
    suggested_create_tts = bool(defaults.get(CONF_CREATE_TTS, DEFAULT_CREATE_TTS))
    if not suggested_prompt:
        suggested_prompt = llm.DEFAULT_INSTRUCTIONS_PROMPT

    schema[vol.Required(CONF_MODEL, default=default_model)] = SelectSelector(
        SelectSelectorConfig(options=model_options)
    )
    if default_model == MODEL_CUSTOM_OPTION or custom_model:
        schema[
            vol.Optional(
                CONF_MODEL_CUSTOM,
                description={"suggested_value": custom_model},
            )
        ] = TextSelector(TextSelectorConfig())
    schema.update(
        {
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
            vol.Optional(
                CONF_WEB_SEARCH_ALLOWED_DOMAINS,
                description={"suggested_value": suggested_allowed_domains},
            ): TextSelector(TextSelectorConfig()),
            vol.Optional(
                CONF_WEB_SEARCH_EXCLUDED_DOMAINS,
                description={"suggested_value": suggested_excluded_domains},
            ): TextSelector(TextSelectorConfig()),
            vol.Required(
                CONF_WEB_SEARCH_IMAGE_UNDERSTANDING,
                default=suggested_web_image_understanding,
            ): BooleanSelector(),
            vol.Required(
                CONF_WEB_SEARCH_IMAGE_SEARCH,
                default=suggested_web_image_search,
            ): BooleanSelector(),
            vol.Required(
                CONF_X_SEARCH,
                default=suggested_x_search,
            ): BooleanSelector(),
            vol.Optional(
                CONF_X_SEARCH_ALLOWED_HANDLES,
                description={"suggested_value": suggested_allowed_handles},
            ): TextSelector(TextSelectorConfig()),
            vol.Optional(
                CONF_X_SEARCH_EXCLUDED_HANDLES,
                description={"suggested_value": suggested_excluded_handles},
            ): TextSelector(TextSelectorConfig()),
            vol.Optional(
                CONF_X_SEARCH_FROM_DATE,
                description={"suggested_value": suggested_x_from_date},
            ): DateSelector(),
            vol.Optional(
                CONF_X_SEARCH_TO_DATE,
                description={"suggested_value": suggested_x_to_date},
            ): DateSelector(),
            vol.Required(
                CONF_X_SEARCH_IMAGE_UNDERSTANDING,
                default=suggested_x_image_understanding,
            ): BooleanSelector(),
            vol.Required(
                CONF_X_SEARCH_VIDEO_UNDERSTANDING,
                default=suggested_x_video_understanding,
            ): BooleanSelector(),
            vol.Required(
                CONF_CODE_INTERPRETER,
                default=suggested_code_interpreter,
            ): BooleanSelector(),
            vol.Required(
                CONF_IMAGE_GENERATION,
                default=suggested_image_generation,
            ): BooleanSelector(),
            vol.Required(
                CONF_IMAGE_GENERATION_ACTION,
                default=suggested_image_generation_action,
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=action, label=action)
                        for action in IMAGE_GENERATION_ACTIONS
                    ]
                )
            ),
            vol.Required(
                CONF_ALLOW_CONTROL_WITH_PROVIDER_TOOLS,
                default=suggested_allow_control,
            ): BooleanSelector(),
            **_sampling_schema(defaults, suggested_max_tokens),
        }
    )
    if include_install_options:
        schema[vol.Required(CONF_CREATE_STT, default=suggested_create_stt)] = (
            BooleanSelector()
        )
        schema[vol.Required(CONF_CREATE_TTS, default=suggested_create_tts)] = (
            BooleanSelector()
        )
    if include_assist_option:
        suggested_default_assist = bool(
            defaults.get(CONF_DEFAULT_ASSIST, DEFAULT_DEFAULT_ASSIST)
        )
        schema[vol.Required(CONF_DEFAULT_ASSIST, default=suggested_default_assist)] = (
            BooleanSelector()
        )
    return vol.Schema(schema)


def _ai_task_schema(
    snapshot: ProviderSnapshot,
    suggested: Mapping[str, Any] | None,
) -> vol.Schema:
    """Build the AI Task configuration schema."""
    defaults = dict(suggested or {})
    if CONF_MAX_OUTPUT_TOKENS not in defaults:
        defaults[CONF_MAX_OUTPUT_TOKENS] = DEFAULT_AI_TASK_MAX_OUTPUT_TOKENS
    if CONF_SERVICE_TIER not in defaults:
        defaults[CONF_SERVICE_TIER] = DEFAULT_AI_TASK_SERVICE_TIER
    default_model, suggested_max_tokens, model_options, custom_model = (
        _model_selector_defaults(snapshot, defaults)
    )
    image_models = snapshot.selectable_image_models or list(IMAGE_MODELS)
    image_model = DEFAULT_IMAGE_MODEL
    if isinstance(suggested_image := defaults.get(CONF_IMAGE_MODEL), str):
        image_model = suggested_image
    elif DEFAULT_IMAGE_MODEL not in image_models and image_models:
        image_model = image_models[0]
    image_aspect_ratio = DEFAULT_IMAGE_ASPECT_RATIO
    image_resolution = DEFAULT_IMAGE_RESOLUTION
    if isinstance(suggested_ratio := defaults.get(CONF_IMAGE_ASPECT_RATIO), str):
        image_aspect_ratio = suggested_ratio
    if isinstance(suggested_resolution := defaults.get(CONF_IMAGE_RESOLUTION), str):
        image_resolution = suggested_resolution
    schema: dict[Any, Any] = {
        vol.Required(CONF_MODEL, default=default_model): SelectSelector(
            SelectSelectorConfig(options=model_options)
        ),
    }
    if default_model == MODEL_CUSTOM_OPTION or custom_model:
        schema[
            vol.Optional(
                CONF_MODEL_CUSTOM,
                description={"suggested_value": custom_model},
            )
        ] = TextSelector(TextSelectorConfig())
    schema.update(
        {
            vol.Required(CONF_IMAGE_MODEL, default=image_model): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=model, label=model)
                        for model in image_models
                    ]
                )
            ),
            vol.Required(
                CONF_IMAGE_ASPECT_RATIO, default=image_aspect_ratio
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=ratio, label=ratio)
                        for ratio in IMAGE_ASPECT_RATIOS
                    ]
                )
            ),
            vol.Required(
                CONF_IMAGE_RESOLUTION, default=image_resolution
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=resolution, label=resolution)
                        for resolution in IMAGE_RESOLUTIONS
                    ]
                )
            ),
            **_sampling_schema(defaults, suggested_max_tokens),
        }
    )
    return vol.Schema(schema)


def _tts_schema(suggested: Mapping[str, Any]) -> vol.Schema:
    """Build the TTS configuration schema."""
    return vol.Schema(
        {
            vol.Required(
                CONF_VOICE,
                default=suggested.get(CONF_VOICE, DEFAULT_VOICE),
            ): SelectSelector(
                SelectSelectorConfig(
                    options=[
                        SelectOptionDict(value=voice_id, label=name)
                        for voice_id, name in TTS_VOICES
                    ]
                )
            ),
            vol.Required(
                CONF_TTS_SPEED,
                default=float(suggested.get(CONF_TTS_SPEED, DEFAULT_TTS_SPEED)),
            ): NumberSelector(
                NumberSelectorConfig(
                    min=0.7,
                    max=1.5,
                    step=0.1,
                    mode=NumberSelectorMode.SLIDER,
                )
            ),
        }
    )


def _sampling_schema(
    defaults: Mapping[str, Any],
    suggested_max_tokens: int,
) -> dict[Any, Any]:
    """Return shared response-length and sampling fields."""
    suggested_temperature = float(defaults.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE))
    suggested_top_p = float(defaults.get(CONF_TOP_P, DEFAULT_TOP_P))
    suggested_store = bool(defaults.get(CONF_STORE_RESPONSES, DEFAULT_STORE_RESPONSES))
    suggested_tier = defaults.get(CONF_SERVICE_TIER, DEFAULT_SERVICE_TIER)
    if suggested_tier not in SERVICE_TIERS:
        suggested_tier = DEFAULT_SERVICE_TIER
    return {
        **_max_output_tokens_schema(suggested_max_tokens),
        vol.Required(
            CONF_SERVICE_TIER,
            default=suggested_tier,
        ): SelectSelector(
            SelectSelectorConfig(
                options=list(SERVICE_TIERS),
                translation_key=CONF_SERVICE_TIER,
                mode=SelectSelectorMode.DROPDOWN,
            )
        ),
        vol.Required(
            CONF_TEMPERATURE,
            default=suggested_temperature,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=2,
                step=0.05,
                mode=NumberSelectorMode.SLIDER,
            )
        ),
        vol.Required(
            CONF_TOP_P,
            default=suggested_top_p,
        ): NumberSelector(
            NumberSelectorConfig(
                min=0,
                max=1,
                step=0.05,
                mode=NumberSelectorMode.SLIDER,
            )
        ),
        vol.Required(
            CONF_STORE_RESPONSES,
            default=suggested_store,
        ): BooleanSelector(),
    }


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
