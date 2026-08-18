# Integration quality scale rules

Source: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules
Retrieved: 2026-08-15

## Bronze

* action-setup — Service actions are registered in async_setup
* appropriate-polling — If it's a polling integration, set an appropriate
  polling interval
* brands — Has branding assets available for the integration
* common-modules — Place common patterns in common modules
* config-flow-test-coverage — Full test coverage for the config flow
* config-flow — Integration needs to be able to be set up via the UI
* dependency-transparency — Dependency transparency
* docs-actions / docs-triggers / docs-conditions
* docs-high-level-description
* docs-installation-instructions / docs-removal-instructions
* entity-event-setup
* entity-unique-id
* has-entity-name
* runtime-data
* test-before-configure / test-before-setup
* unique-config-entry

## Silver

* action-exceptions
* config-entry-unloading
* docs-configuration-parameters / docs-installation-parameters
* entity-unavailable
* integration-owner
* log-when-unavailable
* parallel-updates
* reauthentication-flow
* test-coverage — Above 95% test coverage for all integration modules

## Gold

* devices / diagnostics
* discovery / discovery-update-info
* docs-data-update / docs-examples / docs-known-limitations
* docs-supported-devices / docs-supported-functions
* docs-troubleshooting / docs-use-cases
* dynamic-devices
* entity-category / entity-device-class / entity-disabled-by-default
* entity-translations / exception-translations / icon-translations
* reconfiguration-flow
* repair-issues
* stale-devices

## Platinum

* async-dependency
* inject-websession
* strict-typing
