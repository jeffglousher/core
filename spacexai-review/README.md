# SpaceXAI integration PR drafts

The complete descriptions below are posted to the three existing fork drafts
with your approval. Their contents were read back and verified. They focus on
the integration, its behavior, validation, and companion contributions.
Your approved review checkboxes are recorded; titles, branches, and draft status
are unchanged.

## Python package publication

[Library PR #2](https://github.com/jeffglousher/spacexai-subscription-client/pull/2)
is merged. [Release v0.1.1](https://github.com/jeffglousher/spacexai-subscription-client/releases/tag/v0.1.1)
targets `da47fd71fcb55012fbe182bb445ad36b81c60f51`, whose source tree matches the
reviewed candidate exactly. All required PR, merged-main, and release checks pass.

[PyPI 0.1.1](https://pypi.org/project/spacexai-subscription-client/0.1.1/) is published.
The [release run](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34304360439)
passed after your protected publication approval. The published wheel and source
distribution match the verified release artifacts. Post-publication source,
cryptographic provenance, and all six clean-install checks pass.
The [publication receipt](PACKAGE_RELEASE_0_1_1.json) records the verified sources.

Core's dependency-transparency rule is complete. [Published-dependency Core validation](https://github.com/jeffglousher/core/actions/runs/34312244846)
passes both jobs using the actual PyPI package: 50 tests, 100% statement coverage,
native setup and hooks, generated wiring, and hassfest with zero findings.
No local package substitute or publication exception is used.

## Core

**Title:** Add SpaceXAI conversation integration

[Open your existing draft #39](https://github.com/jeffglousher/core/pull/39)
with the posted [complete Core write-up](pr-bodies/core-01-initial.md).
Do not create a duplicate Core PR.

- Repository: `jeffglousher/core`.
- Base: `codex/spacexai/review-base-release-0-1`.
- Compare: `codex/spacexai/initial-release-0-1`.
- Scope: 18 changed files.
- Current source: `359b12ec6b6c327489c98654ee557f3861dc600a`.

## Brands

**Title:** Add SpaceXAI integration branding

[Open your Brands draft #1](https://github.com/jeffglousher/brands/pull/1)
with the posted [complete Brands write-up](pr-bodies/brands-01-initial.md).

- Repository: `jeffglousher/brands`.
- Base: `codex/spacexai/review-base`.
- Compare: `spacexai-initial`.
- Scope: eight PNG assets.
- Current source: `e3ac8da8bf579ec54210cc211e1eaa0768052679`.

## Documentation

**Title:** Document the SpaceXAI conversation integration

[Open your documentation draft #1](https://github.com/jeffglousher/home-assistant.io/pull/1)
with the posted [complete documentation write-up](pr-bodies/docs-01-initial.md).

- Repository: `jeffglousher/home-assistant.io`.
- Base: `codex/spacexai/review-base-release-0-1`.
- Compare: `codex/spacexai/docs-initial-release-0-1`.
- Scope: one integration page.
- Current source: `44526b046fa26d4ddf0ab037850a54e30ecbf1d0`.

## Submission details

These are review drafts on your forks. Do not merge them into the fixed review
bases. Before upstream submission, verify the released dependency and current
upstream compatibility. Preserve review history on the open Core PR.

All original template sections, comments, and checkbox labels remain intact.
The unchecked change-type alternatives and Core dependency-upgrade comparison
are inapplicable. The two-other-PRs box remains as you left it in draft #39.
The docs Brands-PR box stays open until an actual PR exists in
`home-assistant/brands`; a fork-only review draft does not complete that item.
The docs branch confirmation stays open for upstream submission to `next`;
the current fork draft intentionally targets its fixed review base.
The descriptions link to all three actual fork PRs.
