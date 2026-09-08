## Proposed change

Fix subscription requests failing with HTTP 426 after successful OAuth login.
The proxy was interpreting this package's `0.1.0` version as an outdated Grok
CLI build. I separated the tested Grok Build compatibility value from the
package's own version and kept the explicitly unofficial client identity.

This prepares `0.1.1`. It also explicitly sets `store=False`, matching the
referenced Grok Build sampler. There is no new dependency, CLI execution,
API-key fallback, OAuth identity change, retry, or automatic version negotiation.
The README documents the pinned source and the limits of this interoperability
convention; it is not presented as an official xAI protocol-version contract.

## Testing

- 130 tests pass on Python 3.12, 3.13, and 3.14, locally and in
  [CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34290919712),
  with 100% statement coverage on each version.
- New real-SDK transport tests cover truthful request identity, the separate
  compatibility header, disabled response storage, and plain-text/JSON HTTP 426
  failures without retries.
- Ruff, strict MyPy, build, strict Twine, release preflight, and six isolated
  wheel/source installations pass. Independent code review found no blockers.
- The unchanged initial Home Assistant integration passes all 50 native tests
  with the candidate wheel, with 100% statement coverage. Live chat/history and
  Assist control pass in the separate initial-only HA instance; the unexposed
  test helper stays unchanged. The same account supports chat after a clean
  restart, and account/entity removal completes without requiring restart.
  This is a temporary candidate dependency override,
  not a claim that the Core manifest already pins a published `0.1.1`.

## Release

Review and merge this patch before releasing `v0.1.1` through the existing
protected publishing workflow. Do not replace `v0.1.0`. After publication and
artifact verification, update the initial Core dependency and rerun its checks.
The updated `RELEASING.md` contains the publication checklist.
