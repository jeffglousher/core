"""Constants for the SpaceXAI integration."""

from logging import Logger, getLogger

DOMAIN = "spacexai"
LOGGER: Logger = getLogger(__package__)

AUTHORIZE_URL = "https://auth.x.ai/oauth2/authorize"
TOKEN_URL = "https://auth.x.ai/oauth2/token"
USERINFO_URL = "https://auth.x.ai/oauth2/userinfo"
REVOCATION_URL = "https://auth.x.ai/oauth2/revoke"
DEVICE_CODE_URL = "https://auth.x.ai/oauth2/device/code"
# Subscription OAuth (Grok CLI / Hermes-compatible) uses the CLI chat proxy.
# The developer API at api.x.ai rejects subscription bearers with 402/403.
API_BASE_URL = "https://cli-chat-proxy.grok.com/v1"

# Public Grok CLI OAuth client id used by Hermes/OpenCode device-code login.
GROK_CLI_OAUTH_CLIENT_ID = "b1a00492-073a-47ea-816f-4c329264a828"
# Identity headers required by cli-chat-proxy.grok.com for subscription tokens.
GROK_CLI_REQUEST_HEADERS = {
    "Accept": "application/json",
    "User-Agent": "xai-grok-cli",
    "x-xai-token-auth": "xai-grok-cli",
    "x-grok-client-identifier": "grok-shell",
    "x-grok-client-version": "0.2.103",
}

# Scopes accepted by the public Grok CLI OAuth client for device-code login.
# conversations:* are required by the CLI chat proxy (Hermes/shunt).
OAUTH_SCOPES = (
    "openid",
    "profile",
    "email",
    "offline_access",
    "grok-cli:access",
    "api:access",
    "conversations:read",
    "conversations:write",
)

CONF_MAX_OUTPUT_TOKENS = "max_output_tokens"
CONF_WEB_SEARCH = "web_search"
CONF_X_SEARCH = "x_search"
CONF_CODE_INTERPRETER = "code_interpreter"

DEFAULT_CONVERSATION_NAME = "Grok"
DEFAULT_AI_TASK_NAME = "Grok AI Task"
DEFAULT_MAX_OUTPUT_TOKENS = 2048
DEFAULT_MODEL = "grok-4.5"
DEFAULT_MODEL_PLACEHOLDER = "Grok"
DEFAULT_WEB_SEARCH = False
DEFAULT_X_SEARCH = False
DEFAULT_CODE_INTERPRETER = False
HTTP_TIMEOUT_SECONDS = 30
MAX_TOOL_ITERATIONS = 10
RESPONSE_TIMEOUT = 300
DEVICE_CODE_MAX_POLL_SECONDS = 900
PROVIDER_WEB_SEARCH_TOOL = "web_search_call"
PROVIDER_X_SEARCH_TOOL = "x_search_call"
PROVIDER_CODE_INTERPRETER_TOOL = "code_interpreter"
PROVIDER_SEARCH_TOOLS = frozenset({PROVIDER_WEB_SEARCH_TOOL, PROVIDER_X_SEARCH_TOOL})
