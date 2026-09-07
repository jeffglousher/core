# Current 23-contribution validation

September 7, 2026. This is the current evidence index for the rebuilt branch
chain in [STACK.md](STACK.md). Older evidence files are historical and must not
be attributed to these exact heads.

## Core: all eleven integration suites pass

The native Linux/Python 3.14.5 jobs install the exact client source below,
verify the manifest version, retain the normal pytest socket guard, and
enforce strictly greater than 95% statement coverage for every integration
module. All passing runs have zero failures, errors, or skips. Native lint,
formatting, typing, and regenerated requirements pass at each layer, with
no tracked generated changes. These are statement, not branch, coverage figures.

- Core 01: `ec01be7f73a4650546ad93a0620aedad3f9e3756` + client `584250d60007714d337abfbcb3124318b8f49b22`; [run 34123627426](https://github.com/jeffglousher/core/actions/runs/34123627426); 37 tests, 99.1701% statement coverage.
- Core 02: `881d06d0f815117a50280937baca25df6e56ca09` + client `72b9275207521580215c681597a2da20a7c9ff83`; [run 34123636543](https://github.com/jeffglousher/core/actions/runs/34123636543); 37 tests, 99.1701% statement coverage.
- Core 03: `be2990dc701c8e612dabd9fa6e43427dd5a43f9d` + client `72b9275207521580215c681597a2da20a7c9ff83`; [run 34123635119](https://github.com/jeffglousher/core/actions/runs/34123635119); 51 tests, 99.0991% statement coverage.
- Core 04: `2cf56d884682a631a0e7f75fdf22c23d34e91e87` + client `03bb0ee35e78df69f94c852e22887d4148fec0e4`; [run 34123632852](https://github.com/jeffglousher/core/actions/runs/34123632852); 51 tests, 99.0991% statement coverage.
- Core 05: `9dd2b6ab1e719d4c9e3d76af4b392408a5b21a96` + client `03bb0ee35e78df69f94c852e22887d4148fec0e4`; [run 34123998947](https://github.com/jeffglousher/core/actions/runs/34123998947); 83 tests, 99.5633% statement coverage.
- Core 06: `fa867ecef497b8c0e6e48626a95e6b271a986293` + client `30587578411c3a605daccf1b86ec14022b15ce27`; [run 34124094618](https://github.com/jeffglousher/core/actions/runs/34124094618); 83 tests, 99.5633% statement coverage.
- Core 07: `e0064c95b46d596e430d83e7cc20b092a0676c32` + client `30587578411c3a605daccf1b86ec14022b15ce27`; [run 34124102607](https://github.com/jeffglousher/core/actions/runs/34124102607); 102 tests, 99.6830% statement coverage.
- Core 08: `ba3515225a7087d7d8aa89dd8495b54755a1e2e3` + client `5bfafeceeca8a32ae6ace6d4471764c64ff86d69`; [run 34124111027](https://github.com/jeffglousher/core/actions/runs/34124111027); 102 tests, 99.6830% statement coverage.
- Core 09: `07c95d71202a7599cd4f91070df8a41a958a0524` + client `5bfafeceeca8a32ae6ace6d4471764c64ff86d69`; [run 34124119021](https://github.com/jeffglousher/core/actions/runs/34124119021); 132 tests, 99.3827% statement coverage.
- Core 10: `984008407509045939e32d7263c33977806b944d` + client `5bfafeceeca8a32ae6ace6d4471764c64ff86d69`; [run 34124550362](https://github.com/jeffglousher/core/actions/runs/34124550362); 142 tests, 99.4019% statement coverage.
- Core 11: `298a208679829f70a8c6c424d1ab5471e8c6da15` + client `5bfafeceeca8a32ae6ace6d4471764c64ff86d69`; [run 34124560787](https://github.com/jeffglousher/core/actions/runs/34124560787); 145 tests and three snapshots, 99.4083% statement coverage.

Initial module coverage is init/config-flow/constants 100% and conversation
97.7011%. Final module coverage is conversation 98.4496%, media 97.3684%, and
all other integration modules 100%.

The harness used for these test runs is
`10b4aa0db9d9d409bed5d742ce73dd3dca81ca1b` on the fork-only validation
branch. Subsequent pin-only commit `9f64099f0641ff5b2b1c6229c003f5863118319f`
does not change its validation behavior.

## Native setup, generated wiring, and the honest quality boundary

The [initial exact-source run](https://github.com/jeffglousher/core/actions/runs/34123627426)
also passes unchanged script/setup, the upstream full-tree general-hook subset,
and standard contribution-file hooks. Native MyPy without the scoped import
override, Pylint including applicable tests, requirements, and MyPy-config
generation pass. Strict hassfest has only `dependency-transparency: todo`,
no other errors or warnings. The recorded staging status is
`blocked_only_on_dependency_publication`, not clean hassfest.

[Full-stack hook run 34124137737](https://github.com/jeffglousher/core/actions/runs/34124137737)
used previous Core `2ddb465615d28516d67fe146379f1931d546c3a9` with the
current final client. Setup, general/contribution hooks, and generated wiring
pass, but the workflow fails correctly: one quality-scale finding lists
`dependency-transparency: todo` and `has-entity-name: todo`, with no other
errors/warnings. Current final Core differs by one corrected test expectation.
This run is not relabeled as testing current Core11.

[Exact latest first/final generated run 34124881178](https://github.com/jeffglousher/core/actions/runs/34124881178)
tests the current initial and final pairs above. Both regenerate requirements
and integration wiring without tracked changes, and requirements validation
passes. Initial passes only the staging publication-exception gate. Final fails
the two rules above; the complete workflow result is **failure**.

The current TTS implementation uses `_attr_has_entity_name = False`.
[HA's entity-naming rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name/)
requires true and states there are no exceptions. Speech/Core07 and every
downstream Core layer remain quality-blocked. A proposed framework layer is
not approved or included in the 23-contribution plan. Functional tests, high
coverage, and the declared target tier do not establish Bronze, Gold, or Platinum.

## Python: exact prepared release heads

- Version 0.1.0: `584250d60007714d337abfbcb3124318b8f49b22`; 87 tests, 96.51% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34123466992).
- Version 0.2.0: `72b9275207521580215c681597a2da20a7c9ff83`; 93 tests, 96.93% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34123471193).
- Version 0.3.0: `03bb0ee35e78df69f94c852e22887d4148fec0e4`; 121 tests, 97.93% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34123467044).
- Version 0.4.0: `30587578411c3a605daccf1b86ec14022b15ce27`; 153 tests, 98.47% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34123467280).
- Version 0.5.0: `5bfafeceeca8a32ae6ace6d4471764c64ff86d69`; 182 tests, 98.17% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34123467554).

Every public run passes Python 3.12/3.13/3.14, Ruff lint/format, strict MyPy,
tests, builds, strict Twine checks, exact wheel/sdist contract validation, and
separate isolated installs/imports of each artifact. The additive hardening
does not change provider runtime source, package metadata, or the lockfile.

The initial layer now owns 28 release-contract tests and checked-in release
preflight. Release-source policy requires the exact tag SHA to equal current
main, a matching package version and nonempty changelog section. The exact
release SHA must pass all three Python jobs before artifact handoff to the
isolated, approval-gated publisher. The contract checks required source,
typing marker, license, docs/tests/scripts/workflows/lockfile, distribution
metadata, and source bytes. Independent review also checked the retained
bounded real-aiohttp TTS-stream behavior; its committed regressions remain in
package 0.4.0 and descendants.

No release has been executed. Main remains
`40e8a3bd46653eecbb6269eb7e59cc9ecf91f75c`, not the prepared initial
package. PyPI returns 404 for the intended distribution; no package tags,
releases, GitHub publishing environment, or configured rulesets were present
at the release-gate inspection. Account-owner security/pending-publisher
settings cannot be inferred from that public state. Automation proves source
and artifacts, not human review, successful publication, or approval settings.

## Docs and Brands

New docs base: `16ad324d9cbadf6d03b94f12ef278b00c7b9999f`.
Initial source: `ab12c0012807c333c90b34935e982d0b9df40d04`.
Final source: `30997c988948e3a3e9f138ed350960cd28ce81b3`.
All six scoped documentation layers pass their prose and whitespace checks.
Each SpaceXAI source layer was compared byte-for-byte with its preserved
predecessor-chain content after replaying onto current next.

[Run 34124125762](https://github.com/jeffglousher/core/actions/runs/34124125762)
passes exact initial/final Jekyll builds, native prose checks, and Brands at
`e3ac8da8bf579ec54210cc211e1eaa0768052679`. It uses Ruby 3.4.8, Jekyll 4.4.1, and
Node 20.20.2. Brands checks 19,231 images with zero issues; unrelated warnings
are not SpaceXAI findings. The eight source assets are unchanged; their retained
official-source provenance is in the historical Brands evidence.

[Refreshed blueprint run 34124125762](https://github.com/jeffglousher/core/actions/runs/34124125762)
validates exact final docs against Core09
`07c95d71202a7599cd4f91070df8a41a958a0524`: two valid input cases, missing media
rejected, and zero provider or Home Assistant actions executed. This supersedes
the prior blueprint check pinned to the old Core chain.

Rendered artifacts are built but newly generated previews have not been
visually inspected. Source equality and static HTML checks are not browser
verification. Actual public logo delivery still depends on the Brands merge.

## Release, initial-login, and runtime boundaries

The first four are ready for human review, not upstream submission. See
[FIRST_WAVE_READINESS.md](FIRST_WAVE_READINESS.md) for the distinct human review,
publisher/account setup, publication, post-publication hassfest, fresh
initial-only OAuth login, and visual-preview gates.

No suitable isolated native Home Assistant host is presently available for a
fresh first-install login. Existing full-stack credentials and runtime helpers
must not be reused as initial-only proof. OAuth identity approval is unchanged;
no API-key path or additional provider permission assumption was introduced.

New dogfood `08b259eed599e5d0e15a386d015244afa2221bba` contains Core11 and
the exact final client. It is deployed and running as `0.9.0.dev20260907`;
source hashes, configuration check, restart, existing OAuth load, platform
subentries, and single-overlay checks pass. Bounded conversation, AI text,
fresh TTS, full audio decode, and exact-audio STT round-trip checks pass.
[Runtime verification](RUNTIME_VERIFICATION.md) records the limits: no fresh
initial-only login, new paid image/video generation, or home-device actions.

The previous [Core contribution #178765](https://github.com/home-assistant/core/pull/178765)
is linked in the initial PR draft. It was closed by its author; no human Core
approval/rejection is inferred. Human attestations stay unchecked, and no
upstream PR, comment, publisher setting, or release was created by this work.
