# Integration manifest

Source: https://developers.home-assistant.io/docs/creating_integration_manifest
Retrieved: 2026-08-15

Every integration has `manifest.json`. Required keys include `domain`,
`name`, `documentation`, `integration_type`, and `iot_class`.

## Name

Cloud-only variants of a product that also has a local integration append
"Cloud". Do not append "Local". Inherently cloud products use the name
as-is.

## Version

For core integrations, omit `version`. Custom integrations must include a
valid AwesomeVersion version.

## Integration type

`device`, `entity`, `hardware`, `helper`, `hub`, `service`, `system`,
`virtual`. SpaceXAI is a `service`.

## Documentation

Core submissions use `https://www.home-assistant.io/integrations/<domain>`.

## Issue tracker

Omit for built-in integrations.

## Requirements

Pinned pip-compatible strings. New dependencies must also land in
`requirements_all.txt` via `script.gen_requirements_all`.

## Quality scale

New integrations must fulfill at least bronze. Declaring a scale requires
every rule at that tier to be `done` or `exempt`.

## IoT class

Accepted values: `assumed_state`, `cloud_polling`, `cloud_push`,
`local_polling`, `local_push`, `calculated`.
