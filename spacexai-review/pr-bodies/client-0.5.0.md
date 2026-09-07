# Add deferred video generation

Prepare `spacexai-subscription-client 0.5.0`.

Add video generation from a text prompt and optional reference image. The client starts a job, waits within a fixed overall timeout, and returns the completed video URL and metadata for the caller to store or serve.

Tests cover pending and completed jobs, moderation, invalid job payloads, the overall timeout, and provider/transport failures. This layer includes the preceding release's complete, bounded speech-stream handling and its real-aiohttp regression tests.

## Verification

- Inherits the initial client's malformed-response and OAuth normalization repairs. Real-SDK transport regressions preserve provider-hosted outputs and mixed hosted/custom calls while rejecting local function calls that were not offered.
- 208 tests pass locally on Python 3.14.5 with 98.19% statement coverage.
- [Public CI at the prepared commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169834827) passes at `b6087bbd49428839cc4db845f0c5ec33ef3025fd` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

- All three Python jobs validate exact wheel/sdist contents, metadata, typing marker, license, and isolated imports. The count includes 28 release-contract tests.
- Release automation requires the exact release SHA to equal current `main`, a matching version tag, nonempty versioned changelog notes, and a successful exact-SHA three-Python matrix before the isolated publisher can run. Human review is a separate requirement; it is not inferred from ancestry or green CI.

## Release dependency

This layer follows 0.4.0. Publish it after that release and human review of this change. Version 0.5.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-04-speech...spacexai/client-05-video).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/b6087bbd49428839cc4db845f0c5ec33ef3025fd/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/b6087bbd49428839cc4db845f0c5ec33ef3025fd/RELEASING.md). Follow the same verified workflow with version/tag `v0.5.0`.
