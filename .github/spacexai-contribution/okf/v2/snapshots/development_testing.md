# Testing your code

Source: https://developers.home-assistant.io/docs/development_testing
Retrieved: 2026-08-15

All unit tests must pass. All code must pass linting.

Local testing uses pytest and prek (`prek run --all-files`).

Run at least the tests related to your changes before opening a PR.

## Writing tests for integrations

Do not interact with integration internals. Follow this pattern:

* Set up the integration with `async_setup_component` or
  `hass.config_entries.async_setup`.
* Assert entity state via `hass.states`.
* Perform service action calls via `hass.services`.
* Assert `DeviceEntry` via the device registry.
* Assert entity registry `RegistryEntry` via the entity registry.
* Modify a `ConfigEntry` via `hass.config_entries`.
* Assert config entry state via `ConfigEntry.state`.
* Mock a config entry via `MockConfigEntry` in `tests/common.py`.

## Snapshot testing

Syrupy `.ambr` snapshots are for large outputs. They do not replace
functional tests. Prefer asserting the specific state change you care
about.

## Linters

`prek run --show-diff-on-failure`. If a PyLint warning is unavoidable, add
`# pylint: disable=YOUR-ERROR-NAME` on that line.
