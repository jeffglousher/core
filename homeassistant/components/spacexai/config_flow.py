"""Config flow for SpaceXAI."""

import asyncio
from typing import Any, override

from spacexai_subscription_client import (
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
import voluptuous as vol

from homeassistant.config_entries import (
    ConfigEntryState,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.const import CONF_LLM_HASS_API, CONF_MODEL, CONF_NAME, CONF_PROMPT
from homeassistant.core import callback
from homeassistant.helpers import llm
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TemplateSelector,
)

from . import create_client
from .const import (
    CONF_CODE_INTERPRETER,
    CONF_TTS_SPEED,
    CONF_WEB_SEARCH,
    CONF_X_SEARCH,
    DEFAULT_AI_TASK_NAME,
    DEFAULT_CONVERSATION_NAME,
    DEFAULT_STT_NAME,
    DEFAULT_TTS_NAME,
    DOMAIN,
    RECOMMENDED_CONVERSATION_OPTIONS,
    RECOMMENDED_TTS_SPEED,
)
from .models import SpaceXAIConfigEntry

PROVIDER_TOOL_OPTIONS = (CONF_WEB_SEARCH, CONF_X_SEARCH, CONF_CODE_INTERPRETER)


def _clean_conversation_options(options: dict[str, Any]) -> dict[str, Any]:
    """Remove disabled optional capabilities from stored options."""
    if not options.get(CONF_LLM_HASS_API):
        options.pop(CONF_LLM_HASS_API, None)
    for option in PROVIDER_TOOL_OPTIONS:
        if not options.get(option):
            options.pop(option, None)
    return options


def _conversation_schema(
    models: list[str] | tuple[str, ...],
    hass_apis: list[SelectOptionDict],
) -> vol.Schema:
    """Return the conversation configuration schema."""
    return vol.Schema(
        {
            vol.Required(CONF_MODEL): SelectSelector(
                SelectSelectorConfig(
                    options=list(models),
                    mode=SelectSelectorMode.DROPDOWN,
                    sort=True,
                )
            ),
            vol.Optional(CONF_PROMPT): TemplateSelector(),
            vol.Optional(CONF_LLM_HASS_API): SelectSelector(
                SelectSelectorConfig(options=hass_apis, multiple=True)
            ),
            vol.Optional(CONF_WEB_SEARCH, default=False): bool,
            vol.Optional(CONF_X_SEARCH, default=False): bool,
            vol.Optional(CONF_CODE_INTERPRETER, default=False): bool,
        }
    )


class SpaceXAIConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle SpaceXAI configuration."""

    VERSION = 1

    @classmethod
    @callback
    @override
    def async_get_supported_subentry_types(
        cls, config_entry: SpaceXAIConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return the supported subentry types."""
        return {
            "ai_task_data": SpaceXAIEntitySubentryFlow,
            "conversation": SpaceXAIEntitySubentryFlow,
            "stt": SpaceXAISpeechSubentryFlow,
            "tts": SpaceXAISpeechSubentryFlow,
        }

    def __init__(self) -> None:
        """Initialize the flow."""
        self._client: SpaceXAISubscriptionClient | None = None
        self._device: DeviceAuthorization | None = None
        self._login_task: asyncio.Task[OAuthToken] | None = None
        self._token: dict[str, Any] | None = None
        self._account_name = "SpaceXAI"
        self._models: list[str] = []

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Start device authorization."""
        return await self.async_step_device()

    async def async_step_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Authorize with SpaceXAI using a device code."""
        if self._device is None:
            try:
                self._client = create_client(self.hass)
                self._device = await self._client.async_request_device_authorization()
            except AuthenticationError:
                return self.async_abort(reason="invalid_auth")
            except SpaceXAISubscriptionError:
                return await self.async_step_device_connection_error()

        if self._login_task is None:
            assert self._client is not None
            self._login_task = self.hass.async_create_task(
                self._client.async_poll_device_token(self._device),
            )

        if self._login_task.done():
            login_task = self._login_task
            self._login_task = None
            if error := login_task.exception():
                if isinstance(error, AuthorizationDeniedError):
                    self._device = None
                    return self.async_show_progress_done(next_step_id="device_denied")
                if isinstance(error, AuthenticationError):
                    self._device = None
                    return self.async_show_progress_done(
                        next_step_id="device_invalid_auth"
                    )
                if isinstance(error, DeviceAuthorizationExpiredError):
                    self._device = None
                    return self.async_show_progress_done(next_step_id="device_timeout")
                if not isinstance(
                    error,
                    (ConnectionFailureError, RateLimitError, RequestTimeoutError),
                ):
                    self._device = None
                return self.async_show_progress_done(
                    next_step_id="device_connection_error"
                )
            self._token = login_task.result().as_dict()
            self._device = None
            return self.async_show_progress_done(next_step_id="device_finish")

        return self.async_show_progress(
            step_id="device",
            progress_action="wait_for_device",
            description_placeholders={
                "user_code": self._device.user_code,
                "verification_uri": self._device.verification_uri_complete,
            },
            progress_task=self._login_task,
        )

    async def async_step_device_finish(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate the OAuth account after device approval."""
        assert self._token is not None
        try:
            await self._async_validate_account()
        except AuthenticationError:
            return self.async_abort(reason="invalid_auth")
        except SpaceXAISubscriptionError:
            return await self.async_step_device_validation_error()

        return await self.async_step_conversation()

    async def async_step_conversation(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure the initial conversation agent."""
        assert self._token is not None
        if user_input is not None:
            _clean_conversation_options(user_input)
            return self.async_create_entry(
                title=self._account_name,
                data={"auth_implementation": DOMAIN, "token": self._token},
                subentries=[
                    {
                        "subentry_type": "conversation",
                        "data": user_input,
                        "title": DEFAULT_CONVERSATION_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "ai_task_data",
                        "data": {CONF_MODEL: user_input[CONF_MODEL]},
                        "title": DEFAULT_AI_TASK_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "stt",
                        "data": {},
                        "title": DEFAULT_STT_NAME,
                        "unique_id": None,
                    },
                    {
                        "subentry_type": "tts",
                        "data": {CONF_TTS_SPEED: RECOMMENDED_TTS_SPEED},
                        "title": DEFAULT_TTS_NAME,
                        "unique_id": None,
                    },
                ],
            )

        hass_apis = [
            SelectOptionDict(label=api.name, value=api.id)
            for api in llm.async_get_apis(self.hass)
        ]
        return self.async_show_form(
            step_id="conversation",
            data_schema=self.add_suggested_values_to_schema(
                _conversation_schema(self._models, hass_apis),
                RECOMMENDED_CONVERSATION_OPTIONS,
            ),
        )

    async def async_step_device_timeout(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after the device code expires."""
        if user_input is None:
            return self.async_show_form(step_id="device_timeout")
        return await self.async_step_device()

    async def async_step_device_denied(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after device authorization is denied."""
        if user_input is None:
            return self.async_show_form(step_id="device_denied")
        return await self.async_step_device()

    async def async_step_device_invalid_auth(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Abort after device authorization credentials are rejected."""
        return self.async_abort(reason="invalid_auth")

    async def async_step_device_connection_error(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after a device authorization connection error."""
        if user_input is None:
            return self.async_show_form(step_id="device_connection_error")
        return await self.async_step_device()

    async def async_step_device_validation_error(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Retry after account validation fails."""
        if user_input is None:
            return self.async_show_form(step_id="device_validation_error")
        return await self.async_step_device_finish()

    async def _async_validate_account(self) -> None:
        """Validate account identity and load available models."""
        assert self._token is not None
        assert self._client is not None
        access_token = self._token["access_token"]
        account = await self._client.async_get_account(access_token)
        await self.async_set_unique_id(account.subject)
        self._abort_if_unique_id_configured()
        self._account_name = account.display_name
        self._models = list(await self._client.async_list_models(access_token))
        if not self._models:
            raise SpaceXAISubscriptionError


class SpaceXAIEntitySubentryFlow(ConfigSubentryFlow):
    """Manage SpaceXAI entities."""

    options: dict[str, Any]

    @property
    def _is_new(self) -> bool:
        """Return whether an entity is being added."""
        return self.source == "user"

    @property
    def _is_conversation(self) -> bool:
        """Return whether this flow manages a conversation agent."""
        return self._subentry_type == "conversation"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add an entity."""
        self.options = (
            RECOMMENDED_CONVERSATION_OPTIONS.copy() if self._is_conversation else {}
        )
        return await self.async_step_init(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure an entity."""
        self.options = self._get_reconfigure_subentry().data.copy()
        return await self.async_step_init(user_input)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure an entity."""
        entry = self._get_entry()
        if entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        if user_input is not None:
            options = (
                _clean_conversation_options(user_input)
                if self._is_conversation
                else user_input
            )
            if self._is_new:
                return self.async_create_entry(
                    title=options.pop(CONF_NAME),
                    data=options,
                )
            return self.async_update_and_abort(
                entry,
                self._get_reconfigure_subentry(),
                data=options,
            )

        if self._is_conversation:
            hass_apis = [
                SelectOptionDict(label=api.name, value=api.id)
                for api in llm.async_get_apis(self.hass)
            ]
            schema = _conversation_schema(entry.runtime_data.models, hass_apis)
            default_name = DEFAULT_CONVERSATION_NAME
        else:
            schema = vol.Schema(
                {
                    vol.Required(CONF_MODEL): SelectSelector(
                        SelectSelectorConfig(
                            options=list(entry.runtime_data.models),
                            mode=SelectSelectorMode.DROPDOWN,
                            sort=True,
                        )
                    )
                }
            )
            default_name = DEFAULT_AI_TASK_NAME
        if self._is_new:
            schema = vol.Schema(
                {
                    vol.Required(CONF_NAME, default=default_name): str,
                    **schema.schema,
                }
            )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                schema,
                self.options,
            ),
        )


class SpaceXAISpeechSubentryFlow(ConfigSubentryFlow):
    """Manage SpaceXAI speech entities."""

    options: dict[str, Any]

    @property
    def _is_new(self) -> bool:
        """Return whether an entity is being added."""
        return self.source == "user"

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add a speech entity."""
        self.options = (
            {CONF_TTS_SPEED: RECOMMENDED_TTS_SPEED}
            if self._subentry_type == "tts"
            else {}
        )
        return await self.async_step_init(user_input)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Reconfigure a speech entity."""
        self.options = self._get_reconfigure_subentry().data.copy()
        return await self.async_step_init(user_input)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Configure a speech entity."""
        entry = self._get_entry()
        if entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="entry_not_loaded")

        if user_input is not None:
            options = self.options | user_input
            if self._is_new:
                return self.async_create_entry(
                    title=options.pop(CONF_NAME),
                    data=options,
                )
            return self.async_update_and_abort(
                entry,
                self._get_reconfigure_subentry(),
                data=options,
            )

        default_name = (
            DEFAULT_TTS_NAME if self._subentry_type == "tts" else DEFAULT_STT_NAME
        )
        schema: dict[vol.Marker, Any] = {}
        if self._is_new:
            schema[vol.Required(CONF_NAME, default=default_name)] = str
        if self._subentry_type == "tts":
            schema[vol.Optional(CONF_TTS_SPEED, default=RECOMMENDED_TTS_SPEED)] = (
                NumberSelector(NumberSelectorConfig(min=0.7, max=1.5, step=0.1))
            )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(schema),
                self.options,
            ),
        )
