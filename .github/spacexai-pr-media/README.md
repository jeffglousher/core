# SpaceXAI PR media (fork drafts only)

Screenshots/GIFs for draft PR review on `jeffglousher/core`.
Not used by Home Assistant at runtime. Remove before upstream submission if undesired.

Each wave has **one unique still + one unique GIF** that exercises only that PR’s new capability.
Complexity increases from PR #1 → #7. Do not reuse assets across PRs.

| PR | Still | GIF | What was exercised live |
|---|---|---|---|
| #1 Conversation | `pr1_assist_ha_control.webp` | `pr1_assist_ha_control.gif` | Assist with Grok + HA `assist` API controlling demo lights |
| #2 AI Task | `pr2_ai_task_generate_data.webp` | `pr2_ai_task_generate_data.gif` | `ai_task.generate_data` returning a real task payload |
| #3 Server-side tools | `pr3_tools_web_search.webp` | `pr3_tools_web_search.gif` | Conversation `web_search` ON + Assist answer with live sources |
| #4 Device-code login | `pr4_device_code_wait.webp` | `pr4_device_code_wait.gif` | RFC 8628 wait screen (`verification_uri` + user code) |
| #5 Attachments + image | `pr5_imagine_and_attach.webp` | `pr5_imagine_and_attach.gif` | `ai_task.generate_image` (Imagine) result in UI |
| #6 STT + TTS | `pr6_voice_pipeline.webp` | `pr6_voice_pipeline.gif` | Voice pipeline with Grok STT/TTS/Conversation (+ `tts.speak`) |
| #7 Optimized surface | *(capture)* `pr7_priority_and_video.webp` | *(capture)* `pr7_priority_and_video.gif` | `service_tier=priority` Assist + `spacexai.generate_video` URL |

`spacexai.markdown` in this folder mirrors
[`.github/spacexai-contribution/docs/spacexai.markdown`](../spacexai-contribution/docs/spacexai.markdown)
for draft PR review.

Raw GitHub embeds are pinned to the media commit on `cursor/spacexai-conversation-0109`
(`9127ae8c876ad701a9bed7cd8586734f06c982d6`) so CDN branch URLs cannot serve a stale corrupt blob:

`https://raw.githubusercontent.com/jeffglousher/core/9127ae8c876ad701a9bed7cd8586734f06c982d6/.github/spacexai-pr-media/<file>`
