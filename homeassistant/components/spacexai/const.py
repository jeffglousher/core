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
IMAGES_EDIT_URL = f"{DEVELOPER_API_BASE_URL}/images/edits"
VIDEOS_URL = f"{DEVELOPER_API_BASE_URL}/videos/generations"
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

CONF_RECOMMENDED = "recommended"
CONF_MODEL_CUSTOM = "model_custom"
# Sentinel select value that reveals the manual model text field.
MODEL_CUSTOM_OPTION = "__custom__"

CONF_MAX_OUTPUT_TOKENS = "max_output_tokens"
CONF_TEMPERATURE = "temperature"
CONF_TOP_P = "top_p"
CONF_STORE_RESPONSES = "store_responses"
CONF_SERVICE_TIER = "service_tier"
SERVICE_TIER_DEFAULT = "default"
SERVICE_TIER_PRIORITY = "priority"
SERVICE_TIERS = (SERVICE_TIER_DEFAULT, SERVICE_TIER_PRIORITY)
CONF_WEB_SEARCH = "web_search"
CONF_X_SEARCH = "x_search"
CONF_CODE_INTERPRETER = "code_interpreter"
CONF_IMAGE_GENERATION = "image_generation"
CONF_IMAGE_GENERATION_ACTION = "image_generation_action"
CONF_ALLOW_CONTROL_WITH_PROVIDER_TOOLS = "allow_control_with_provider_tools"
CONF_WEB_SEARCH_ALLOWED_DOMAINS = "web_search_allowed_domains"
CONF_WEB_SEARCH_EXCLUDED_DOMAINS = "web_search_excluded_domains"
CONF_WEB_SEARCH_IMAGE_UNDERSTANDING = "web_search_image_understanding"
CONF_WEB_SEARCH_IMAGE_SEARCH = "web_search_image_search"
CONF_X_SEARCH_ALLOWED_HANDLES = "x_search_allowed_handles"
CONF_X_SEARCH_EXCLUDED_HANDLES = "x_search_excluded_handles"
CONF_X_SEARCH_FROM_DATE = "x_search_from_date"
CONF_X_SEARCH_TO_DATE = "x_search_to_date"
CONF_X_SEARCH_IMAGE_UNDERSTANDING = "x_search_image_understanding"
CONF_X_SEARCH_VIDEO_UNDERSTANDING = "x_search_video_understanding"
CONF_IMAGE_MODEL = "image_model"
CONF_IMAGE_ASPECT_RATIO = "image_aspect_ratio"
CONF_IMAGE_RESOLUTION = "image_resolution"
CONF_CREATE_STT = "create_stt"
CONF_CREATE_TTS = "create_tts"
CONF_DEFAULT_ASSIST = "default_assist"
CONF_VOICE = "voice"
CONF_TTS_SPEED = "tts_speed"

DEFAULT_CONVERSATION_NAME = "Grok"
DEFAULT_AI_TASK_NAME = "Grok AI Task"
DEFAULT_STT_NAME = "Grok STT"
DEFAULT_TTS_NAME = "Grok TTS"
# Align with openai_conversation Assist ceiling; responses can still be short.
DEFAULT_MAX_OUTPUT_TOKENS = 3000
# Higher ceiling for structured AI Task output (schemas, longer drafts).
DEFAULT_AI_TASK_MAX_OUTPUT_TOKENS = 8192
# Match xAI / openai_conversation sampling defaults (provider default is 1.0).
DEFAULT_TEMPERATURE = 1.0
DEFAULT_TOP_P = 1.0
DEFAULT_STORE_RESPONSES = False
# xAI Priority Processing: request body service_tier="priority" (not a header).
# Assist/conversation defaults to priority; AI Task stays on standard tier.
DEFAULT_SERVICE_TIER = SERVICE_TIER_PRIORITY
DEFAULT_AI_TASK_SERVICE_TIER = SERVICE_TIER_DEFAULT
DEFAULT_MODEL = "grok-4.5"
DEFAULT_MODEL_PLACEHOLDER = "Grok"
DEFAULT_WEB_SEARCH = False
DEFAULT_X_SEARCH = False
DEFAULT_CODE_INTERPRETER = False
DEFAULT_IMAGE_GENERATION = False
DEFAULT_IMAGE_GENERATION_ACTION = "auto"
DEFAULT_ALLOW_CONTROL_WITH_PROVIDER_TOOLS = False
DEFAULT_WEB_SEARCH_IMAGE_SEARCH = False
DEFAULT_X_SEARCH_VIDEO_UNDERSTANDING = False
DEFAULT_IMAGE_MODEL = "grok-imagine-image-quality"
DEFAULT_VIDEO_MODEL = "grok-imagine-video-1.5"
DEFAULT_IMAGE_ASPECT_RATIO = "1:1"
DEFAULT_IMAGE_RESOLUTION = "1k"
DEFAULT_CREATE_STT = True
DEFAULT_CREATE_TTS = True
DEFAULT_DEFAULT_ASSIST = True
DEFAULT_VOICE = "eve"
DEFAULT_TTS_SPEED = 1.0
HTTP_TIMEOUT_SECONDS = 30
IMAGE_TIMEOUT_SECONDS = 120
VIDEO_TIMEOUT_SECONDS = 300
STT_TIMEOUT_SECONDS = 120
TTS_TIMEOUT_SECONDS = 60
MAX_TOOL_ITERATIONS = 10
MAX_AI_TASK_TOOL_ITERATIONS = 1000
RESPONSE_TIMEOUT = 300
RESPONSE_IDLE_TIMEOUT = 300
DEVICE_CODE_MAX_POLL_SECONDS = 900
MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
MAX_STT_AUDIO_BYTES = 25 * 1024 * 1024
MAX_IMAGE_BYTES = 20 * 1024 * 1024
MAX_IMAGE_COUNT = 10
PROVIDER_WEB_SEARCH_TOOL = "web_search_call"
PROVIDER_X_SEARCH_TOOL = "x_search_call"
PROVIDER_CODE_INTERPRETER_TOOL = "code_interpreter"
PROVIDER_SEARCH_TOOLS = frozenset({PROVIDER_WEB_SEARCH_TOOL, PROVIDER_X_SEARCH_TOOL})
IMAGE_MODELS = (
    "grok-imagine-image-quality",
    "grok-imagine-image",
)
VIDEO_MODELS = (
    "grok-imagine-video-1.5",
    "grok-imagine-video",
)
IMAGE_ASPECT_RATIOS = (
    "1:1",
    "3:2",
    "2:3",
    "16:9",
    "9:16",
)
IMAGE_RESOLUTIONS = (
    "1k",
    "2k",
)
IMAGE_GENERATION_ACTIONS = (
    "auto",
    "generate",
    "edit",
)
SERVICE_GENERATE_VIDEO = "generate_video"
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
