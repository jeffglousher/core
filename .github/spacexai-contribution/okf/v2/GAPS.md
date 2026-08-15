# OKF v2 gap list — 2026-08-15

Scored against official HA contribution docs in `snapshots/`. This is
fork meta. Do not copy it onto Core-bound slices.

## Collisions (do not "fix" by rewriting history)

1. **Dependent PRs / more than five open PRs**
   Official MUST. Local fork staging currently has `#14`, `#15`,
   `#17`–`#18`, `#23`–`#24`, `#28`–`#32`, `#34`–`#37`. That is allowed
   on the fork. Official `home-assistant/core` only gets wave 1 after
   brands, docs, and the OAuth client decision.

2. **Protocol code on PyPI**
   Official MUST. Peer `openai_conversation` also wraps `openai==2.45.0`
   in-tree. Do not extract a `spacexai` library this pass. Keep the
   client a thin async wrapper.

3. **Platinum while brands/docs 404**
   `quality_scale.yaml` already says `done` with comments pointing at
   `brands#10947` and `docs#47349`. Keep those comments. Do not flip
   `brands` / `docs-*` to `todo` on Core slices.

4. **Wave 1 size ~5.7k**
   Peers land nearer 1.3k–2.0k. Cut later by trimming exotic stream
   tests on wave 1, not by deleting production modules. Do not rewrite
   `#14` history.

5. **AI policy / human explainability**
   Autonomous official PRs and comments are forbidden. Jeff must be able
   to explain every change before anything is opened on
   `home-assistant/core`.

## Test review (12 modules)

Reviewed: `test_services.py`, `test_init.py`, `test_conversation.py`,
`test_client.py`, `test_ai_task.py`, `test_config_flow.py`,
`test_assist.py`, `test_diagnostics.py`, `test_stt_tts.py`,
`test_oauth_device.py`, `test_repairs.py`, `conftest.py`.

Accepted internals (peer pattern):

- `entity._format_tool` unit test — `openai_conversation` tests
  `_format_structured_output` the same way.
- `stream._stream_failure` unit test — classifies provider codes; keep.
- `KEY_ASSIST_PIPELINE` is a Core constant, not a SpaceXAI private.

Confirmed and fixed on `cursor/spacexai-conformance-2f69`:

- Conversation image tool did not call `snapshot.has_image_model()` at
  send time. AI Task already did. Unknown Imagine ids are now omitted
  so a stale picker value cannot fail the whole chat turn.

Left for later (not this pass):

- Wave 1 exotic stream-test trim toward ~2–2.5k.
- Public-only rewrite of `_format_tool` / `_stream_failure` tests.
- OAuth `conversations:read/write` drop needs a reauth plan first.

## Live PR map (2026-08-15)

Official: `home-assistant/core#178765` conversation — do not touch.

Fork Core-bound:

- `#14` `up-conversation` → `dev`
- `#24` gold-diagnostics → `#14`
- `#23` runtime-entitlement → `#24`
- `#18` ai-task → `#23`
- `#17` capabilities → `#18`
- `#28` device-code → `#17`
- `#29` hardening → `#28`
- `#30` full-capabilities → `#29`
- `#31` optimized-surface → `#30`
- `#32` runtime-repair → `#31`
- `#34` platinum → `#32`
- `#35` stacked tip 1–6 (review slices, not the combined view)
- `#36` grok-46 (parent of `#37`; do not rewrite)
- `#37` media-friction — required CI green; do not mark ready
- conformance tip — base `#37` / `cursor/spacexai-media-friction-2f69`

Fork meta: `#15` contribution-kit.

External: docs `#47349` (draft, URL 404), brands `#10947` (open, CDN 404).

Do not merge `#37` into `#36`.
