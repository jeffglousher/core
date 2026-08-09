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
# Speech/Imagine still use the developer API host with the same OAuth bearer.
API_BASE_URL = "https://cli-chat-proxy.grok.com/v1"
DEVELOPER_API_BASE_URL = "https://api.x.ai/v1"
IMAGES_URL = f"{DEVELOPER_API_BASE_URL}/images/generations"
STT_URL = f"{DEVELOPER_API_BASE_URL}/stt"
TTS_URL = f"{DEVELOPER_API_BASE_URL}/tts"

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
CONF_IMAGE_MODEL = "image_model"
CONF_VOICE = "voice"
CONF_TTS_SPEED = "tts_speed"

DEFAULT_CONVERSATION_NAME = "Grok"
DEFAULT_AI_TASK_NAME = "Grok AI Task"
DEFAULT_STT_NAME = "Grok STT"
DEFAULT_TTS_NAME = "Grok TTS"
DEFAULT_MAX_OUTPUT_TOKENS = 2048
DEFAULT_MODEL = "grok-4.5"
DEFAULT_MODEL_PLACEHOLDER = "Grok"
DEFAULT_WEB_SEARCH = False
DEFAULT_X_SEARCH = False
DEFAULT_CODE_INTERPRETER = False
DEFAULT_IMAGE_MODEL = "grok-imagine-image-quality"
DEFAULT_VOICE = "eve"
DEFAULT_TTS_SPEED = 1.0
HTTP_TIMEOUT_SECONDS = 30
IMAGE_TIMEOUT_SECONDS = 120
STT_TIMEOUT_SECONDS = 120
TTS_TIMEOUT_SECONDS = 60
MAX_TOOL_ITERATIONS = 10
RESPONSE_TIMEOUT = 300
DEVICE_CODE_MAX_POLL_SECONDS = 900
PROVIDER_WEB_SEARCH_TOOL = "web_search_call"
PROVIDER_X_SEARCH_TOOL = "x_search_call"
PROVIDER_CODE_INTERPRETER_TOOL = "code_interpreter"
PROVIDER_SEARCH_TOOLS = frozenset({PROVIDER_WEB_SEARCH_TOOL, PROVIDER_X_SEARCH_TOOL})
IMAGE_MODELS = (
    "grok-imagine-image-quality",
    "grok-imagine-image",
)
TTS_VOICES = (
    ("eve", "Eve"),
    ("ara", "Ara"),
    ("rex", "Rex"),
    ("sal", "Sal"),
    ("leo", "Leo"),
    ("luna", "Luna"),
    ("orion", "Orion"),
    ("atlas", "Atlas"),
    ("iris", "Iris"),
    ("helix", "Helix"),
    ("carina", "Carina"),
    ("altair", "Altair"),
    ("zenith", "Zenith"),
    ("perseus", "Perseus"),
    ("helios", "Helios"),
    ("lux", "Lux"),
    ("kepler", "Kepler"),
    ("rigel", "Rigel"),
    ("cosmo", "Cosmo"),
    ("celeste", "Celeste"),
    ("ursa", "Ursa"),
    ("sirius", "Sirius"),
    ("lumen", "Lumen"),
    ("castor", "Castor"),
    ("naksh", "Naksh"),
    ("zagan", "Zagan"),
)
STT_LANGUAGES = (
    "ar-SA",
    "cs-CZ",
    "da-DK",
    "de-DE",
    "en-US",
    "es-ES",
    "fa-IR",
    "fil-PH",
    "fr-FR",
    "hi-IN",
    "id-ID",
    "it-IT",
    "ja-JP",
    "ko-KR",
    "mk-MK",
    "ms-MY",
    "nl-NL",
    "pl-PL",
    "pt-PT",
    "ro-RO",
    "ru-RU",
    "sv-SE",
    "th-TH",
    "tr-TR",
    "vi-VN",
)
TTS_LANGUAGES = (
    "en",
    "ar-EG",
    "ar-SA",
    "ar-AE",
    "bn",
    "zh",
    "fr",
    "de",
    "hi",
    "id",
    "it",
    "ja",
    "ko",
    "pt-BR",
    "pt-PT",
    "ru",
    "es-MX",
    "es-ES",
    "tr",
    "vi",
)
