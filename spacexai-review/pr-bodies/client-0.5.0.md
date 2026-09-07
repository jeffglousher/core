# Add deferred video generation

Prepare `spacexai-subscription-client 0.5.0`.

Add video generation from a text prompt and optional reference image. The client starts a job, waits within a fixed overall timeout, and returns the completed video URL and metadata for the caller to store or serve.

Tests cover pending and completed jobs, moderation, invalid job payloads, the overall timeout, and provider/transport failures. This layer includes the preceding release's complete, bounded speech-stream handling and its real-aiohttp regression tests.

## Verification

- 154 tests pass locally on Python 3.14.5 with 98.17% statement coverage.
- [Public CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34081006987) passes at `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

## Release dependency

This layer follows 0.4.0. Publish it after that release and human review of this change. Version 0.5.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-04-speech...spacexai/client-05-video).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c/RELEASING.md). Follow the same verified workflow with version/tag `v0.5.0`.
