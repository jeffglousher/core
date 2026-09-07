# SpaceXAI contribution stack

Canonical staging map, September 7, 2026. This replaces the prior 19-contribution
map; old published refs remain historical and were not rewritten or deleted.
The packet is separate from every upstream-shaped contribution diff.

## Scope and order

There are 23 prepared contributions: 11 Core, five package, six docs, and one
Brands contribution. They are not 23 open upstream PRs. The first wave remains
four contributions: client 0.1.0, initial Core, Brands, and initial docs.

OAuth-only provider communication belongs in the unofficial Python client.
Core handles HA adaptation, configuration, lifecycle, and entity/action behavior.
No API-key fallback or runtime CLI dependency is introduced.

## Canonical Core layers

All are pushed to jeffglousher/core on official dev base
`be2e14f4273335fb5ef02b7f636cd01800e1491a`. Each comparison uses the immediately preceding
Core layer, not the preceding feature alone. Initial Core compares to that
recorded upstream base. Additive fixes and parent merges preserve published history.

1. [Initial OAuth conversation](pr-bodies/core-01-initial.md) — `codex/spacexai/staged-01-initial` at `1be5415320b9f511d568df7990d5f32ffb0df0df`; client 0.1.0.
2. [Dependency upgrade only](pr-bodies/core-dependency-02-0.2.0.md) — `codex/spacexai/staged-02-client-0-2` at `23d3cadc96f939b3a0bb63409c31e3844aabae1c`; client 0.2.0.
3. [Conversation agents, attachments, and provider tools](pr-bodies/core-02-conversation.md) — `codex/spacexai/staged-03-conversation` at `c52ad690083d732abc49a64edd0f79730dd65fac`; client 0.2.0.
4. [Dependency upgrade only](pr-bodies/core-dependency-04-0.3.0.md) — `codex/spacexai/staged-04-client-0-3` at `33d48cf808320e6123cc6141fd759c75cb49afea`; client 0.3.0.
5. [AI data tasks and image generation/editing](pr-bodies/core-03-ai-task.md) — `codex/spacexai/staged-05-ai-task` at `4046b353e5b74553bfea2eaa30e4884e0e41ebc9`; client 0.3.0.
6. [Dependency upgrade only](pr-bodies/core-dependency-06-0.4.0.md) — `codex/spacexai/staged-06-client-0-4` at `5e86d419c261bf98f92ed199b4f09e9ba7300c26`; client 0.4.0.
7. [Batch speech recognition and speech generation](pr-bodies/core-04-speech.md) — `codex/spacexai/staged-07-speech` at `2c59f3dc5e7ad02e12eeea8072e25a804ce5c698`; client 0.4.0. Quality-blocked by the speech naming rule.
8. [Dependency upgrade only](pr-bodies/core-dependency-08-0.5.0.md) — `codex/spacexai/staged-08-client-0-5` at `a0ab0bd3a699ffcb436bf8a63be60229a2b3d06f`; client 0.5.0. Quality-blocked by the speech naming rule.
9. [Video generation and administrator-only media actions](pr-bodies/core-05-video.md) — `codex/spacexai/staged-09-video` at `26b85560a728196e64fac184bffb32b16f430685`; client 0.5.0. Quality-blocked by the speech naming rule.
10. [Same-account reauthentication and reconfiguration](pr-bodies/core-06-account.md) — `codex/spacexai/staged-10-account` at `82d4cc5337e1eb147a9a206da7fc0977d5efa5be`; client 0.5.0. Quality-blocked by the speech naming rule.
11. [Privacy-safe diagnostics](pr-bodies/core-07-diagnostics.md) — `codex/spacexai/staged-11-diagnostics` at `fd1db0993f4b92450784e26dc30d48c27e57f075`; client 0.5.0. Quality-blocked by the speech naming rule.

Core03, Core05, Core07, and Core09 are feature-only comparisons against dependency
layers Core02, Core04, Core06, and Core08 respectively. This follows the
[perfect PR recommendation](https://developers.home-assistant.io/docs/review-process/#creating-the-perfect-pr)
to separate dependency upgrades from feature changes. Submit against official
dev only after predecessors merge; refresh and retest at that time.

Native test counts are 41, 41, 55, 55, 87, 87, 106, 106, 136, 146, and 149.
The last includes three snapshots. Every module exceeds 95% statement coverage.
[Current proof](STAGED_READINESS.md) preserves exact source/run attribution.
Initial hassfest is blocked only by dependency publication. Speech and later
also fail the written entity-naming requirement; test success does not remove it.

## Package layers

All five source heads are pushed and pass Python 3.12/3.13/3.14 CI, strict types,
build/artifact checks, and isolated wheel/sdist imports. None is published.

1. [Client 0.1.0](pr-bodies/client-0.1.0.md) — `harden-initial-release` at `f12b460dffecff7ce4f2827fffa8351e06cadcb6`; 110 tests.
2. [Client 0.2.0](pr-bodies/client-0.2.0.md) — `spacexai/client-02-conversation` at `573e22c48b9e182ab27fcc0d3d4027d0e9e4a142`; 119 tests.
3. [Client 0.3.0](pr-bodies/client-0.3.0.md) — `spacexai/client-03-image` at `f98151c06729b7bb5a930bc863075cc396b25bf6`; 147 tests.
4. [Client 0.4.0](pr-bodies/client-0.4.0.md) — `spacexai/client-04-speech` at `b29c66df6833a2527fa4835aef10c46c26ed49ed`; 179 tests.
5. [Client 0.5.0](pr-bodies/client-0.5.0.md) — `spacexai/client-05-video` at `b6087bbd49428839cc4db845f0c5ec33ef3025fd`; 208 tests.

The initial package owns release-source, matrix, changelog, and distribution
contract checks; additive parent merges carry them through later releases.
[Package evidence](PACKAGE_REPAIR_EVIDENCE.md) distinguishes automation from
uncompleted human review, main merge, publisher setup, and publication.

## Documentation and Brands

Docs is rebuilt on official next at `16ad324d9cbadf6d03b94f12ef278b00c7b9999f`.
Each of the six branches contains one scoped layer. This pass carries the same
four-line initial prose correction through all six, preserving their published
history. The initial page remains 96 lines.

1. [docs-01-initial](pr-bodies/docs-01-initial.md) — `codex/spacexai/staged-docs-01-initial` at `0a5a5dfb0f779bf027b609781c5117cc78f9d3a7`; accompanies Core 01.
2. [docs-02-conversation](pr-bodies/docs-02-conversation.md) — `codex/spacexai/staged-docs-02-conversation` at `ce493b6c2d545d3f0b0b8f887a01c140b4e35347`; accompanies Core 03.
3. [docs-03-ai-task](pr-bodies/docs-03-ai-task.md) — `codex/spacexai/staged-docs-03-ai-task` at `fc805f1dd2565f5d9fdecd3c08a6b8f806c5cc96`; accompanies Core 05.
4. [docs-04-speech](pr-bodies/docs-04-speech.md) — `codex/spacexai/staged-docs-04-speech` at `7c1846b5924b4c5715c67c8ae3791821668150b9`; accompanies Core 07.
5. [docs-05-video](pr-bodies/docs-05-video.md) — `codex/spacexai/staged-docs-05-video` at `f50938f93797f403cae294f7b790344885180dce`; accompanies Core 09.
6. [docs-06-account](pr-bodies/docs-06-account.md) — `codex/spacexai/staged-docs-06-account` at `69221dc8a853972e4b4fcbf78d4fbba8047b393d`; accompanies Core 10.

[Brands](pr-bodies/brands-01-initial.md) remains `spacexai-initial` at
`e3ac8da8bf579ec54210cc211e1eaa0768052679`: eight assets with retained official-source
provenance and native validator success. Public CDN delivery awaits merge.

Initial/final Jekyll builds and all six individual prose checks pass.
The exact rebuilt media-capable Core schema validates the docs blueprint without
executing actions. New rendered previews have not been visually inspected.
Docs04–06 accompany quality-blocked Core features; a docs build is not a
Core quality approval.

## Deployment and submission boundaries

The new full stack is deployed and verified: dogfood `85ac0fd099cdfb94ebc604ee9677aa16f61719c8` on `codex/spacexai/dogfood-staged-20260907`, version `0.9.0.dev20260907`, contains Core11 and client 0.5.0 above. Source hashes, configuration check, restart, loaded existing OAuth entry, all four platform subentry types, and the single-overlay condition pass. Bounded live conversation, AI text, and a fresh TTS-to-STT round trip pass. See [runtime verification](RUNTIME_VERIFICATION.md) for exact scope and limits.

Dogfood is never an upstream PR head. Keep the 23 prepared contributions and a
conditional HA naming-fix slot beside the later speech wave, only if still
needed then. No extra Python package or first-wave framework change is planned.
Accepted OpenAI and Fish Audio TTS precedent supports keeping this issue
separate from the initial integration; it does not establish an automatic
quality-rule exemption. Speech/downstream remain quality-blocked until the
written rule is genuinely satisfied or maintainers explicitly resolve it.

After human review, publish and verify each required package version, refresh
its dependency-only Core layer, then submit the corresponding feature only
after prerequisites merge. Keep full templates and personally complete the
attestations; replace staging comparisons with actual PR/release links only
when those exist.
