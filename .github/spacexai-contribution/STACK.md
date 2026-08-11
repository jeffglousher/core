# SpaceXAI individual contribution stack

Domain: **`spacexai`**. Company name stays SpaceXAI; model IDs change over time and are **discovered** from the account (`models.list`), then presented in selectors. Chat, image, and video models are partitioned into `ProviderSnapshot` when the catalog exposes them; curated Imagine IDs remain as a fallback when discovery is sparse.

This folder is the **human-facing contribution kit** (fork meta only). It is **not** part of the upstream-ready Core branches. Core code lives in `homeassistant/components/spacexai/` on the `cursor/spacexai-up-*-2f69` stack. Do **not** open against `home-assistant/core` until the [HUMAN_CHECKLIST.md](HUMAN_CHECKLIST.md) blockers are cleared. Retarget notes: [UPSTREAM.md](UPSTREAM.md).

## External prerequisites (parallel, not Core commits)

| Track | Repo / branch | Content | Status artifact |
| --- | --- | --- | --- |
| Brands | `home-assistant/brands` → `master` | `core_integrations/spacexai/` from [`brands/`](brands/) | [`brands/SOURCE.md`](brands/SOURCE.md) |
| Docs | `home-assistant/home-assistant.io` → `current` | `source/_integrations/spacexai.markdown` from [`docs/spacexai.markdown`](docs/spacexai.markdown) | Front matter `ha_quality_scale: bronze` on docs PR; platinum on Core wave 8 |
| OAuth | xAI allowlist | Dedicated Home Assistant public client ID | **BLOCKER** until issued |

## Upstream-ready Core stack (canonical)

Rebuilt from `upstream/dev` (`cursor/spacexai-up-base-2f69` == `home-assistant/core` `dev`). Fork-only paths stripped (`spacexai-contribution/`, `spacexai-pr-media/`, `components/spacexai/brand/`). Former wave 8 (`brands` / `docs-*` = `done`) is **folded into wave 1** so Bronze hassfest can pass.

| Wave | Branch (fork) | Adds | Quality-scale intent |
| --- | --- | --- | --- |
| base | `cursor/spacexai-up-base-2f69` | Pin = `upstream/dev` | n/a |
| 1 | `cursor/spacexai-up-conversation-2f69` | Conversation + OAuth app credentials + client + diagnostics | `quality_scale: bronze`; `brands` + applicable `docs-*` already `done` |
| 2 | `cursor/spacexai-up-ai-task-2f69` | AI Task `GENERATE_DATA` | Same |
| 3 | `cursor/spacexai-up-capabilities-2f69` | Web search / X search / code interpreter | Same |
| 4 | `cursor/spacexai-up-device-code-2f69` | RFC 8628 device-code login + Grok CLI OAuth / CLI-proxy entitlement | Same — **needs A1 OAuth before Core** |
| 5 | `cursor/spacexai-up-hardening-2f69` | Attachments + `GENERATE_IMAGE` | Same |
| 6 | `cursor/spacexai-up-full-capabilities-2f69` | STT + TTS + Assist pipeline helpers / STT stream limits | Same |
| 7 | `cursor/spacexai-up-optimized-surface-2f69` | Optimized provider surface (defaults/`service_tier`, progressive models, reauth, diagnostics, video, adversarial) | Feature tip |
| 8 | `cursor/spacexai-up-platinum-2f69` | Raise `manifest.json` `quality_scale` to `platinum` | Declaration-only |

Legacy `-0109` branches / fork PRs `#1`–`#7`, `#12`, `#13` are **superseded** by this `up-*` cut. Do not retarget those to Core.

## Per-wave validation (every Core PR)

```bash
uv run --no-sync pytest tests/components/spacexai/ -q
uv run --no-sync prek run --all-files
python3 -m script.hassfest
python3 -m script.translations develop --integration spacexai   # if strings.json changed
```

Human checklist (do not auto-check): see [HUMAN_CHECKLIST.md](HUMAN_CHECKLIST.md).

## Feature confirmation matrix

| Surface | Covered by tests today | Live smoke |
| --- | --- | --- |
| Conversation + `llm_hass_api` | `test_conversation.py` | Assist HA control demos |
| Model discovery / selector | config flow + client model list | Reconfigure model list |
| AI Task `generate_data` | `test_ai_task.py` | Dev Tools Actions |
| AI Task `generate_image` | `test_ai_task.py` / `test_client.py` | Live OK 2026-08-10 ([#9](https://github.com/jeffglousher/core/issues/9) closed) |
| Attachments (JPEG, PDF, GIF) | `test_ai_task.py` (incl. GIF) | Assist / AI Task attach |
| Server tools | conversation tool tests | web_search Assist |
| Device code | `test_oauth_device.py` | Wait-screen capture |
| STT / TTS | `test_stt_tts.py` | Live OK with subscription bearer; selectable in Voice assistants |
| `service_tier=priority` | client + conversation tests | Live OK on CLI proxy ([#11](https://github.com/jeffglousher/core/issues/11) closed) |
| Imagine video service | client / service tests | Live OK ([#10](https://github.com/jeffglousher/core/issues/10) closed) |

Live smoke notes: [`TRACKING.md`](TRACKING.md).

**GIF note:** Imagine **output** is JPEG today (`client.py`). “Fun GIFs” are supported as **input attachments** (`image/gif`). Animated Imagine output needs a provider model + client change before it can be promised in docs.

## Assist version questions

Home Assistant’s default LLM prompt and Assist API do **not** expose Core version or the configured LLM model id. SpaceXAI appends a small runtime identity block (HA Core version + configured Grok model) so Assist can answer those questions without a new Assist tool. See `conversation.py`.

## Suggested human submission order

1. Brands edition — [brands#10947](https://github.com/home-assistant/brands/pull/10947): Ready for review → **sign CLA** → merge
2. Docs PR (`home-assistant.io` `current`) — [docs#47349](https://github.com/home-assistant/home-assistant.io/pull/47349) with `ha_quality_scale: bronze`
3. Clear **A1** OAuth client (human)
4. Core waves 1 → 8 on `home-assistant/core` `dev` using the `up-*` branches (wave 1 already includes brands/docs `done`)
5. Docs follow-up — bump `ha_quality_scale` to `platinum` with Core wave 8
