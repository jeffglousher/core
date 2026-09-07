# SpaceXAI staged contribution review

This packet accompanies the prepared code on the jeffglousher forks. It is not
part of an upstream integration diff and does not submit any PR or release.
The implementation uses OAuth device authorization only, with no API-key fallback
or dependency on the Grok CLI.

## Review the first four

1. [Python 0.1.0](pr-bodies/client-0.1.0.md): the unofficial subscription client,
   OAuth protocol, and initial conversation API. Review this before publishing.
2. [Core initial integration](pr-bodies/core-01-initial.md): the minimal
   conversation integration, optional Assist tools, and tests.
3. [Brands](pr-bodies/brands-01-initial.md): the eight prepared integration assets
   with retained official-source provenance.
4. [Documentation](pr-bodies/docs-01-initial.md): the initial conversation page,
   setup instructions, privacy disclosures, and troubleshooting.

[First-wave readiness](FIRST_WAVE_READINESS.md) distinguishes completed checks
from submission gates. [Stack map](STACK.md) identifies every canonical layer.
The 19 descriptions are review drafts; follow-ons are not simultaneous upstream
submissions. Keep each later layer staged until its prerequisites merge/release.

## Verification

- [Native Core tests and per-module coverage](CORE_LINUX_EVIDENCE.md).
- [Native generated wiring and scoped hassfest](GENERATED_WIRING_EVIDENCE.md).
- [Python tests, supported versions, distributions, and release preparation](PACKAGE_REPAIR_EVIDENCE.md).
- [Final documentation builds and blueprint validation](DOCS_QUALITY_REPAIR_EVIDENCE.md).
- [Initial documentation and Brands provenance](DOCS_BRANDS_REPAIR_EVIDENCE.md).
- [Sanitized live test-system verification](RUNTIME_VERIFICATION.md).

The native checks do not depend on the retired Windows HA test shims. The
required Windows-wide hook run was attempted but its shell-based type-check
launcher could not start; this limitation is recorded, not counted as a pass.

## Human publication gates

No PyPI version has been published by this work. The package's tracked
[release checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/c4fd662c281b5700a5c5d547b4afe097c8e5be22/RELEASING.md)
specifies account setup, approval-gated trusted publishing, artifact checks,
release approval, and post-publication verification. Only after publication
can Core mark dependency-transparency done and pass clean final hassfest.

A human must review, understand, and be able to explain the changes before
submission under Home Assistant's AI policy. Personal attestations remain
unchecked. Replace staging comparisons with real PR and release links at that
time, and recheck upstream freshness. Bronze is the initial target; this packet
does not claim awarded Bronze, Gold, or Platinum status.

Private runtime credentials, host inventory, raw deployment logs, media samples,
and backups are intentionally excluded from this public review packet.
