# Current 23-contribution validation

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
