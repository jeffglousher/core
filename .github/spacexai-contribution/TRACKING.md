# SpaceXAI open tracking (fork issues)

Issues are enabled on `jeffglousher/core` for product gaps that need live
subscription verification before docs can promise them.

| Issue | Topic | Status |
| --- | --- | --- |
| [#9](https://github.com/jeffglousher/core/issues/9) | Imagine image generation under device-code OAuth | **Validated 2026-08-10** — `ai_task.generate_image` returned JPEG via `grok-imagine-image-quality` |
| [#10](https://github.com/jeffglousher/core/issues/10) | Imagine video generation under device-code OAuth | **Validated 2026-08-10** — `spacexai.generate_video` returned mp4 URL (`grok-imagine-video-1.5`) |
| [#11](https://github.com/jeffglousher/core/issues/11) | `service_tier=priority` on `cli-chat-proxy` | **Validated 2026-08-10** — proxy response included `"service_tier": "priority"` |

## Live HA note

Config entry re-added cleanly after remove. Recommended defaults observed in
`.storage`:

| Setting | Conversation / Assist | AI Task |
| --- | --- | --- |
| `max_output_tokens` | 3000 | 8192 |
| `temperature` / `top_p` | 1.0 / 1.0 | 1.0 / 1.0 |
| `service_tier` | `priority` | `default` |
| STT / TTS | Entities present and selectable | n/a |

## Live smoke matrix (2026-08-10)

| Surface | Result |
| --- | --- |
| Conversation | OK (`priority validation ok`) |
| AI Task `generate_data` | OK structured `{ok:true,n:1}` |
| AI Task `generate_image` | OK JPEG media source |
| `spacexai.generate_video` | OK provider mp4 URL |
| TTS (`tts.grok_tts`) | OK mp3 proxy URL |
| STT (`api.x.ai/v1/stt`) | OK HTTP 200 with subscription bearer |
| Assist preferred pipeline | Uses `conversation.grok`; speech engines remain HA Cloud / Google Translate (selectable) |
| Brands | Replaced incorrect placeholder pack with official SpaceXAI symbol assets from `data.x.ai` |

Speech/Imagine repair copy only fires when `api.x.ai` actually rejects the session.

## Adversarial tip follow-ups (applied)

- Assist matches pipelines by conversation engine only (no name hijack)
- Assist wires SpaceXAI STT/TTS when those entities exist
- `/models` auth failures abort setup; sparse catalogs still degrade gracefully
- Video status polling refreshes the OAuth access token each loop
- STT aborts while streaming once `MAX_STT_AUDIO_BYTES` is exceeded
- AI Task image attachments enforce `MAX_IMAGE_BYTES`
- Install-only `create_stt` / `create_tts` / `default_assist` are stripped from conversation subentry data
- AI Task missing `service_tier` defaults to standard, not Assist priority
- Diagnostics cover speech platforms + media model lists
- `spacexai.generate_video` service tests added


## Stack rebuild (2026-08-10)

Fat tip PR #8 content redistributed and tip branch aligned to wave 7
(`cursor/spacexai-optimized-surface-0109`).

| Wave | Branch tip ownership after rebuild |
| --- | --- |
| 4 | Device-code + Grok CLI OAuth / CLI-proxy entitlement |
| 5 | Attachments + Imagine |
| 6 | STT/TTS + Assist helpers + STT size limits |
| 7 | Optimized surface (defaults, UI, brands, video, adversarial) |
| tip #8 | Closed; empty vs wave 7 |

Backup: tag `backup/spacexai-tip-pre-rebuild` (`963d538f`).

Post-rebuild live smoke on HAOS overlay (entry `01KZNWZ4M5NPYCS51ADZBDVBKS`):

| Surface | Result |
| --- | --- |
| Conversation | OK (`stack rebuild ok`) |
| AI Task `generate_data` | OK structured `{ok:true,n:1}` |
| Diagnostics defaults | Assist `3000`/`priority`; AI Task `8192`/`default` |
| OAuth scopes | Includes `conversations:read` / `conversations:write` |
| Platforms loaded | conversation + ai_task + stt + tts |

Post-rebuild pytest (HAOS host Alpine clone `/mnt/data/pytest-spacexai/core`):

| Check | Result |
| --- | --- |
| `uv run --no-sync pytest tests/components/spacexai/ -q` | **240 passed** @ `e6a4691e` (reconfirmed after tip test fixes) |
| Tip branch vs wave 7 | Identical empty tip (`cursor/spacexai-device-flow-fix-2f69` == wave 7) |
| Follow-up fixes | Install Assist/STT/TTS toggles preserved through finalize; tip tests aligned to 403→subscription gate, video poll mock queue, model-entitlement setup; Assist reload syncs Grok STT/TTS onto owned pipelines without re-forcing preferred |

Live Assist wiring (after tip `4ae2d711` + HA Core restart): preferred pipeline `GH` now uses `conversation.grok` + `stt.grok_stt` + `tts.grok_tts` (previously Cloud STT / Google Translate TTS). Overlay note: custom_components deploys need `"version"` in `manifest.json` or HA blocks the integration.

## Upstream-ready cut (2026-08-11)

Rebuilt from `upstream/dev` as `cursor/spacexai-up-*-2f69`. Former wave 8
(brands/docs `done`) folded into wave 1. Platinum is wave 8.

| Wave | Branch | Fork draft PR | Notes |
| --- | --- | --- | --- |
| base | `cursor/spacexai-up-base-2f69` | — | == `upstream/dev` |
| 1 | `cursor/spacexai-up-conversation-2f69` | [#14](https://github.com/jeffglousher/core/pull/14) | Bronze + brands/docs `done` |
| 2 | `cursor/spacexai-up-ai-task-2f69` | [#18](https://github.com/jeffglousher/core/pull/18) | AI Task |
| 3 | `cursor/spacexai-up-capabilities-2f69` | [#17](https://github.com/jeffglousher/core/pull/17) | Server tools |
| 4 | `cursor/spacexai-up-device-code-2f69` | [#16](https://github.com/jeffglousher/core/pull/16) | Device-code + CLI OAuth (**A1 blocker**) |
| 5 | `cursor/spacexai-up-hardening-2f69` | [#21](https://github.com/jeffglousher/core/pull/21) | Attachments / Imagine |
| 6 | `cursor/spacexai-up-full-capabilities-2f69` | [#19](https://github.com/jeffglousher/core/pull/19) | STT/TTS/Assist |
| 7 | `cursor/spacexai-up-optimized-surface-2f69` | [#22](https://github.com/jeffglousher/core/pull/22) | Feature tip |
| 8 | `cursor/spacexai-up-platinum-2f69` | [#20](https://github.com/jeffglousher/core/pull/20) | `quality_scale: platinum` |
| kit | `cursor/spacexai-contribution-kit-2f69` | [#15](https://github.com/jeffglousher/core/pull/15) | This folder only (not for Core) |

Legacy `-0109` fork PRs `#1`–`#7`, `#12`, `#13` are **closed** as superseded by the `up-*` drafts.

External drafts:

| Track | PR | Notes |
| --- | --- | --- |
| Brands | [`brands#10947`](https://github.com/home-assistant/brands/pull/10947) | `core_integrations/spacexai/` pack |
| Docs | [`docs#47349`](https://github.com/home-assistant/home-assistant.io/pull/47349) | bronze front matter; platinum docs follow Core wave 8 |

Host validate (Alpine clone `/mnt/data/pytest-spacexai/core` on tip `up-platinum` @ `7588c0cf`):

| Check | Result |
| --- | --- |
| Fork-only paths absent | kit / pr-media / `brand/` clean |
| Manifest | `quality_scale: platinum` |
| `quality_scale.yaml` | `brands: done` (folded from former wave 8) |
| `pytest tests/components/spacexai/ -q` | **241 passed** |
| `hassfest --plugins quality_scale` | Invalid integrations: **0** |

