# Add deferred video generation

Prepare `spacexai-subscription-client 0.5.0`.

Add video generation from a text prompt and optional reference image. The client starts a job, waits within a fixed overall timeout, and returns the completed video URL and metadata for the caller to store or serve.

Tests cover pending and completed jobs, moderation, invalid job payloads, the overall timeout, and provider/transport failures. This layer includes the preceding release's complete, bounded speech-stream handling and its real-aiohttp regression tests.

## Verification

- Inherits the initial client's malformed-response and OAuth normalization repairs. Real-SDK transport regressions preserve provider-hosted outputs and mixed hosted/custom calls while rejecting local function calls that were not offered.
- 216 tests pass locally on Python 3.14.5 with 98.19% statement coverage.
- [Public CI at the prepared commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992203) passes at `f58ec77aebff01fe6bf4b72e97a2370b023647a2` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

- All three Python jobs validate the wheel member set, required wheel/sdist source bytes, release identity, typing marker, license, and isolated imports. The count includes 36 release-contract tests. Extra or duplicate wheel members are rejected; the sdist check is not a universal archive-security audit.
- Release automation requires the exact release SHA to equal current `main` at preflight, a matching version tag, nonempty versioned changelog notes, and a successful exact-SHA three-Python matrix before the isolated publisher can run. Human review is a separate requirement; it is not inferred from ancestry or green CI.

## Release dependency

The shared GitHub publishing controls are configured, but current `main` still has the legacy workflow until the reviewed initial package is merged. Genuine human review, private PyPI account/publisher verification, and publication approval remain required; the prepared branch's green CI does not replace them.

This layer follows 0.4.0. Publish it after that release and human review of this change. Version 0.5.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-04-speech...spacexai/client-05-video).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/f58ec77aebff01fe6bf4b72e97a2370b023647a2/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/f58ec77aebff01fe6bf4b72e97a2370b023647a2/RELEASING.md). Follow the same verified workflow with version/tag `v0.5.0`.
