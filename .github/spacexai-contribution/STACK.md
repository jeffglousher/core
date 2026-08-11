# SpaceXAI individual contribution stack

Domain: **`spacexai`**. Company name stays SpaceXAI; model IDs change over time and are **discovered** from the account (`models.list`), then presented in selectors. Chat, image, and video models are partitioned into `ProviderSnapshot` when the catalog exposes them; curated Imagine IDs remain as a fallback when discovery is sparse.

This folder is the **human-facing contribution kit**. Core code still lives in `homeassistant/components/spacexai/` on the fork stack. Do **not** open against `home-assistant/core` until the [HUMAN_CHECKLIST.md](HUMAN_CHECKLIST.md) blockers are cleared. Retarget notes: [UPSTREAM.md](UPSTREAM.md).

## External prerequisites (parallel, not Core commits)

| Track | Repo / branch | Content | Status artifact |
| --- | --- | --- | --- |
| Brands | `home-assistant/brands` → `master` | `core_integrations/spacexai/` from [`brands/`](brands/) | [`brands/SOURCE.md`](brands/SOURCE.md) |
| Docs | `home-assistant/home-assistant.io` → `current` | `source/_integrations/spacexai.markdown` from [`docs/spacexai.markdown`](docs/spacexai.markdown) | Front matter `ha_quality_scale: bronze` on docs PR; platinum on Core wave 9 |
| OAuth | xAI allowlist | Dedicated Home Assistant public client ID | Blocker until issued |

## Core stack (fork today → `home-assistant/core` `dev` when ready)

Each wave starts from the final quality bar for **code** and only adds capability. Tests, hassfest, ruff, mypy, and the development checklist apply to every wave.

| Wave | Branch (fork) | Adds | Quality-scale intent |
| --- | --- | --- | --- |
| 1 | `cursor/spacexai-conversation-0109` | Conversation + OAuth app credentials + client + diagnostics | Bronze code `done`; `brands` + bronze `docs-*` stay `todo` with comments pointing at this kit |
| 2 | `cursor/spacexai-ai-task-0109` | AI Task `GENERATE_DATA` | Same docs/brands todos |
| 3 | `cursor/spacexai-capabilities-0109` | Web search / X search / code interpreter | Same |
| 4 | `cursor/spacexai-device-code-0109` | RFC 8628 device-code login + Grok CLI OAuth / CLI-proxy entitlement | Same |
| 5 | `cursor/spacexai-hardening-0109` | Attachments + `GENERATE_IMAGE` | Same |
| 6 | `cursor/spacexai-full-capabilities-0109` | STT + TTS + Assist pipeline helpers / STT stream limits | Same |
| 7 | `cursor/spacexai-optimized-surface-0109` | Optimized provider surface: defaults/`service_tier`, progressive models, reauth merge, diagnostics, brands, video service, adversarial hardening | Feature tip |
| 8 | `cursor/spacexai-quality-docs-brands-0109` | No feature code — flip `brands` + all applicable `docs-*` to `done`; sync contribution-kit tracking | Unblocks hassfest bronze certification |
| 9 | `cursor/spacexai-quality-platinum-0109` | Raise `manifest.json` / docs `ha_quality_scale` to platinum (code Platinum rules already `done`) | Declaration-only after wave 8 |

Wave 7 ships the feature tip and contribution-kit assets. Waves 8–9 are declaration-only quality flips. External brands + docs PRs should land (or be draft-linked) alongside wave 8.

Wave 1’s PR body should link the brands + docs PRs (even as drafts). Later feature waves do not rewrite earlier ones.

## Per-wave validation (every Core PR)

Run from a Core checkout of that wave tip:

```bash
uv run --no-sync pytest tests/components/spacexai/ -q
uv run --no-sync prek run --all-files   # or the scoped hooks from .vscode/tasks.json
python3 -m script.hassfest
python3 -m script.translations develop --integration spacexai   # if strings.json changed
```

Human checklist (do not auto-check):

- [ ] Author understands and can explain the diff ([AI policy](https://developers.home-assistant.io/docs/ai_policy))
- [ ] CLA signed for the submitting GitHub account
- [ ] PR template fully filled; unchecked boxes left visible
- [ ] No fork-only demo media required upstream (`.github/spacexai-pr-media/` may be omitted from upstream PRs)
- [ ] Application Credentials + device-code smoke against a real subscription

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

Home Assistant’s default LLM prompt and Assist API do **not** expose Core version or the configured LLM model id. SpaceXAI now appends a small runtime identity block (HA Core version + configured Grok model) so Assist can answer those questions without a new Assist tool. See `conversation.py`.

## Suggested human submission order

1. Brands PR (`home-assistant/brands`) — draft from `jeffglousher/brands`
2. Docs PR (`home-assistant.io` `current`) — `ha_quality_scale: bronze` initially
3. Core wave 1 → … → 7 stacked on `home-assistant/core` `dev`
4. Wave 8 quality flip (`cursor/spacexai-quality-docs-brands-0109`)
5. Wave 9 declare Platinum (`cursor/spacexai-quality-platinum-0109`)
