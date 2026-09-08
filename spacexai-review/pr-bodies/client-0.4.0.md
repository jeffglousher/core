# Add speech transcription and synthesis

Prepare `spacexai-subscription-client 0.4.0`.

Add batch audio transcription and speech synthesis with language, voice, speed, and output codec controls. Audio requests use the existing OAuth access token and shared HTTP session; the client normalizes results and provider errors.

Tests verify transcription and synthesis requests, supported output formats, response validation, size limits, and provider/transport failures. Synthesis reads the complete response through EOF within a bounded size. Four real-aiohttp stream regression cases verify delayed chunks, interrupted transfers, and cumulative size limits so partial audio is not returned as success.

## Verification

- Inherits the initial client's malformed-response and OAuth normalization repairs. Real-SDK transport regressions preserve provider-hosted outputs and mixed hosted/custom calls while rejecting local function calls that were not offered.
- 187 tests pass locally on Python 3.14.5 with 98.49% statement coverage.
- [Public CI at the prepared commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992423) passes at `b6b1d7d301b66bd29e24d2c0c309fa3e775f9881` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

- All three Python jobs validate the wheel member set, required wheel/sdist source bytes, release identity, typing marker, license, and isolated imports. The count includes 36 release-contract tests. Extra or duplicate wheel members are rejected; the sdist check is not a universal archive-security audit.
- Release automation requires the exact release SHA to equal current `main` at preflight, a matching version tag, nonempty versioned changelog notes, and a successful exact-SHA three-Python matrix before the isolated publisher can run. Human review is a separate requirement; it is not inferred from ancestry or green CI.

## Release dependency

The shared GitHub publishing controls are configured, but current `main` still has the legacy workflow until the reviewed initial package is merged. Genuine human review, private PyPI account/publisher verification, and publication approval remain required; the prepared branch's green CI does not replace them.

This layer follows 0.3.0. Publish it after that release and human review of this change. Version 0.4.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-03-image...spacexai/client-04-speech).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/b6b1d7d301b66bd29e24d2c0c309fa3e775f9881/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/b6b1d7d301b66bd29e24d2c0c309fa3e775f9881/RELEASING.md). Follow the same verified workflow with version/tag `v0.4.0`.
