"""Constants for the SpaceXAI integration."""

from logging import Logger, getLogger

DOMAIN = "spacexai"
LOGGER: Logger = getLogger(__package__)

AUTHORIZE_URL = "https://auth.x.ai/oauth2/authorize"
TOKEN_URL = "https://auth.x.ai/oauth2/token"
USERINFO_URL = "https://auth.x.ai/oauth2/userinfo"
REVOCATION_URL = "https://auth.x.ai/oauth2/revoke"
DEVICE_CODE_URL = "https://auth.x.ai/oauth2/device/code"
API_BASE_URL = "https://api.x.ai/v1"

# SpaceXAI currently requires both scopes for subscription-backed api.x.ai
# access from third-party OAuth clients. Keep both until a Home Assistant
# specific scope set is assigned.
OAUTH_SCOPES = (
    "openid",
    "profile",
    "email",
    "offline_access",
    "grok-cli:access",
    "api:access",
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
PROVIDER_WEB_SEARCH_TOOL = "web_search_call"
PROVIDER_X_SEARCH_TOOL = "x_search_call"
PROVIDER_CODE_INTERPRETER_TOOL = "code_interpreter"
PROVIDER_SEARCH_TOOLS = frozenset({PROVIDER_WEB_SEARCH_TOOL, PROVIDER_X_SEARCH_TOOL})
