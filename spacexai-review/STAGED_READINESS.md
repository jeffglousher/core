# Current 23-contribution validation

## Current published-dependency checkpoint

September 8, 2026. Python 0.1.0 is published from `155d76c5b940108be707bb379c02d476b893b758`
with verified hashes, source bytes, signed provenance, and six clean installations.
[Publication evidence](PACKAGE_REPAIR_EVIDENCE.md) records the exact files and scope.

Current initial Core `cd495263eed9794a02a19efb797206e4ff67ef8f` contains three commits
on official dev `38aacedef39eb3f077ce4a112a58bf7286af5e2c`, still exactly 18 files.
The second commit gives device polling HA background-task shutdown ownership
and adds one public shutdown regression. The third adds three public-flow tests
for default/enabled/disabled Assist choices. The PyPI dependency and production
files are unchanged from `25e04203`.

The full 50-case related suite passes locally on the user's Linux HA host in a
separate development environment: zero failures/errors/skips, 241/241 statements,
zero exclusions, and all four modules at 100%. Native socket/task safeguards
remain unchanged and dependency checks pass. Neither running HA environment
was modified. [Fresh native CI](https://github.com/jeffglousher/core/actions/runs/34260917145)
passes all 50 tests, scoped checks, unchanged setup, native hooks, and clean
generated-file/publication validation for the full new commit ID. Both jobs are
successful. The earlier invocation
34260599438 failed before testing because an abbreviated ID was interpreted
as a branch/tag pattern by checkout; this was corrected in the new invocation.

The prior production-revision
[Native run 34251664631](https://github.com/jeffglousher/core/actions/runs/34251664631)
passes the integration job with actual PyPI 0.1.0/release `155d76c5`: 47 tests,
241/241 statements (100%), all four modules at 100%, zero exclusions, failures,
errors, or skips. Scoped lint, formatting, MyPy, and Pylint pass. Its negative
control gives exactly one expected failure against old `7a41a035` production
(cancellation at `not_running` instead of `stopping`), then restores fixed source
before the full 47-test pass. This proves late cancellation, not shutdown duration.

Both jobs in that run pass, including unchanged script/setup, the full-tree
general-hook subset, standard native contribution hooks, and generated wiring
and publication validation. Its harness:
`15adcb71e31a2ade8db05463da95498082537634`. The isolated `25e04203` instance
matches all seven source blobs, with all 118 dependencies and PyPI client 0.1.0
unchanged; import/dependency checks and configuration validation pass. It is
running on loopback-only HTTP with no SpaceXAI entries. Real OAuth start reaches
device progress; cancel produces verified 404 without an entry. A second pending
authorization is cancelled by shutdown: the process exits, its port closes, and
the reported late-device-task warning is absent. Restart returns to running.
The first-party provider sign-in page awaits human approval; completed login,
HA UI setup, and functional acceptance remain pending.
[Runtime evidence](RUNTIME_VERIFICATION.md) records live scope.
Later layers have not inherited/retested this fix; the old full stack is unchanged.

### Historical release-backed replay

The refreshed initial Core `7a41a0358c01a58700bde227fa0a951d28f5e638` was one commit
on official dev `38aacedef39eb3f077ce4a112a58bf7286af5e2c`. Its runtime and tests
are unchanged; the dependency-publication rule is now done.
[Native run 34244844613](https://github.com/jeffglousher/core/actions/runs/34244844613)
uses the actual PyPI package, not a local source install: 46 tests, 241/241
statements, zero missing/excluded statements, failures, errors, or skips.
All six installed runtime files match the release source and direct-URL
metadata is absent. Scoped checks and requirement regeneration pass. The same
exact-source run also passes unchanged script/setup, the upstream full-tree
general-hook subset, and standard native hooks on all 18 contribution files,
including unskipped hassfest. Full-hook generated validation is clean too;
the wheelhouse build is skipped and `UV_FIND_LINKS` is empty.

[Generated run 34244846528](https://github.com/jeffglousher/core/actions/runs/34244846528)
records the initial pair as genuinely clean: hassfest exit 0, zero findings or
warnings, status `passed`, and unchanged tracked generated files. Its unchanged
final pair `c5aa6274`/`24cfeaed` still fails exactly publication and speech naming.
The overall generated workflow therefore fails; the initial job passes.
Harness `5229aa8a4be5e9083c9f53f3e25283d47986678a` enforces actual PyPI installation
and rejects the old publication exception in PyPI mode. Explicit checkout mode
is retained only for unpublished follow-on versions.

[First-wave readiness](FIRST_WAVE_READINESS.md) records completed current native
checks and companion builds, source refs, and remaining human/live-login
gates. The older 23-layer design, runtime installation, and receipts below are
preserved, not relabeled as tested on the refreshed base.

## Historical pre-publication coverage and fork-draft checkpoint

September 8, 2026. The initial Core integration now has exact 100% statement
coverage: 241/241 statements, zero missing or excluded statements, and 46 tests.
The initial Python client passes 127 tests with exact 100% on Python 3.12,
3.13, and 3.14. These are statement measurements, not branch coverage or a
substitute for human review. Only test files changed from the expiry checkpoint;
no production code, coverage exclusions, or dependency versions changed.

The [historical four-draft instructions](https://github.com/jeffglousher/core/blob/6ba2c7d337f0d4d3eb3fe036a66aa507a2fa24e6/spacexai-review/README.md#create-the-four-fork-drafts)
target only jeffglousher's repositories. Three fixed review-base branches give
clean initial Core/docs/Brands diffs; package review targets its own main.
No draft was opened, package published, or HA deployment performed.

All eleven current Core/package pairs pass native Linux/Python 3.14.5 tests,
with zero failures, errors, skips, or excluded statements. Their exact artifact
source pins and JUnit/coverage receipts were checked. Scoped lint, format,
types, and dependency regeneration pass; tracked generated files are unchanged.
Every module exceeds 95% statement coverage, but follow-ons are not all 100%.

- Core 01: `5d623e0a730ded8c3b4d4fa41af064d9955ad623` + client `e3269374781fcbe8f0d55713219e089bebb2d08b`; [run 34234130097](https://github.com/jeffglousher/core/actions/runs/34234130097); 46 tests, 241/241 statements (100%).
- Core 02: `7bc75c5d6779818a06a6911d42142577f47cdf49` + client `c571128196a790526f51ba5b66f8cf0ba9c77edb`; [run 34234988875](https://github.com/jeffglousher/core/actions/runs/34234988875); 46 tests, 241/241 statements (100%).
- Core 03: `ff27b13f102d7831c006edb9c9a40e9b96c629c9` + client `c571128196a790526f51ba5b66f8cf0ba9c77edb`; [run 34234992204](https://github.com/jeffglousher/core/actions/runs/34234992204); 60 tests, 332/333 statements (99.6997%).
- Core 04: `c3a9240e8fa0e9d8c3f76258b705152aa50eb1e8` + client `74c7e22805c2b25651f307d8f9256bbfd8dfa520`; [run 34234995677](https://github.com/jeffglousher/core/actions/runs/34234995677); 60 tests, 332/333 statements (99.6997%).
- Core 05: `0534071acb44c328bf625fe93507eb9c24e6ec5a` + client `74c7e22805c2b25651f307d8f9256bbfd8dfa520`; [run 34234998984](https://github.com/jeffglousher/core/actions/runs/34234998984); 94 tests, 457/458 statements (99.7817%).
- Core 06: `c29dcae8be97f50aeb27aa31f17ede7cf857d732` + client `0fafe1f2a2966987ba6041e8d318cd3cd9f61627`; [run 34235282105](https://github.com/jeffglousher/core/actions/runs/34235282105); 94 tests, 457/458 statements (99.7817%).
- Core 07: `3c918d49d191b51e11f632eb0d9ab52d85c586cd` + client `0fafe1f2a2966987ba6041e8d318cd3cd9f61627`; [run 34235285057](https://github.com/jeffglousher/core/actions/runs/34235285057); 115 tests, 630/631 statements (99.8415%).
- Core 08: `c8ad97e2ea9a649b5e87d45fec2a2fa6d9fc2bda` + client `24cfeaed9266550d23859739c685c78f7ad1faa7`; [run 34235287824](https://github.com/jeffglousher/core/actions/runs/34235287824); 115 tests, 630/631 statements (99.8415%).
- Core 09: `36b7b3f9261992cffef227eab5c3824d259fe6fc` + client `24cfeaed9266550d23859739c685c78f7ad1faa7`; [run 34235290922](https://github.com/jeffglousher/core/actions/runs/34235290922); 146 tests, 806/810 statements (99.5062%).
- Core 10: `13dfb2f8f8b4012e13e9a2a9b83c0f8cce29a974` + client `24cfeaed9266550d23859739c685c78f7ad1faa7`; [run 34235294166](https://github.com/jeffglousher/core/actions/runs/34235294166); 156 tests, 832/836 statements (99.5215%).
- Core 11: `c5aa62747eb9e0701ce01c5a7e08c90a7161ef0e` + client `24cfeaed9266550d23859739c685c78f7ad1faa7`; [run 34235297253](https://github.com/jeffglousher/core/actions/runs/34235297253); 159 tests, 841/845 statements (99.5266%), with three snapshots.

Only the initial run in this checkpoint executes unchanged script/setup,
the upstream full-tree general-hook subset, and standard contribution-file
hooks. All pass. The ten follow-on runs explicitly skip the full-hooks job;
their scoped checks are not relabeled as full-hook execution. Ordered parent
merges preserve the tests. Four dependency-only diffs remain one replacement
each in manifest.json and requirements_all.txt, with no feature code.

Harness `52f78bbee9a5a25dae0d3715cdb37884ebf9cf60` pins the current initial
and final pairs. Its [default initial smoke run](https://github.com/jeffglousher/core/actions/runs/34235390253)
passes. [Generated run 34235390337](https://github.com/jeffglousher/core/actions/runs/34235390337)
reports exactly `dependency-transparency: todo` for initial Core. Final Core
reports that publication blocker plus `has-entity-name: todo`; neither pair
has other errors or warnings. Generated tracked files are unchanged. The
overall generated workflow fails: the initial staging exception is not clean
hassfest, and speech/downstream naming remains a separate unresolved gate.

[Package evidence](PACKAGE_REPAIR_EVIDENCE.md) records all fifteen successful
Python jobs for the five current heads. Runtime remains on the earlier
`f58ec77a` client. Publication, fresh initial-only OAuth acceptance, human review,
and replay/retest against current upstream remain
[first-wave gates](FIRST_WAVE_READINESS.md).

## Historical September 8 expiry correction

The package heads recorded at this historical checkpoint pass all fifteen public
Python jobs. They contain only the two timestamp-normalization changes and
two added public regression cases, propagated through existing parent merges.
No Core, integration docs, Brands, or live deployment source changed.

[Native initial run 34229775265](https://github.com/jeffglousher/core/actions/runs/34229775265)
verifies Core `cbe618c9800419de39601496779da68e5dd8ed23` with client
`410730d2c9803d2a4c83cdeb6ebe7f1f2c0b9dd3` on recorded base
`be2e14f4273335fb5ef02b7f636cd01800e1491a`: 44 tests, no failures/errors/skips,
239/241 statements (99.1701%), standard socket guard, unchanged setup,
full-tree general-hook subset, and standard contribution hooks all pass.
Generated wiring remains unchanged. Strict hassfest still reports exactly
`dependency-transparency: todo`, no other errors or warnings: this is an
explicit publication-blocked staging result, not clean hassfest.

Harness `f6ca2b875d214d12173306eb8a80fc1e880976ee` now defaults to the new client
heads. Its [default initial smoke run](https://github.com/jeffglousher/core/actions/runs/34230277910)
passes scoped checks; full hooks are proven by the separate run above.
[Generated run 34230277869](https://github.com/jeffglousher/core/actions/runs/34230277869)
records the same initial publication blocker. Its final pair, Core `b8be5c4f`
with client `376fe0c9`, fails exactly publication and `has-entity-name: todo`,
with no other errors/warnings. The overall generated workflow fails; later
speech naming is not an initial-layer blocker.

The remaining ten Core/package pairs below have not been rerun with the new
package heads. Their receipts remain historical evidence. Runtime remains on
the previous `f58ec77a` client. Upstream inspection identified no initial API
migration, but no current-tip replay or fresh initial-only OAuth login is
claimed. [First-wave readiness](FIRST_WAVE_READINESS.md) retains those gates.

## Historical timeout and wheel-contract checkpoint

September 7, 2026 (America/Chicago; CI receipts extend into September 8 UTC).
These exact-source results cover the OAuth-timeout and publication-contract
repairs, propagated additively through [the stack](STACK.md).
[The previous packet](https://github.com/jeffglousher/core/blob/40e9dc4893fb663b38649145e47e0f7c9bfec019/spacexai-review/STAGED_READINESS.md)
preserves the earlier protocol-hardening results. They are not relabeled as
testing these new heads.

## Verified defects and minimal repairs

The [original closed PR's bot finding](https://github.com/home-assistant/core/pull/178765#discussion_r3760223813)
identified an OAuth refresh timeout that still escaped HA error handling.
[Pre-fix native reproduction](https://github.com/jeffglousher/core/actions/runs/34174576579)
confirmed setup entered SETUP_ERROR and conversation leaked TimeoutError.
Cancellation already passed. A later recovery test incorrectly called
async_setup while in SETUP_RETRY; it was corrected to public async_reload
before the final successful run.

The initial integration now maps that timeout to setup retry or a translated
conversation error. The AI layer handles its boundary; speech moves that
mapping into the existing shared token helper. Final runtime changes are
exactly two existing exception-handler lines. No extra adapter, package,
framework, or API-key fallback was added.

Tests reach the real HA OAuth helper through a mocked token HTTP endpoint.
They verify retained credentials, new-token recovery, cancellation, public
AI/STT/TTS errors, and video failure without provider or local-media side effects.
Independent re-review found no actionable issue in this scoped repair.

The package wheel checker previously accepted unexpected installable members.
Eight regressions failed before the correction and now pass: missing standard
members, extra .pth/.data/package files, and duplicate members are rejected.
The sdist contract verifies required source bytes, not every possible archive
security property. Only release checker/tests/instructions changed; runtime
code, package versions, metadata, and lockfiles are byte-unchanged.

## Core: all eleven exact pairs pass

Native Linux/Python 3.14.5 runs retain the original pytest socket guard,
verify installed package versions, regenerate requirements without tracked
changes, and pass lint, formatting, typing, and tests. All runs have zero
test failures, errors, or skips. Every module exceeds 95% statement coverage;
this is not branch coverage.

- Core 01: `cbe618c9800419de39601496779da68e5dd8ed23` + client `b5513112b12a14baa43c295cf82cec8be3604ba7`; [run 34175174869](https://github.com/jeffglousher/core/actions/runs/34175174869); 44 tests, 99.1701% statement coverage.
- Core 02: `bfb6bf9ccb55d1e42267175201affdd9d642c052` + client `fc13749a2d9befa62b9581ccd4e3a60a9ef3c54e`; [run 34175270367](https://github.com/jeffglousher/core/actions/runs/34175270367); 44 tests, 99.1701% statement coverage.
- Core 03: `a3adf7f56bb35d70b8b4db5acb1a59709574245e` + client `fc13749a2d9befa62b9581ccd4e3a60a9ef3c54e`; [run 34175271997](https://github.com/jeffglousher/core/actions/runs/34175271997); 58 tests, 99.0991% statement coverage.
- Core 04: `7057018ab57429d82dbbf43123f530bb5323ece2` + client `44e84f8b4962dfd52098f5520655bdddc3def88b`; [run 34175274032](https://github.com/jeffglousher/core/actions/runs/34175274032); 58 tests, 99.0991% statement coverage.
- Core 05: `cc5abf2719d35d7b1cf5380e0052380ab46c39be` + client `44e84f8b4962dfd52098f5520655bdddc3def88b`; [run 34175275683](https://github.com/jeffglousher/core/actions/runs/34175275683); 92 tests, 99.5633% statement coverage.
- Core 06: `4034c56fefbef6b9aa346adb63fcb4fe752a3475` + client `b6b1d7d301b66bd29e24d2c0c309fa3e775f9881`; [run 34175277392](https://github.com/jeffglousher/core/actions/runs/34175277392); 92 tests, 99.5633% statement coverage.
- Core 07: `5494fee60b2b4f4720ee93463bf25b9375040d36` + client `b6b1d7d301b66bd29e24d2c0c309fa3e775f9881`; [run 34175311223](https://github.com/jeffglousher/core/actions/runs/34175311223); 113 tests, 99.6830% statement coverage.
- Core 08: `a7a0e4b5f6fbad3cc36bec34d4199bb766614735` + client `f58ec77aebff01fe6bf4b72e97a2370b023647a2`; [run 34175312827](https://github.com/jeffglousher/core/actions/runs/34175312827); 113 tests, 99.6830% statement coverage.
- Core 09: `22180c78bea231061810d1427a4a3acd36014dde` + client `f58ec77aebff01fe6bf4b72e97a2370b023647a2`; [run 34175314769](https://github.com/jeffglousher/core/actions/runs/34175314769); 144 tests, 99.3827% statement coverage.
- Core 10: `fc87cca838e64db775d94842d5d21830a81a797c` + client `f58ec77aebff01fe6bf4b72e97a2370b023647a2`; [run 34175316461](https://github.com/jeffglousher/core/actions/runs/34175316461); 154 tests, 99.4019% statement coverage.
- Core 11: `b8be5c4f783900a8e50db8cb577756d4f8901136` + client `f58ec77aebff01fe6bf4b72e97a2370b023647a2`; [run 34175318077](https://github.com/jeffglousher/core/actions/runs/34175318077); 157 tests, 99.4083% statement coverage.

Initial coverage is 239/241 statements, minimum module 97.7011%.
Final is 840/845 statements, minimum module 97.3684%, with three snapshots.
Exact artifact source pins were checked for every run. All source worktrees
are clean and their pushed heads match.

All published predecessor heads remain ancestors. Dependency-only layers
02/04/06/08 still change exactly manifest.json and requirements_all.txt,
one replacement each, against their updated immediate predecessors.
No later feature was added to the initial layer.

## Native setup and quality boundary

[Initial run 34175174869](https://github.com/jeffglousher/core/actions/runs/34175174869)
also passes unchanged script/setup, the upstream full-tree general-hook subset,
and standard contribution-file hooks, including native MyPy/Pylint and generated
requirements/typing wiring. Strict hassfest reports only
`dependency-transparency: todo`, with no other errors or warnings.
This is a publication-exception staging pass, not clean hassfest.
Only initial Core ran full standard hooks in this repair batch.

[Exact first/final generated run 34175415170](https://github.com/jeffglousher/core/actions/runs/34175415170)
regenerates both pairs without tracked changes. Initial passes the explicit
publication-exception gate. Final correctly fails with
`dependency-transparency: todo` and `has-entity-name: todo`, no other findings.
The complete workflow result is failure; its strict check was not weakened.
These pins are recorded by harness commit
`fa44940aa7b2069f4d15ddf531cdc2d48f0a20f5`; the explicit-input integration runs
used `40e9dc4893fb663b38649145e47e0f7c9bfec019`.

The TTS entity uses `_attr_has_entity_name = False`, while
[HA's written naming rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name/)
requires true with no exceptions. Keep the conditional minimal HA naming-fix
slot beside speech if needed then; no extra Python package or initial framework
change is planned. [OpenAI TTS precedent](https://github.com/home-assistant/core/pull/162468#discussion_r2782946709),
[Fish Audio precedent](https://github.com/home-assistant/core/pull/152000#discussion_r2406956179),
and [shared naming fix #174614](https://github.com/home-assistant/core/pull/174614)
support a separately scoped resolution, not an automatic quality exemption.
No Bronze, Gold, or Platinum award is claimed.

## Python: all five prepared releases pass

- Version 0.1.0: `b5513112b12a14baa43c295cf82cec8be3604ba7`; 118 tests, 96.59% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174829112).
- Version 0.2.0: `fc13749a2d9befa62b9581ccd4e3a60a9ef3c54e`; 127 tests, 96.99% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992495).
- Version 0.3.0: `44e84f8b4962dfd52098f5520655bdddc3def88b`; 155 tests, 97.96% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992428).
- Version 0.4.0: `b6b1d7d301b66bd29e24d2c0c309fa3e775f9881`; 187 tests, 98.49% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992423).
- Version 0.5.0: `f58ec77aebff01fe6bf4b72e97a2370b023647a2`; 216 tests, 98.19% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992203).

All fifteen Python 3.12/3.13/3.14 jobs pass lint/format, strict MyPy, tests,
wheel/sdist builds, strict Twine, distribution contracts, and isolated imports.
Each layer includes 36 release-contract tests. Locked runtime names, versions,
and license metadata for 25 packages were retained on win32/Python 3.14.5;
that platform-specific evidence is not a human license-compatibility attestation.

The actual GitHub environment, main checks, and version-tag protections are
now configured and independently read back. Current main still contains its
legacy workflow; the prepared stronger release workflow must be reviewed and
merged before release. PyPI sign-in, account security, pending-publisher binding,
human review, and publication remain uncompleted. An agent must not approve
the owner's publication. [Package evidence](PACKAGE_REPAIR_EVIDENCE.md) and the
[first-wave checklist](FIRST_WAVE_READINESS.md) separate these gates.

## Docs, Brands, and upstream freshness

[Native run 34168495512](https://github.com/jeffglousher/core/actions/runs/34168495512)
passes exact initial docs `0a5a5dfb0f779bf027b609781c5117cc78f9d3a7` and final
`69221dc8a853972e4b4fcbf78d4fbba8047b393d` Jekyll builds and prose checks.
All six docs heads pass individual prose/whitespace checks.
Brands `e3ac8da8bf579ec54210cc211e1eaa0768052679` passes the full
19,231-image scan with zero issues. All eight assets retain source provenance.

The exact initial preview was visually inspected at desktop/mobile widths
and final integration page at desktop width. Content is readable without
overlap; interactive controls and intermediate previews were not exercised.
The integration CDN logo remains unavailable until Brands merges, and the
partial preview artifact omits the generic footer image.

The blueprint evidence still uses older Core09
`07c95d71202a7599cd4f91070df8a41a958a0524`: two valid cases, missing media
rejected, zero actions executed. It is not a new run against the corrected
Core09. The timeout repair does not change the blueprint action schema.

Canonical bases remain Core dev `be2e14f4273335fb5ef02b7f636cd01800e1491a`
and docs next `16ad324d9cbadf6d03b94f12ef278b00c7b9999f`.
Fresh official reads found dev `384c153186de3f095d62188bb2d6e88a03dc7dd6`
30 commits ahead and next `4ea450877c77e70f9aa364012134b8a662ecb8c2` four ahead.
Docs changes are unrelated. Core includes generic reauthentication translation,
selector fixes, and a Zizmor upgrade; OAuth/conversation/AI/STT/TTS sources are
unchanged. This inspection is not a current-tip test run. Refresh and retest
submission branches before upstream submission without silently rewriting
published history.

## Deployment and submission boundaries

[Runtime verification](RUNTIME_VERIFICATION.md) records the separately
assembled, source-verified dogfood deployment and bounded live results.
Existing-account full-stack success does not prove an isolated initial-only
installation or a fresh human OAuth login.

No upstream PR, comment, package release, main merge, or publication approval
was performed. Personal review attestations remain unchecked. The original
PR closure facts and useful bot feedback are recorded in the
[first-wave summary](FIRST_WAVE_READINESS.md#original-contribution-provenance).
