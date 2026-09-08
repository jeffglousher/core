# SpaceXAI first-wave review packet

Current packet: September 8, 2026. Python 0.1.0 is published and verified.
The remaining contributions are initial Core, Brands, and documentation.
These are prepared for human review on your forks; no companion PR was opened.

OAuth device authorization remains the only login path. There is no API-key
fallback or runtime Grok CLI dependency.

## Completed: Python 0.1.0

[Package PR #1](https://github.com/jeffglousher/spacexai-subscription-client/pull/1)
is merged. [Release v0.1.0](https://github.com/jeffglousher/spacexai-subscription-client/releases/tag/v0.1.0)
and [PyPI 0.1.0](https://pypi.org/project/spacexai-subscription-client/0.1.0/)
come from `155d76c5b940108be707bb379c02d476b893b758`, whose tree exactly matches
the reviewed source. Both distribution files passed source-byte and cryptographic
attestation checks; all six clean wheel/sdist installations passed on Python
3.12–3.14. [Publication evidence](PACKAGE_REPAIR_EVIDENCE.md) records the scope.

Do not create the library draft again or republish 0.1.0.

## Create the three companion fork drafts

Read and understand each write-up first. Run these commands from the
`codex/spacexai-validation` checkout containing `spacexai-review/`.
They target only your repositories and have not been executed.

1. **Add SpaceXAI conversation integration** — [write-up](pr-bodies/core-01-initial.md), [preview](https://github.com/jeffglousher/core/compare/codex/spacexai/review-base-release-0-1...codex/spacexai/initial-release-0-1).

   ```shell
   gh pr create --draft --repo jeffglousher/core --base codex/spacexai/review-base-release-0-1 --head codex/spacexai/initial-release-0-1 --title "Add SpaceXAI conversation integration" --body-file spacexai-review/pr-bodies/core-01-initial.md
   ```

2. **Add SpaceXAI integration branding** — [write-up](pr-bodies/brands-01-initial.md), [preview](https://github.com/jeffglousher/brands/compare/codex/spacexai/review-base...spacexai-initial).

   ```shell
   gh pr create --draft --repo jeffglousher/brands --base codex/spacexai/review-base --head spacexai-initial --title "Add SpaceXAI integration branding" --body-file spacexai-review/pr-bodies/brands-01-initial.md
   ```

3. **Document the SpaceXAI conversation integration** — [write-up](pr-bodies/docs-01-initial.md), [preview](https://github.com/jeffglousher/home-assistant.io/compare/codex/spacexai/review-base-release-0-1...codex/spacexai/docs-initial-release-0-1).

   ```shell
   gh pr create --draft --repo jeffglousher/home-assistant.io --base codex/spacexai/review-base-release-0-1 --head codex/spacexai/docs-initial-release-0-1 --title "Document the SpaceXAI conversation integration" --body-file spacexai-review/pr-bodies/docs-01-initial.md
   ```

The fresh Core and docs candidates each contain one commit on the checked
official upstream tips: `38aacedef39eb3f077ce4a112a58bf7286af5e2c` and
`1b359d16aca5ba2c6b7983fa36c8c5f2334c5c5a`. Their new fixed review-base branches
produce exactly 18 Core files and one docs page. Brands retains its existing
fixed base `2751989265f1e13fa596dbdec9363b7bed0f0f48` and eight assets.

All old staging branches and review bases are preserved. Do not use the fork
default branches or move these fixed review bases. Replace companion comparison
links with actual draft PR links after you create them.

## Readiness and boundaries

[First-wave readiness](FIRST_WAVE_READINESS.md) records the current checks and
remaining gates. Core's published-dependency marker is now `done`; its runtime
and tests are unchanged from the prepared initial contribution. Validation now
installs the actual PyPI package, verifies its installed bytes against the
release source, and requires clean hassfest without a publication exception.

Fresh initial-only Home Assistant UI/OAuth acceptance and your review of the
three HA contributions still remain. Automated checks do not complete personal
attestations. An upstream Core submission stays on hold until those gates pass;
the public Brands logo also needs checking after its merge.

[The 23-contribution design stack](STACK.md) remains preserved. The new initial
submission candidates do not claim that all later layers were replayed onto
today's upstream. Package versions 0.2–0.5 remain unpublished; speech and later
Core layers retain the separate `has-entity-name: todo` blocker. No Bronze,
Gold, or Platinum award is claimed.

[Current native evidence](STAGED_READINESS.md) distinguishes the release-backed
first wave from historical source-checkout runs. [Runtime verification](RUNTIME_VERIFICATION.md)
still describes the earlier full-stack deployment: dogfood `18be3997`,
Core `b8be5c4f`, and client `f58ec77a`. This work did not redeploy or replace it.

Under [Home Assistant's AI policy](https://developers.home-assistant.io/docs/ai_policy),
a human must review, understand, and be able to explain every submitted change.
Private credentials, host inventory, raw deployment logs, and media samples
are excluded from this public packet.
