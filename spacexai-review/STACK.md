# SpaceXAI contribution stack

Preserved staging map, September 8, 2026. This replaces the prior 19-contribution
map; old published refs remain historical and were not rewritten or deleted.
The packet is separate from every upstream-shaped contribution diff.

## Current first-wave submission candidates

Python 0.1.0 is [published](https://pypi.org/project/spacexai-subscription-client/0.1.0/)
from `155d76c5b940108be707bb379c02d476b893b758`, but live initial conversation
failed with HTTP 426. The reviewed correction is client 0.1.1 at
`a7f7afb514e6a0362d927124fd01b75d25885af9` on `codex/initial-client-compatibility`.
All three Python CI jobs pass 130 tests with 100% statement coverage, artifact
checks, and clean installations. It is committed and pushed, not published;
no 0.1.1 PR or release exists.

The current initial Core branch is `codex/spacexai/initial-release-0-1` at
`82984cdde6d0801e2d79753ce39645bc658a3266`, four commits on official dev
`38aacedef39eb3f077ce4a112a58bf7286af5e2c` with exactly 18 changed files. It retains the focused
shutdown repair and default/enabled/disabled Assist setup tests, and now prepares
the corrected 0.1.1 requirement. The dependency-transparency rule remains `todo`
until that version is published and verified. The matching-pin native run passes
50 tests and 241/241 statements with no override;
[current CI](https://github.com/jeffglousher/core/actions/runs/34298154970) passes
both integration and full-native-hooks jobs. The separate hassfest report remains
blocked only on dependency publication; CI success does not close that gate.
[First-wave readiness](FIRST_WAVE_READINESS.md) records the scope; no completed Bronze or
upstream-ready status is claimed.

Bounded initial-only candidate acceptance passes: fresh external-Chrome OAuth,
chat/history, exposed-helper control with the unexposed helper unchanged,
same-account restart followed by chat, and normal account/entity removal.
Those live checks used the verified local 0.1.1 wheel as an explicit override
of the earlier Core 0.1.0 pin. The empty isolated instance was then stopped;
its environment and evidence are preserved. The [runtime record](RUNTIME_VERIFICATION.md)
keeps this history separate from current dependency checks. The old full-stack
deployment below was not changed.

Initial docs is `codex/spacexai/docs-initial-release-0-1` at
`44526b046fa26d4ddf0ab037850a54e30ecbf1d0`, one commit on official next
`1b359d16aca5ba2c6b7983fa36c8c5f2334c5c5a`; the 96-line page is byte-unchanged.
Brands remains at the source listed below.

First review/create/merge the [0.1.1 library correction](README.md#next-review-the-python-011-correction),
then approve its protected release and verify the published artifacts before
completing Core's publication gate and the three companion fork drafts.
The old 23-layer design and all its branch histories remain available below;
they have not all been replayed onto today's upstream. Follow-ons still use
unpublished package versions and must retain their publication blockers.
The shutdown fix and client compatibility/storage correction have not been
carried into or retested through these later layers; previous green receipts
do not certify an updated complete stack.

## Scope and order

There are 23 prepared contributions: 11 Core, five package, six docs, and one
Brands contribution. They are not 23 open upstream PRs. The first wave remains
four contribution areas: the initial client (now requiring corrective 0.1.1),
initial Core, Brands, and initial docs. The corrective library PR does not add
a new feature wave or a separate initial Core dependency-upgrade PR.

OAuth-only provider communication belongs in the unofficial Python client.
Core handles HA adaptation, configuration, lifecycle, and entity/action behavior.
No API-key fallback or runtime CLI dependency is introduced.

## Preserved Core design layers

All are pushed to jeffglousher/core on official dev base
`be2e14f4273335fb5ef02b7f636cd01800e1491a`. Each comparison uses the immediately preceding
Core layer, not the preceding feature alone. Initial Core compares to that
recorded upstream base. Additive fixes and parent merges preserve published history.

1. [Initial OAuth conversation](pr-bodies/core-01-initial.md) — `codex/spacexai/staged-01-initial` at `5d623e0a730ded8c3b4d4fa41af064d9955ad623`; client 0.1.0.
2. [Dependency upgrade only](pr-bodies/core-dependency-02-0.2.0.md) — `codex/spacexai/staged-02-client-0-2` at `7bc75c5d6779818a06a6911d42142577f47cdf49`; client 0.2.0.
3. [Conversation agents, attachments, and provider tools](pr-bodies/core-02-conversation.md) — `codex/spacexai/staged-03-conversation` at `ff27b13f102d7831c006edb9c9a40e9b96c629c9`; client 0.2.0.
4. [Dependency upgrade only](pr-bodies/core-dependency-04-0.3.0.md) — `codex/spacexai/staged-04-client-0-3` at `c3a9240e8fa0e9d8c3f76258b705152aa50eb1e8`; client 0.3.0.
5. [AI data tasks and image generation/editing](pr-bodies/core-03-ai-task.md) — `codex/spacexai/staged-05-ai-task` at `0534071acb44c328bf625fe93507eb9c24e6ec5a`; client 0.3.0.
6. [Dependency upgrade only](pr-bodies/core-dependency-06-0.4.0.md) — `codex/spacexai/staged-06-client-0-4` at `c29dcae8be97f50aeb27aa31f17ede7cf857d732`; client 0.4.0.
7. [Batch speech recognition and speech generation](pr-bodies/core-04-speech.md) — `codex/spacexai/staged-07-speech` at `3c918d49d191b51e11f632eb0d9ab52d85c586cd`; client 0.4.0. Quality-blocked by the speech naming rule.
8. [Dependency upgrade only](pr-bodies/core-dependency-08-0.5.0.md) — `codex/spacexai/staged-08-client-0-5` at `c8ad97e2ea9a649b5e87d45fec2a2fa6d9fc2bda`; client 0.5.0. Quality-blocked by the speech naming rule.
9. [Video generation and administrator-only media actions](pr-bodies/core-05-video.md) — `codex/spacexai/staged-09-video` at `36b7b3f9261992cffef227eab5c3824d259fe6fc`; client 0.5.0. Quality-blocked by the speech naming rule.
10. [Same-account reauthentication and reconfiguration](pr-bodies/core-06-account.md) — `codex/spacexai/staged-10-account` at `13dfb2f8f8b4012e13e9a2a9b83c0f8cce29a974`; client 0.5.0. Quality-blocked by the speech naming rule.
11. [Privacy-safe diagnostics](pr-bodies/core-07-diagnostics.md) — `codex/spacexai/staged-11-diagnostics` at `c5aa62747eb9e0701ce01c5a7e08c90a7161ef0e`; client 0.5.0. Quality-blocked by the speech naming rule.

Core03, Core05, Core07, and Core09 are feature-only comparisons against dependency
layers Core02, Core04, Core06, and Core08 respectively. This follows the
[perfect PR recommendation](https://developers.home-assistant.io/docs/review-process/#creating-the-perfect-pr)
to separate dependency upgrades from feature changes. Submit against official
dev only after predecessors merge; refresh and retest at that time.

The pre-publication native runs for these eleven preserved Core/package pairs
pass after the coverage tests were inherited. The preserved initial has
241/241 statements covered (100%), with no excluded statements. This does not
claim 100% for every follow-on layer or branch coverage.
[Validation evidence](STAGED_READINESS.md) preserves exact source/run attribution.
Historical `25e04203` passed full native hooks and generated/publication validation
using PyPI. The older initial's publication finding is historical. Unpublished follow-on
versions and the speech entity-naming rule remain separate blockers.

## Package layers

All five source heads are pushed and pass Python 3.12/3.13/3.14 CI, strict types,
build/artifact checks, and isolated wheel/sdist imports. Version 0.1.0 is
published; 0.2–0.5 remain unpublished. The following are the prepared source
branch heads; the published initial merge commit is recorded above.

1. [Client 0.1.0](pr-bodies/client-0.1.0.md) — `harden-initial-release` at `e3269374781fcbe8f0d55713219e089bebb2d08b`; 127 tests.
2. [Client 0.2.0](pr-bodies/client-0.2.0.md) — `spacexai/client-02-conversation` at `c571128196a790526f51ba5b66f8cf0ba9c77edb`; 136 tests.
3. [Client 0.3.0](pr-bodies/client-0.3.0.md) — `spacexai/client-03-image` at `74c7e22805c2b25651f307d8f9256bbfd8dfa520`; 164 tests.
4. [Client 0.4.0](pr-bodies/client-0.4.0.md) — `spacexai/client-04-speech` at `0fafe1f2a2966987ba6041e8d318cd3cd9f61627`; 196 tests.
5. [Client 0.5.0](pr-bodies/client-0.5.0.md) — `spacexai/client-05-video` at `24cfeaed9266550d23859739c685c78f7ad1faa7`; 225 tests.

The initial package owns release-source, matrix, changelog, and distribution
contract checks; additive parent merges carry them through later releases.
[Package evidence](PACKAGE_REPAIR_EVIDENCE.md) distinguishes automation from
historical release checks from the current 0.1.1 human-review/publication gate.

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
The recorded media-capable Core schema validates the docs blueprint without
executing actions; it is not the current Core head. Exact initial docs have now
been visually inspected at desktop/mobile widths and final docs at desktop width.
Interactive controls and each intermediate preview were not separately exercised.
Docs04–06 accompany quality-blocked Core features; a docs build is not a
Core quality approval.

## Deployment and submission boundaries

The previously verified full stack is deployed: dogfood `18be39973b1361ebe23605dc4a605ae0d69cff43` on `codex/spacexai/dogfood-staged-20260907`, version `0.9.0.dev20260907`, contains the earlier Core11 `b8be5c4f783900a8e50db8cb577756d4f8901136` and client 0.5.0 at `f58ec77aebff01fe6bf4b72e97a2370b023647a2`, not the current prepared heads above. Source hashes, configuration check, restart, loaded existing OAuth entry, all four platform subentry types, and the single-overlay condition pass. Bounded live conversation, AI text, and a fresh TTS-to-STT round trip pass. See [runtime verification](RUNTIME_VERIFICATION.md) for exact scope and limits.

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
