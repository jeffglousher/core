# Current 23-contribution validation

September 7, 2026. This is the exact-source evidence for the first-wave
hardening and its additive propagation through [the stack](STACK.md).
[The previous packet](https://github.com/jeffglousher/core/blob/c1ae633f17322fe3f17738deebe842779f2d00f5/spacexai-review/STAGED_READINESS.md)
preserves earlier results; they are not relabeled as testing these new heads.

## First-wave changes

The existing Python client now rejects malformed consumed response fields,
unoffered function calls, unsupported explicit OAuth token types, and invalid
numeric token metadata with controlled library errors. Real pinned-SDK wire
tests verify this, including hosted/custom tool combinations in later releases.
OAuth identity and the sole browser-login path are unchanged.

Core adds no runtime code in this pass. Public-interface tests now finish login
retries, verify shared HTTP sessions and cancellation, and exercise real Assist
exposure controls and disabled-tool behavior. The four-line docs correction
clarifies subscription eligibility, selected-by-default Assist access, and
supported initial-layer troubleshooting. Brands assets are unchanged.

## Core: all eleven exact pairs pass

Native Linux/Python 3.14.5 runs retain the original pytest socket guard, check
the installed client against the manifest, regenerate requirements without
tracked changes, and pass scoped lint, formatting, typing, and tests. Every
module exceeds 95% statement coverage. All runs have zero test failures,
errors, or skips. These are statement, not branch, coverage measurements.

- Core 01: `1be5415320b9f511d568df7990d5f32ffb0df0df` + client `f12b460dffecff7ce4f2827fffa8351e06cadcb6`; [run 34169029198](https://github.com/jeffglousher/core/actions/runs/34169029198); 41 tests, 99.1701% statement coverage.
- Core 02: `23d3cadc96f939b3a0bb63409c31e3844aabae1c` + client `573e22c48b9e182ab27fcc0d3d4027d0e9e4a142`; [run 34169519326](https://github.com/jeffglousher/core/actions/runs/34169519326); 41 tests, 99.1701% statement coverage.
- Core 03: `c52ad690083d732abc49a64edd0f79730dd65fac` + client `573e22c48b9e182ab27fcc0d3d4027d0e9e4a142`; [run 34169520627](https://github.com/jeffglousher/core/actions/runs/34169520627); 55 tests, 99.0991% statement coverage.
- Core 04: `33d48cf808320e6123cc6141fd759c75cb49afea` + client `f98151c06729b7bb5a930bc863075cc396b25bf6`; [run 34169546289](https://github.com/jeffglousher/core/actions/runs/34169546289); 55 tests, 99.0991% statement coverage.
- Core 05: `4046b353e5b74553bfea2eaa30e4884e0e41ebc9` + client `f98151c06729b7bb5a930bc863075cc396b25bf6`; [run 34169548007](https://github.com/jeffglousher/core/actions/runs/34169548007); 87 tests, 99.5633% statement coverage.
- Core 06: `5e86d419c261bf98f92ed199b4f09e9ba7300c26` + client `b29c66df6833a2527fa4835aef10c46c26ed49ed`; [run 34169678476](https://github.com/jeffglousher/core/actions/runs/34169678476); 87 tests, 99.5633% statement coverage.
- Core 07: `2c59f3dc5e7ad02e12eeea8072e25a804ce5c698` + client `b29c66df6833a2527fa4835aef10c46c26ed49ed`; [run 34169680685](https://github.com/jeffglousher/core/actions/runs/34169680685); 106 tests, 99.6830% statement coverage.
- Core 08: `a0ab0bd3a699ffcb436bf8a63be60229a2b3d06f` + client `b6087bbd49428839cc4db845f0c5ec33ef3025fd`; [run 34169848657](https://github.com/jeffglousher/core/actions/runs/34169848657); 106 tests, 99.6830% statement coverage.
- Core 09: `26b85560a728196e64fac184bffb32b16f430685` + client `b6087bbd49428839cc4db845f0c5ec33ef3025fd`; [run 34169849867](https://github.com/jeffglousher/core/actions/runs/34169849867); 136 tests, 99.3827% statement coverage.
- Core 10: `82d4cc5337e1eb147a9a206da7fc0977d5efa5be` + client `b6087bbd49428839cc4db845f0c5ec33ef3025fd`; [run 34169851037](https://github.com/jeffglousher/core/actions/runs/34169851037); 146 tests, 99.4019% statement coverage.
- Core 11: `fd1db0993f4b92450784e26dc30d48c27e57f075` + client `b6087bbd49428839cc4db845f0c5ec33ef3025fd`; [run 34169852160](https://github.com/jeffglousher/core/actions/runs/34169852160); 149 tests, 99.4083% statement coverage.

Final includes three passing snapshots. Initial modules are 100% except
conversation at 97.7011%; final minimum module coverage is 97.3684%.
These explicit-input test runs used harness `c1ae633f17322fe3f17738deebe842779f2d00f5`.
Pin-only `8ac22e5f8fc511c74bc46fa9c5edbe2816b11d06` preserves validation behavior.

All published predecessor heads remain ancestors. Each updated Core tree
differs from its previous head only in the two intended test files. All four
dependency-only comparisons still change exactly manifest.json and
requirements_all.txt, one replacement in each. No later feature leaked
into the initial layer.

## Native setup and the honest quality boundary

[Initial run 34169029198](https://github.com/jeffglousher/core/actions/runs/34169029198)
also passes unchanged script/setup, the upstream full-tree general-hook subset,
and standard contribution-file hooks, including native MyPy/Pylint and generated
requirements/typing wiring. Strict hassfest reports only
`dependency-transparency: todo`, with no other errors or warnings. The staging
status is `blocked_only_on_dependency_publication`, not clean hassfest.
Only initial Core ran full standard hooks in this refinement batch.

[Exact first/final generated run 34169916228](https://github.com/jeffglousher/core/actions/runs/34169916228)
regenerates both exact current pairs without tracked changes. Initial passes
the publication-exception staging gate. Final correctly fails:
`dependency-transparency: todo` and `has-entity-name: todo`, no other findings.
The complete workflow result is failure; its strict check was not weakened.

The current TTS entity uses `_attr_has_entity_name = False`, while
[HA's written naming rule](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/has-entity-name/)
requires true with no exceptions. Keep 23 prepared contributions plus a
conditional minimal HA naming-fix slot beside the later speech wave, if still
needed. No additional Python package or first-wave framework change is planned.
[OpenAI TTS review](https://github.com/home-assistant/core/pull/162468#discussion_r2782946709)
accepted a TTS-only override;
[Fish Audio review](https://github.com/home-assistant/core/pull/152000#discussion_r2406956179)
requested separate handling; and
[shared naming fix #174614](https://github.com/home-assistant/core/pull/174614)
demonstrates a small Core fix with regression tests. This supports deferral,
not an automatic exemption. No Bronze, Gold, or Platinum award is claimed.

## Python: all five prepared releases pass

- Version 0.1.0: `f12b460dffecff7ce4f2827fffa8351e06cadcb6`; 110 tests, 96.59% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34168803786).
- Version 0.2.0: `573e22c48b9e182ab27fcc0d3d4027d0e9e4a142`; 119 tests, 96.99% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169272336).
- Version 0.3.0: `f98151c06729b7bb5a930bc863075cc396b25bf6`; 147 tests, 97.96% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169495197).
- Version 0.4.0: `b29c66df6833a2527fa4835aef10c46c26ed49ed`; 179 tests, 98.49% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169671109).
- Version 0.5.0: `b6087bbd49428839cc4db845f0c5ec33ef3025fd`; 208 tests, 98.19% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169834827).

All fifteen Python 3.12/3.13/3.14 jobs pass lint/format, strict MyPy, tests,
wheel/sdist builds, strict Twine, distribution contracts, and isolated imports
of both artifacts. The existing release-source, exact-main/tag, changelog,
matrix, and approval-gated publisher checks remain in place.
[Package evidence](PACKAGE_REPAIR_EVIDENCE.md) separates this runtime hardening
from prior release-automation work and uncompleted human publication gates.

No release was executed or main merge performed. PyPI publication and private
account/publisher setup remain owner-controlled, unverified gates; source CI
does not establish human review or successful publication.

## Docs and Brands

All six corrected docs heads are pushed on official next
`16ad324d9cbadf6d03b94f12ef278b00c7b9999f`, with individual prose checks.
[Native run 34168495512](https://github.com/jeffglousher/core/actions/runs/34168495512)
passes exact initial `0a5a5dfb0f779bf027b609781c5117cc78f9d3a7` and final
`69221dc8a853972e4b4fcbf78d4fbba8047b393d` Jekyll builds and prose checks.
The unchanged Brands `e3ac8da8bf579ec54210cc211e1eaa0768052679` passes the full
19,231-image scan with zero issues. All eight assets retain source provenance.

That run's blueprint checks use exact older Core09
`07c95d71202a7599cd4f91070df8a41a958a0524`, not the new test-only head:
two valid cases, missing media rejected, zero actions executed. The new Core
changes do not alter runtime/schema source. Static HTML checks pass, but no
browser surface is available for a new visual preview. Public logo delivery
still awaits Brands merge. [Docs/Brands evidence](DOCS_BRANDS_REPAIR_EVIDENCE.md)
records the precise limits.

## Deployment and submission boundaries

Dogfood `85ac0fd099cdfb94ebc604ee9677aa16f61719c8` contains current Core11 and pins
current client 0.5.0. It is pushed, deployed, and running as
`0.9.0.dev20260907`. Source hashes, configuration check, restart, existing OAuth
load, all four platform subentry types, and the single-overlay condition pass.
Bounded conversation, AI text, uncached TTS, complete audio decoding, and the
exact-audio STT round trip pass. [Runtime verification](RUNTIME_VERIFICATION.md)
distinguishes the loaded source pin from unavailable container-level wheel
hash inspection and preserves earlier live evidence as historical.

The [first-four checklist](FIRST_WAVE_READINESS.md) remains explicit: human
review, package main merge and publisher/account setup, publication,
post-publication clean hassfest, fresh initial-only OAuth installation, and
visual review are not completed. The existing full-stack account is not fresh
first-install proof. No suitable isolated native host is available here.

No upstream PR, comment, release, or account setting was created. Personal
attestations remain unchecked under [HA's AI policy](https://developers.home-assistant.io/docs/ai_policy).
The initial draft links [previous #178765](https://github.com/home-assistant/core/pull/178765)
without inventing maintainer approval/rejection. The first attempted new Core
test run failed a test import; the corrected exact source above was rerun and
passed. Failed or cancelled runs are not counted as green evidence.
