# SpaceXAI staged contribution review

Current packet: September 7, 2026. These are fork-only review drafts, not
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

## Current stack and proof

The [canonical map](STACK.md) has **23 prepared contributions**: 11 Core layers,
five package layers, six docs layers, and one Brands change. Four separate Core
dependency upgrades now precede the features that need them. Follow-ons remain
staged until their prerequisites merge or release.

[Current validation and gates](STAGED_READINESS.md) identifies exact source pairs
and native run links. All eleven Core layers pass their integration tests; the
final layer has 145 tests and three snapshots. This is not a clean final
quality verdict: speech and every later Core layer remain blocked by
`has-entity-name: todo`, in addition to unpublished dependencies.

The earlier Core, generated-wiring, docs, and runtime evidence files are retained
with explicit historical labels. Their older successful runs are not evidence
for the rebuilt heads. [Package evidence](PACKAGE_REPAIR_EVIDENCE.md) now begins
with the current release-hardening and five-version CI results.

## Human and publication boundaries

No package version is published. The prepared package is not merged to main,
and its GitHub publishing environment is not configured. PyPI account security
and pending-publisher setup require account-owner verification. Release
automation checks source and artifacts; it does not prove human review.

Under [Home Assistant's AI policy](https://developers.home-assistant.io/docs/ai_policy),
a human must review, understand, and be able to explain every submitted change.
Personal attestations remain unchecked. The initial draft links the
[previous contribution #178765](https://github.com/home-assistant/core/pull/178765);
it does not invent maintainer approval or rejection.

The current plan does not include an unapproved 24th shared-framework change.
No Bronze, Gold, or Platinum award is claimed. New rendered docs still need
visual review, and a fresh initial-only Home Assistant OAuth login still needs
an isolated native host and human authorization. Full-stack runtime status is
recorded separately in [runtime verification](RUNTIME_VERIFICATION.md).

Private credentials, host inventory, raw deployment logs, media samples, and
backups are excluded from this public packet.
