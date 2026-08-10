"""Attachment encoding helpers for SpaceXAI prompts."""

import base64
from mimetypes import guess_type as guess_file_type
from pathlib import Path

from openai.types.responses.response_input_file_param import ResponseInputFileParam
from openai.types.responses.response_input_image_param import ResponseInputImageParam
from openai.types.responses.response_input_message_content_list_param import (
    ResponseInputMessageContentListParam,
)

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN, MAX_ATTACHMENT_BYTES


async def async_prepare_files_for_prompt(
    hass: HomeAssistant, files: list[tuple[Path, str | None]]
) -> ResponseInputMessageContentListParam:
    """Encode local attachments for a multimodal user message."""

    def append_files_to_content() -> ResponseInputMessageContentListParam:
        content: ResponseInputMessageContentListParam = []

        for file_path, mime_type in files:
            if not file_path.exists():
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="attachment_not_found",
                    translation_placeholders={"path": str(file_path)},
                )

            if mime_type is None:
                mime_type = guess_file_type(file_path)[0]

            if not mime_type or not mime_type.startswith(("image/", "application/pdf")):
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="attachment_unsupported_type",
                    translation_placeholders={"path": str(file_path)},
                )

            size = file_path.stat().st_size
            if size > MAX_ATTACHMENT_BYTES:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="attachment_too_large",
                    translation_placeholders={
                        "path": file_path.name,
                        "max_mb": str(MAX_ATTACHMENT_BYTES // (1024 * 1024)),
                    },
                )

            base64_file = base64.b64encode(file_path.read_bytes()).decode("utf-8")

            if mime_type.startswith("image/"):
                content.append(
                    ResponseInputImageParam(
                        type="input_image",
                        image_url=f"data:{mime_type};base64,{base64_file}",
                        detail="auto",
                    )
                )
            elif mime_type.startswith("application/pdf"):
                content.append(
                    ResponseInputFileParam(
                        type="input_file",
                        filename=file_path.name,
                        file_data=f"data:{mime_type};base64,{base64_file}",
                    )
                )

        return content

    return await hass.async_add_executor_job(append_files_to_content)
