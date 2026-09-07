# Add conversation attachments and provider tools

Prepare `spacexai-subscription-client 0.2.0`.

Allow applications to send JPEG/PNG images and PDF attachments with user messages, and opt into provider-hosted web search, X search, or code execution. Local function tools remain available alongside the selected provider tools.

Tests verify attachment encoding, supported provider-tool payloads, and existing OAuth, conversation, and error behavior.

## Verification

- 93 tests pass locally on Python 3.14.5 with 96.93% statement coverage.
- [Public CI at the prepared commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34123471193) passes at `72b9275207521580215c681597a2da20a7c9ff83` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

- All three Python jobs validate exact wheel/sdist contents, metadata, typing marker, license, and isolated imports. The count includes 28 release-contract tests.
- Release automation requires the exact release SHA to equal current `main`, a matching version tag, nonempty versioned changelog notes, and a successful exact-SHA three-Python matrix before the isolated publisher can run. Human review is a separate requirement; it is not inferred from ancestry or green CI.

## Release dependency

This layer follows 0.1.0. Publish it after that release and human review of this change. Version 0.2.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/harden-initial-release...spacexai/client-02-conversation).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/72b9275207521580215c681597a2da20a7c9ff83/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/72b9275207521580215c681597a2da20a7c9ff83/RELEASING.md). Follow the same verified workflow with version/tag `v0.2.0`.
