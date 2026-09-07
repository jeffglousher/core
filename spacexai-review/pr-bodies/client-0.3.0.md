# Add structured responses and image generation

Prepare `spacexai-subscription-client 0.3.0`.

Add strict structured response formats, image generation, and editing with multiple reference images. The client returns typed image bytes and metadata while retaining caller-owned sessions and OAuth credentials.

Tests cover structured request formatting, image generation and editing, malformed image responses, and translated provider failures.

## Verification

- 93 tests pass locally on Python 3.14.5 with 97.93% statement coverage.
- [Public CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34078363629) passes at `80e36af0863d5b31742fddd6edd0ccdb306f1bcc` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

## Release dependency

This layer follows 0.2.0. Publish it after that release and human review of this change. Version 0.3.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-02-conversation...spacexai/client-03-image).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/80e36af0863d5b31742fddd6edd0ccdb306f1bcc/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/80e36af0863d5b31742fddd6edd0ccdb306f1bcc/RELEASING.md). Follow the same verified workflow with version/tag `v0.3.0`.
