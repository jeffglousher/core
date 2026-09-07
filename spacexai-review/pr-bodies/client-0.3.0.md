# Add structured responses and image generation

Prepare `spacexai-subscription-client 0.3.0`.

Add strict structured response formats, image generation, and editing with multiple reference images. The client returns typed image bytes and metadata while retaining caller-owned sessions and OAuth credentials.

Tests cover structured request formatting, image generation and editing, malformed image responses, and translated provider failures.

## Verification

- 121 tests pass locally on Python 3.14.5 with 97.93% statement coverage.
- [Public CI at the prepared commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34123467044) passes at `03bb0ee35e78df69f94c852e22887d4148fec0e4` on Python 3.12, 3.13, and 3.14.
- Ruff lint/format, strict MyPy, wheel and source builds, and strict Twine validation pass. CI independently installs and imports each artifact.

- All three Python jobs validate exact wheel/sdist contents, metadata, typing marker, license, and isolated imports. The count includes 28 release-contract tests.
- Release automation requires the exact release SHA to equal current `main`, a matching version tag, nonempty versioned changelog notes, and a successful exact-SHA three-Python matrix before the isolated publisher can run. Human review is a separate requirement; it is not inferred from ancestry or green CI.

## Release dependency

This layer follows 0.2.0. Publish it after that release and human review of this change. Version 0.3.0 has not been published; the matching Home Assistant layer must wait for publication and clean installation from PyPI.

- [Incremental source diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/spacexai/client-02-conversation...spacexai/client-03-image).
- [Changelog](https://github.com/jeffglousher/spacexai-subscription-client/blob/03bb0ee35e78df69f94c852e22887d4148fec0e4/CHANGELOG.md).
- [Publishing checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/03bb0ee35e78df69f94c852e22887d4148fec0e4/RELEASING.md). Follow the same verified workflow with version/tag `v0.3.0`.
