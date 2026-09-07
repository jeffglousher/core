# Add conversation attachments and provider tools

Prepare `spacexai-subscription-client 0.2.0`.

Allow applications to send JPEG/PNG images and PDF attachments with user messages, and opt into provider-hosted web search, X search, or code execution. Local function tools remain available alongside the selected provider tools.

Tests verify attachment encoding, supported provider-tool payloads, and existing OAuth, conversation, and error behavior.

## Verification

- 65 tests pass locally on Python 3.14.5 with 96.93% statement coverage.
- [Public CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34078363848) passes at `25952c5f839a30cd26e374d1eae6408fa46392c1` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

## Release dependency

This layer follows 0.1.0. Publish it after that release and human review of this change. Version 0.2.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/harden-initial-release...spacexai/client-02-conversation).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/25952c5f839a30cd26e374d1eae6408fa46392c1/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/25952c5f839a30cd26e374d1eae6408fa46392c1/RELEASING.md). Follow the same verified workflow with version/tag `v0.2.0`.
