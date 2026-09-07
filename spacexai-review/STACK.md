# SpaceXAI contribution stack

Canonical staging map, September 6, 2026. This supersedes the old map and test
counts. FIRST_WAVE_READINESS.md records gates; branch names are not a readiness
claim. This review packet stays separate from upstream-shaped contribution diffs.

## Design

OAuth device authorization is the only login path. The explicitly unofficial
spacexai-subscription-client owns the provider protocol; Core owns HA adaptation
and lifecycle. No CLI dependency or API-key fallback was added.

Seven Core layers, five package layers, six docs layers, and one Brands change:
19 prepared descriptions, not 19 open upstream PRs. The initial wave is four
contributions; follow-ons remain staged until prerequisites merge/release.

## Canonical Core layers

All are pushed to jeffglousher/core, on official dev at
d8840c5879458bd2dd504587f4d57cb6b1dfe4f9. The initial contribution is one focused
commit. The rebuilt follow-ons subsequently received test repairs through normal
commits and parent merges; no published history was rewritten. The integration
and test trees were compared against the repaired, preserved old branch chain
before the fresh history was published.

1. codex/spacexai/core-01-ready — c9e6db462a36cd5a70e12672d09579bd757f0e1b.
   Minimal OAuth-only conversation and optional Assist tools; package 0.1.0.
2. codex/spacexai/core-02-conversation-ready — a27a9ff9af041d1ae48b41a89f3f85466ec62506.
   Attachments, provider tools, multiple agents; package 0.2.0.
3. codex/spacexai/core-03-ai-task-ready — 53b75924a577da6aee2a35ddba13d617e094d83f.
   AI Task text/structured data and image generation/editing; package 0.3.0.
4. codex/spacexai/core-04-speech-ready — 9f96bf6adc9ccc6dbc23ae66b099c86f4ca1831e.
   Batch STT and TTS entities; package 0.4.0.
5. codex/spacexai/core-05-video-ready — b64085011ba8309005ec645d9500d76c45ba8c64.
   Video generation and administrator-only media publishing; package 0.5.0.
6. codex/spacexai/core-06-account-ready — 99c30c08fb74e97ba1fdba02b809ebb966d0a91b.
   Same-account OAuth reauthentication and preserved entity settings.
7. codex/spacexai/core-07-diagnostics-ready — 2315fa45b978aa1ebf637c111d0c1410d68d12ea.
   Privacy-safe diagnostics.

All seven layers pass native Linux tests: 39, 53, 85, 101, 123, 134, and 137
respectively. The final layer includes three snapshots. Every module exceeds
95% coverage in every layer, and native lint/types pass. Exact source pairs and
workflow evidence are in CORE_LINUX_EVIDENCE.md; old shim counts are retired.
The manifest still declares Bronze with an unsatisfied dependency-publication
gate. Platinum is a target, not an achieved tier.

## Package layers

All five heads are pushed, clean, and pass public CI on Python 3.12/3.13/3.14
including isolated wheel and source installs. None is published to PyPI.

1. harden-initial-release — c4fd662c281b5700a5c5d547b4afe097c8e5be22; 0.1.0; 59 tests.
2. spacexai/client-02-conversation — 25952c5f839a30cd26e374d1eae6408fa46392c1; 0.2.0; 65 tests.
3. spacexai/client-03-image — 80e36af0863d5b31742fddd6edd0ccdb306f1bcc; 0.3.0; 93 tests.
4. spacexai/client-04-speech — 9133ea56b89e6b35081f2bb19826bb83088582c8; 0.4.0; 125 tests.
5. spacexai/client-05-video — b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c; 0.5.0; 154 tests.

## Documentation and Brands

Docs uses codex/spacexai/docs-01-initial-next through
codex/spacexai/docs-06-account-next on official next, matching Core waves 1–6.
Current SHAs and native build evidence are in DOCS_QUALITY_REPAIR_EVIDENCE.md;
DOCS_BRANDS_REPAIR_EVIDENCE.md preserves the first build and asset provenance.
The final docs include both video/media action pages.

Brands remains spacexai-initial at e3ac8da8bf579ec54210cc211e1eaa0768052679.
Its eight assets have retained official-source provenance and pass the native
validator. The public CDN changes only after merge.

## Dogfood and preserved history

spacexai/dogfood-full at 47db702e65b7 is historical. The active deployment branch
is codex/spacexai/dogfood-current-dev at ae2897793bc9498a0d5714286d57dc21afdc912a.
It includes final Core `2315fa45` and exact package `b2d82345`, is pushed and deployed,
and preserves the existing OAuth entry. Live tests caught truncated TTS audio;
the package-layer repair was validated, deployed, and successfully retested with
full audio decoding and a TTS-to-STT round trip. RUNTIME_VERIFICATION.md records
the sanitized current runtime evidence.

Old published Core/docs refs were preserved without force pushes or deletion.
Use the canonical names above for new review. Dogfood is never an upstream PR
head; its only integration differences should be a development version and an
exact published GitHub source pin.

Rollback copies belong outside /config/custom_components; backup manifests in
that directory can be selected as duplicate integrations.
