# Style guidelines

Source: https://developers.home-assistant.io/docs/development_guidelines
Retrieved: 2026-08-15

Home Assistant enforces PEP8 and PEP 257. Ruff formats every pull request.

* Comments should be full sentences and end with a period.
* Imports should be ordered.
* Constants and the content of lists and dictionaries should be in
  alphabetical order.

## File headers

The docstring in the file header should describe what the file is about.

## Log messages

Do not add the platform or component name. Do not end log messages with a
period. Do not print API keys, tokens, usernames, or passwords. Prefer
`_LOGGER.debug` over `_LOGGER.info` for non-user targeting.

## String formatting

Prefer f-strings except for logging, which uses percentage formatting so
suppressed messages are not formatted.

## Typing

Fully type code. Modules can be added to `.strict-typing` when complete.
Use `assert` inside `TYPE_CHECKING` only to narrow types.

## Function docstring convention

Type annotations document parameters. When extended docs are needed, use
Google style and omit types already in annotations.
