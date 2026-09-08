# Add conversation attachments and provider tools

Prepare `spacexai-subscription-client 0.2.0`.

Allow applications to send JPEG/PNG images and PDF attachments with user messages, and opt into provider-hosted web search, X search, or code execution. Local function tools remain available alongside the selected provider tools.

Tests verify attachment encoding, supported provider-tool payloads, and existing OAuth, conversation, and error behavior.

## Verification

- Inherits the initial client's malformed-response and OAuth normalization repairs. Real-SDK transport regressions preserve provider-hosted outputs and mixed hosted/custom calls while rejecting local function calls that were not offered.
- 127 tests pass locally on Python 3.14.5 with 96.99% statement coverage.
- [Public CI at the prepared commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992495) passes at `fc13749a2d9befa62b9581ccd4e3a60a9ef3c54e` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

- All three Python jobs validate the wheel member set, required wheel/sdist source bytes, release identity, typing marker, license, and isolated imports. The count includes 36 release-contract tests. Extra or duplicate wheel members are rejected; the sdist check is not a universal archive-security audit.
- Release automation requires the exact release SHA to equal current `main` at preflight, a matching version tag, nonempty versioned changelog notes, and a successful exact-SHA three-Python matrix before the isolated publisher can run. Human review is a separate requirement; it is not inferred from ancestry or green CI.

## Release dependency

The shared GitHub publishing controls are configured, but current `main` still has the legacy workflow until the reviewed initial package is merged. Genuine human review, private PyPI account/publisher verification, and publication approval remain required; the prepared branch's green CI does not replace them.

This layer follows 0.1.0. Publish it after that release and human review of this change. Version 0.2.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/harden-initial-release...spacexai/client-02-conversation).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/fc13749a2d9befa62b9581ccd4e3a60a9ef3c54e/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/fc13749a2d9befa62b9581ccd4e3a60a9ef3c54e/RELEASING.md). Follow the same verified workflow with version/tag `v0.2.0`.
