# Add speech transcription and synthesis

Prepare `spacexai-subscription-client 0.4.0`.

Add batch audio transcription and speech synthesis with language, voice, speed, and output codec controls. Audio requests use the existing OAuth access token and shared HTTP session; the client normalizes results and provider errors.

Tests verify transcription and synthesis requests, supported output formats, response validation, size limits, and provider/transport failures. Synthesis reads the complete response through EOF within a bounded size. Four real-aiohttp stream regression cases verify delayed chunks, interrupted transfers, and cumulative size limits so partial audio is not returned as success.

## Verification

- 125 tests pass locally on Python 3.14.5 with 98.47% statement coverage.
- [Public CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34081007042) passes at `9133ea56b89e6b35081f2bb19826bb83088582c8` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

## Release dependency

This layer follows 0.3.0. Publish it after that release and human review of this change. Version 0.4.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-03-image...spacexai/client-04-speech).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/9133ea56b89e6b35081f2bb19826bb83088582c8/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/9133ea56b89e6b35081f2bb19826bb83088582c8/RELEASING.md). Follow the same verified workflow with version/tag `v0.4.0`.
