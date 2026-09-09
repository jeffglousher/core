# SpaceXAI integration submissions

The actual Home Assistant upstream drafts are created and cross-linked:

- [Core #181709](https://github.com/home-assistant/core/pull/181709), targeting `dev`, with the [complete Core write-up](upstream-pr-bodies/core-01-initial.md).
- [Brands #11129](https://github.com/home-assistant/brands/pull/11129), targeting `master`, with the [complete Brands write-up](upstream-pr-bodies/brands-01-initial.md).
- [Documentation #48027](https://github.com/home-assistant/home-assistant.io/pull/48027), targeting `next`, with the [complete documentation write-up](upstream-pr-bodies/docs-01-initial.md).

Each submission uses `codex/spacexai/upstream-initial` in its respective fork.
Review fixes are added as new commits, preserving the submitted history:

- Core: `d6b69cd9656e898d1e6ca6bf135f72ff38e6b05b`, based on `005d3fb369c3abf84a151c09d53f53cce27523d9`.
- Brands: `a82077c6aaafd2f1efd8872b41caf97f46f8d4cf`, based on `1a8f7ea2f5fb862db615fa5fcb78b9a70f29c579`.
- Documentation: `737c9022f862149f38e8cd380891aa72238bb97e`, based on `9ec3189633c7905570e5012d52200e9000054c68`.

Core validates the saved conversation model during setup and reports a translated
setup error when it is unavailable. Tests cover the error, recovery, and catalog
ordering; documentation explains recovery. The artwork is unchanged.
The linked write-ups reflect the verified validation below; checkbox states are unchanged.
The upstream PRs remain drafts; do not create duplicates.
The original fork drafts below remain unchanged staging records.

As of September 9, Core's updated [upstream CI](https://github.com/home-assistant/core/actions/runs/34347659004)
is running with no failures reported at this checkpoint. Its
[deterministic requirements check](https://github.com/home-assistant/core/actions/runs/34347658118) passes.
The independent fork validation below does not replace upstream CI or maintainer review.
Copilot reviewed the updated Core commit with no new inline comments, while explicitly
requesting final human validation of the OAuth and Assist control path. This is not
maintainer approval.

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

Core's dependency-transparency rule is complete. [Published-dependency Core validation](https://github.com/jeffglousher/core/actions/runs/34347124653)
passes both jobs using the actual PyPI package: 52 tests, 247/247 statements covered,
native setup and hooks, generated wiring, and hassfest with zero findings.
There are no test failures, errors, skips, or coverage exclusions. No local package
substitute or publication exception is used. This is native Linux CI verification;
the expanded suite was not rerun on the user's HA device, and no new live acceptance
or deployment is claimed.

[Companion validation](https://github.com/jeffglousher/core/actions/runs/34347046875)
passes the native documentation linters and prescribed Jekyll build, plus the
full Brands validator: 19,237 images checked with zero issues. This run tests only
the initial submissions; later documentation and blueprint validation require
an explicit opt-in.

## Core staging record

**Title:** Add SpaceXAI conversation integration

[Open your existing draft #39](https://github.com/jeffglousher/core/pull/39)
with the posted [complete Core write-up](pr-bodies/core-01-initial.md).
Do not create a duplicate Core PR.

- Repository: `jeffglousher/core`.
- Base: `codex/spacexai/review-base-release-0-1`.
- Compare: `codex/spacexai/initial-release-0-1`.
- Scope: 18 changed files.
- Current source: `359b12ec6b6c327489c98654ee557f3861dc600a`.

## Brands staging record

**Title:** Add SpaceXAI integration branding

[Open your Brands draft #1](https://github.com/jeffglousher/brands/pull/1)
with the posted [complete Brands write-up](pr-bodies/brands-01-initial.md).

- Repository: `jeffglousher/brands`.
- Base: `codex/spacexai/review-base`.
- Compare: `spacexai-initial`.
- Scope: eight PNG assets.
- Current source: `e3ac8da8bf579ec54210cc211e1eaa0768052679`.

## Documentation staging record

**Title:** Document the SpaceXAI conversation integration

[Open your documentation draft #1](https://github.com/jeffglousher/home-assistant.io/pull/1)
with the posted [complete documentation write-up](pr-bodies/docs-01-initial.md).

- Repository: `jeffglousher/home-assistant.io`.
- Base: `codex/spacexai/review-base-release-0-1`.
- Compare: `codex/spacexai/docs-initial-release-0-1`.
- Scope: one integration page.
- Current source: `44526b046fa26d4ddf0ab037850a54e30ecbf1d0`.

## Template and staging details

Do not merge the fork staging drafts into their fixed review bases. Preserve
the history of every open PR; the new submissions did not rewrite those branches.

All original template sections, comments, and checkbox labels remain intact.
The unchecked change-type alternatives and Core dependency-upgrade comparison
are inapplicable. The two-other-PRs box remains as you left it in draft #39.
The upstream documentation write-up checks both the Brands-PR and correct-branch
confirmations: Brands #11129 exists and documentation #48027 targets `next`.
The preserved staging descriptions retain their earlier fork links and checkbox
states. Use the upstream descriptions linked above for the current submissions.
