# SpaceXAI staged contribution review

Current packet: September 8, 2026. These are fork-only review drafts, not
upstream submissions or releases. OAuth device authorization remains the only
login path; there is no API-key fallback or Grok CLI dependency.

## Review the first four

1. [Python 0.1.0](pr-bodies/client-0.1.0.md): unofficial provider/OAuth client
   and release preparation.
2. [Core initial integration](pr-bodies/core-01-initial.md): minimal
   conversation support and optional Assist tools.
3. [Brands](pr-bodies/brands-01-initial.md): eight integration assets.
4. [Documentation](pr-bodies/docs-01-initial.md): initial setup, privacy,
   limitations, troubleshooting, and removal.

The first four are prepared for human review, not upstream-ready. The
[readiness checklist](FIRST_WAVE_READINESS.md) records the remaining gates.

## Create the four fork drafts

Read and understand each write-up before creating its draft. These commands
target only your repositories; they have not been executed. Run them from a
checkout of `codex/spacexai-validation`, where `spacexai-review/` is present.
They supply the title, body, base, head, and draft status explicitly.

1. **Prepare spacexai-subscription-client 0.1.0** — [write-up](pr-bodies/client-0.1.0.md), [preview](https://github.com/jeffglousher/spacexai-subscription-client/compare/main...harden-initial-release).

   ```shell
   gh pr create --draft --repo jeffglousher/spacexai-subscription-client --base main --head harden-initial-release --title "Prepare spacexai-subscription-client 0.1.0" --body-file spacexai-review/pr-bodies/client-0.1.0.md
   ```

2. **Add SpaceXAI conversation integration** — [write-up](pr-bodies/core-01-initial.md), [preview](https://github.com/jeffglousher/core/compare/codex/spacexai/review-base...codex/spacexai/staged-01-initial).

   ```shell
   gh pr create --draft --repo jeffglousher/core --base codex/spacexai/review-base --head codex/spacexai/staged-01-initial --title "Add SpaceXAI conversation integration" --body-file spacexai-review/pr-bodies/core-01-initial.md
   ```

3. **Add SpaceXAI integration branding** — [write-up](pr-bodies/brands-01-initial.md), [preview](https://github.com/jeffglousher/brands/compare/codex/spacexai/review-base...spacexai-initial).

   ```shell
   gh pr create --draft --repo jeffglousher/brands --base codex/spacexai/review-base --head spacexai-initial --title "Add SpaceXAI integration branding" --body-file spacexai-review/pr-bodies/brands-01-initial.md
   ```

4. **Document the SpaceXAI conversation integration** — [write-up](pr-bodies/docs-01-initial.md), [preview](https://github.com/jeffglousher/home-assistant.io/compare/codex/spacexai/review-base...codex/spacexai/staged-docs-01-initial).

   ```shell
   gh pr create --draft --repo jeffglousher/home-assistant.io --base codex/spacexai/review-base --head codex/spacexai/staged-docs-01-initial --title "Document the SpaceXAI conversation integration" --body-file spacexai-review/pr-bodies/docs-01-initial.md
   ```

The three review bases are pinned to the recorded upstream Core, docs, and
Brands commits, respectively: `be2e14f4`, `16ad324d`, and `27519892`.
GitHub comparisons contain exactly 18 Core files, one docs page, and eight
Brands assets. Existing fork `dev`, `current`, and `master` are not the clean
review bases. Do not merge into or move these review-base branches during
staging; prepare refreshed upstream submission branches later.

After creating the drafts, replace the companion comparison links with their
actual draft PR links. Personal understanding, live-install testing, publication,
and upstream-readiness attestations remain unchecked where unfulfilled; do not
check them merely because this packet is complete. Package publication still
requires a separate human-reviewed main merge and approval. An upstream Core
PR remains on hold; these fork drafts do not claim that all release gates pass.

## Current stack and proof

The [canonical map](STACK.md) has **23 prepared contributions**: 11 Core layers,
five package layers, six docs layers, and one Brands change. Four separate Core
dependency upgrades now precede the features that need them. Follow-ons remain
staged until their prerequisites merge or release.

Recorded Core and docs bases are behind the freshly checked upstream tips;
refresh and retest before human-reviewed upstream submission.

[Current validation and gates](STAGED_READINESS.md) identifies exact source pairs
and native run links. The initial Core/client pair passes 46 native tests
and standard hooks, with 241/241 statements covered. The initial Python client
passes 127 tests and has 100% statement coverage on all three supported Pythons.
Neither measurement excludes statements or claims branch coverage. All five
package heads pass their three-Python matrices (127/136/164/196/225 tests), and
all eleven updated Core/package pairs pass native tests. The inherited coverage
tests do not change production code. This is not a clean final
quality verdict: speech and every later Core layer remain blocked by
`has-entity-name: todo`, in addition to unpublished dependencies.

The earlier Core, generated-wiring, docs, and runtime evidence files are retained
with explicit historical labels. Their older successful runs are not evidence
for the rebuilt heads. [Package evidence](PACKAGE_REPAIR_EVIDENCE.md) now begins
with the coverage checkpoint and all fifteen current Python CI results.
HA runtime code, docs, and Brands did not change in this coverage pass.

## Human and publication boundaries

No package version is published, and the prepared package is not merged to main.
Verified GitHub controls now require owner approval in the `pypi` environment,
limit it to `v*` tags, and disallow administrator bypass. Protected main requires
a PR and the three strict Python CI checks; version tags cannot be changed or
deleted. These controls do not prove independent human review or distinguish
an agent using the owner's identity from the owner. An agent must not approve
publication. Tag protection is not release-asset immutability.

Current main still has the legacy release workflow. It uses the protected
`pypi` environment, but the stronger exact-main preflight, full release matrix,
and artifact contract are only on the prepared branch until its reviewed merge.
PyPI account security and the exact pending publisher remain unverified; the
browser reached sign-in without a login attempt. See the [first-wave checklist](FIRST_WAVE_READINESS.md)
for these distinct publication gates.

Under [Home Assistant's AI policy](https://developers.home-assistant.io/docs/ai_policy),
a human must review, understand, and be able to explain every submitted change.
Personal attestations remain unchecked. The earliest and only publicly found
`jeffglousher` Core contribution is [#178765](https://github.com/home-assistant/core/pull/178765).
The author account closed it unmerged on August 18, 2026, without a written
closure explanation. Its reviews were automated, not a human maintainer
rejection. The [provenance summary](FIRST_WAVE_READINESS.md#original-contribution-provenance)
separates that record from our conclusions about the rewritten code.

The plan remains 23 prepared contributions, with a conditional HA naming-fix
slot beside the later speech wave if still needed. This is not a new Python
package and does not enlarge or block the initial conversation contribution.
No Bronze, Gold, or Platinum award is claimed. The exact initial docs preview
was visually checked at desktop and mobile widths: readable, with no overlap.
Its missing public integration logo is expected until Brands merges; a missing
footer image is a preview-artifact limitation. The exact final docs also pass
desktop visual inspection. Interactive controls and separate previews of all
six docs layers were not exercised. A fresh initial-only Home Assistant OAuth
login still needs
an isolated native host and human authorization. Full-stack runtime status is
recorded separately in [runtime verification](RUNTIME_VERIFICATION.md); the
running dogfood still uses the previous `f58ec77a` client, not this expiry fix.

Private credentials, host inventory, raw deployment logs, media samples, and
backups are excluded from this public packet.
