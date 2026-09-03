"""Constants for the SpaceXAI integration."""

from logging import Logger, getLogger

from homeassistant.const import CONF_LLM_HASS_API, CONF_PROMPT
from homeassistant.helpers import llm

DOMAIN = "spacexai"
LOGGER: Logger = getLogger(__package__)

DEFAULT_CONVERSATION_NAME = "Grok"
DEFAULT_AI_TASK_NAME = "Grok AI Task"
RECOMMENDED_IMAGE_MODEL = "grok-imagine-image-2.0"
MAX_TOOL_ITERATIONS = 10
MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024

CONF_CODE_INTERPRETER = "code_interpreter"
CONF_WEB_SEARCH = "web_search"
CONF_X_SEARCH = "x_search"

RECOMMENDED_CONVERSATION_OPTIONS = {
    CONF_CODE_INTERPRETER: False,
    CONF_LLM_HASS_API: [llm.LLM_API_ASSIST],
    CONF_PROMPT: llm.DEFAULT_INSTRUCTIONS_PROMPT,
    CONF_WEB_SEARCH: False,
    CONF_X_SEARCH: False,
}
