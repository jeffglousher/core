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

Fat tip PR #8 content redistributed and tip branch aligned to wave 7 (cursor/spacexai-optimized-surface-0109 @ 4d72a4a3).

| Wave | Branch tip ownership after rebuild |
| --- | --- |
| 4 | Device-code + Grok CLI OAuth / CLI-proxy entitlement |
| 5 | Attachments + Imagine |
| 6 | STT/TTS + Assist helpers + STT size limits |
| 7 | Optimized surface (defaults, UI, brands, video, adversarial) |
| tip #8 | Closed; empty vs wave 7 |

Backup: tag ackup/spacexai-tip-pre-rebuild (963d538f).

