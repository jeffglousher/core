"""Validate the documentation blueprint without running any actions."""

import argparse
import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from homeassistant.components.automation.config import (
    AUTOMATION_BLUEPRINT_SCHEMA,
    PLATFORM_SCHEMA,
)
from homeassistant.components.blueprint.errors import MissingInput
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.components.homeassistant.triggers.time import TRIGGER_SCHEMA
from homeassistant.const import __version__
from homeassistant.core import HomeAssistant
from homeassistant.helpers.selector import selector
from homeassistant.helpers.template import Template
from homeassistant.util import yaml as yaml_util


async def async_validate(config_dir: str) -> None:
    """Check metadata, inputs, expanded automation, and response templating."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blueprint", type=Path)
    args = parser.parse_args()
    hass = HomeAssistant(config_dir)
    blueprint = Blueprint(
        yaml_util.load_yaml_dict(args.blueprint),
        expected_domain="automation",
        schema=AUTOMATION_BLUEPRINT_SCHEMA,
    )
    assert set(blueprint.inputs) == {"media", "notification_time"}
    cases = (
        (
            {
                "media_content_id": "media-source://media_source/local/example.png",
                "media_content_type": "image/png",
            },
            None,
            "18:00:00",
        ),
        (
            {
                "media_content_id": "media-source://media_source/local/example.mp4",
                "media_content_type": "video/mp4",
            },
            "06:30:00",
            "06:30:00",
        ),
    )
    for media, selected_time, expected_time in cases:
        inputs = {"media": media}
        if selected_time is not None:
            inputs["notification_time"] = selected_time
        instance = BlueprintInputs(
            blueprint,
            {"use_blueprint": {"path": args.blueprint.name, "input": inputs}},
        )
        instance.validate()
        for name, value in instance.inputs_with_default.items():
            selector(blueprint.inputs[name]["selector"])(value)
        expanded = instance.async_substitute()
        assert not yaml_util.extract_inputs(expanded)
        assert expanded["triggers"] == [{"trigger": "time", "at": expected_time}]
        assert [action["action"] for action in expanded["actions"]] == [
            "spacexai.publish_media",
            "persistent_notification.create",
        ]
        assert expanded["actions"][0]["data"] == {"media": media}
        assert expanded["actions"][0]["response_variable"] == "published_media"
        automation = PLATFORM_SCHEMA(expanded)
        TRIGGER_SCHEMA(automation["triggers"][0])
        message = Template(expanded["actions"][1]["data"]["message"], hass)
        message.ensure_valid()
        assert (
            message.async_render(
                {"published_media": {"url": "/media/example.mp4?authSig=example"}},
                parse_result=False,
            )
            == "[Open media](/media/example.mp4?authSig=example)"
        )
    try:
        BlueprintInputs(
            blueprint,
            {"use_blueprint": {"path": args.blueprint.name, "input": {}}},
        ).validate()
    except MissingInput:
        pass
    else:
        raise AssertionError("The blueprint must require a selected local media file")
    print(
        json.dumps(
            {
                "blueprint": args.blueprint.name,
                "homeassistant": __version__,
                "valid_cases": len(cases),
                "missing_media_rejected": True,
                "actions_executed": 0,
            }
        )
    )


if __name__ == "__main__":
    with TemporaryDirectory(prefix="spacexai-blueprint-validation-") as config_dir:
        asyncio.run(async_validate(config_dir))
