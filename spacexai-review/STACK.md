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

1. [Initial OAuth conversation](pr-bodies/core-01-initial.md) — `codex/spacexai/staged-01-initial` at `ec01be7f73a4650546ad93a0620aedad3f9e3756`; client 0.1.0.
2. [Dependency upgrade only](pr-bodies/core-dependency-02-0.2.0.md) — `codex/spacexai/staged-02-client-0-2` at `881d06d0f815117a50280937baca25df6e56ca09`; client 0.2.0.
3. [Conversation agents, attachments, and provider tools](pr-bodies/core-02-conversation.md) — `codex/spacexai/staged-03-conversation` at `be2990dc701c8e612dabd9fa6e43427dd5a43f9d`; client 0.2.0.
4. [Dependency upgrade only](pr-bodies/core-dependency-04-0.3.0.md) — `codex/spacexai/staged-04-client-0-3` at `2cf56d884682a631a0e7f75fdf22c23d34e91e87`; client 0.3.0.
5. [AI data tasks and image generation/editing](pr-bodies/core-03-ai-task.md) — `codex/spacexai/staged-05-ai-task` at `9dd2b6ab1e719d4c9e3d76af4b392408a5b21a96`; client 0.3.0.
6. [Dependency upgrade only](pr-bodies/core-dependency-06-0.4.0.md) — `codex/spacexai/staged-06-client-0-4` at `fa867ecef497b8c0e6e48626a95e6b271a986293`; client 0.4.0.
7. [Batch speech recognition and speech generation](pr-bodies/core-04-speech.md) — `codex/spacexai/staged-07-speech` at `e0064c95b46d596e430d83e7cc20b092a0676c32`; client 0.4.0. Quality-blocked by the speech naming rule.
8. [Dependency upgrade only](pr-bodies/core-dependency-08-0.5.0.md) — `codex/spacexai/staged-08-client-0-5` at `ba3515225a7087d7d8aa89dd8495b54755a1e2e3`; client 0.5.0. Quality-blocked by the speech naming rule.
9. [Video generation and administrator-only media actions](pr-bodies/core-05-video.md) — `codex/spacexai/staged-09-video` at `07c95d71202a7599cd4f91070df8a41a958a0524`; client 0.5.0. Quality-blocked by the speech naming rule.
10. [Same-account reauthentication and reconfiguration](pr-bodies/core-06-account.md) — `codex/spacexai/staged-10-account` at `984008407509045939e32d7263c33977806b944d`; client 0.5.0. Quality-blocked by the speech naming rule.
11. [Privacy-safe diagnostics](pr-bodies/core-07-diagnostics.md) — `codex/spacexai/staged-11-diagnostics` at `298a208679829f70a8c6c424d1ab5471e8c6da15`; client 0.5.0. Quality-blocked by the speech naming rule.

Core03, Core05, Core07, and Core09 are feature-only comparisons against dependency
layers Core02, Core04, Core06, and Core08 respectively. This follows the
[perfect PR recommendation](https://developers.home-assistant.io/docs/review-process/#creating-the-perfect-pr)
to separate dependency upgrades from feature changes. Submit against official
dev only after predecessors merge; refresh and retest at that time.

Native test counts are 37, 37, 51, 51, 83, 83, 102, 102, 132, 142, and 145.
The last includes three snapshots. Every module exceeds 95% statement coverage.
[Current proof](STAGED_READINESS.md) preserves exact source/run attribution.
Initial hassfest is blocked only by dependency publication. Speech and later
also fail the written entity-naming requirement; test success does not remove it.

## Package layers

All five source heads are pushed and pass Python 3.12/3.13/3.14 CI, strict types,
build/artifact checks, and isolated wheel/sdist imports. None is published.

1. [Client 0.1.0](pr-bodies/client-0.1.0.md) — `harden-initial-release` at `584250d60007714d337abfbcb3124318b8f49b22`; 87 tests.
2. [Client 0.2.0](pr-bodies/client-0.2.0.md) — `spacexai/client-02-conversation` at `72b9275207521580215c681597a2da20a7c9ff83`; 93 tests.
3. [Client 0.3.0](pr-bodies/client-0.3.0.md) — `spacexai/client-03-image` at `03bb0ee35e78df69f94c852e22887d4148fec0e4`; 121 tests.
4. [Client 0.4.0](pr-bodies/client-0.4.0.md) — `spacexai/client-04-speech` at `30587578411c3a605daccf1b86ec14022b15ce27`; 153 tests.
5. [Client 0.5.0](pr-bodies/client-0.5.0.md) — `spacexai/client-05-video` at `5bfafeceeca8a32ae6ace6d4471764c64ff86d69`; 182 tests.

The initial package owns release-source, matrix, changelog, and distribution
contract checks; additive parent merges carry them through later releases.
[Package evidence](PACKAGE_REPAIR_EVIDENCE.md) distinguishes automation from
uncompleted human review, main merge, publisher setup, and publication.

## Documentation and Brands

Docs is rebuilt on official next at `16ad324d9cbadf6d03b94f12ef278b00c7b9999f`.
Each of the six new branches contains one scoped layer; its SpaceXAI source
matches the preserved prior layer. The new initial page is 96 lines.

1. [docs-01-initial](pr-bodies/docs-01-initial.md) — `codex/spacexai/staged-docs-01-initial` at `ab12c0012807c333c90b34935e982d0b9df40d04`; accompanies Core 01.
2. [docs-02-conversation](pr-bodies/docs-02-conversation.md) — `codex/spacexai/staged-docs-02-conversation` at `ed3c8555040ce5910af857c5aabeb64cfd166dde`; accompanies Core 03.
3. [docs-03-ai-task](pr-bodies/docs-03-ai-task.md) — `codex/spacexai/staged-docs-03-ai-task` at `341c603235f9dec052aa8e0cc792d57bd37fdd41`; accompanies Core 05.
4. [docs-04-speech](pr-bodies/docs-04-speech.md) — `codex/spacexai/staged-docs-04-speech` at `54a6c6bd83aeb70637e2badf50fc0d183a137364`; accompanies Core 07.
5. [docs-05-video](pr-bodies/docs-05-video.md) — `codex/spacexai/staged-docs-05-video` at `f10ee3fb40ccb707cc7e5d66c5a6146fa1bb12b6`; accompanies Core 09.
6. [docs-06-account](pr-bodies/docs-06-account.md) — `codex/spacexai/staged-docs-06-account` at `30997c988948e3a3e9f138ed350960cd28ce81b3`; accompanies Core 10.

[Brands](pr-bodies/brands-01-initial.md) remains `spacexai-initial` at
`e3ac8da8bf579ec54210cc211e1eaa0768052679`: eight assets with retained official-source
provenance and native validator success. Public CDN delivery awaits merge.

Initial/final Jekyll builds and all six individual prose checks pass.
The exact rebuilt media-capable Core schema validates the docs blueprint without
executing actions. New rendered previews have not been visually inspected.
Docs04–06 accompany quality-blocked Core features; a docs build is not a
Core quality approval.

## Deployment and submission boundaries

The new full stack is deployed and verified: dogfood `08b259eed599e5d0e15a386d015244afa2221bba` on `codex/spacexai/dogfood-staged-20260907`, version `0.9.0.dev20260907`, contains Core11 and client 0.5.0 above. Source hashes, configuration check, restart, loaded existing OAuth entry, all four platform subentry types, and the single-overlay condition pass. Bounded live conversation, AI text, and a fresh TTS-to-STT round trip pass. See [runtime verification](RUNTIME_VERIFICATION.md) for exact scope and limits.

Dogfood is never an upstream PR head. No shared TTS-framework change is included
or approved as a 24th contribution. Keep the 23-layer plan intact until that
choice is made; speech/downstream remain quality-blocked.

After human review, publish and verify each required package version, refresh
its dependency-only Core layer, then submit the corresponding feature only
after prerequisites merge. Keep full templates and personally complete the
attestations; replace staging comparisons with actual PR/release links only
when those exist.
