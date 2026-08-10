# SpaceXAI Core Architecture — Adversarial Review

**Subject:** `homeassistant/components/spacexai`  
**Tip:** `cursor/spacexai-full-capabilities-0109`  
**Stance:** Assume merge pressure. Prefer failure modes over compliments.  
**Scope:** Architectural choices, application structure, code paths, decisions, trade-offs, weak areas. Not PR media or contribution process.

---

## 1. System overview

SpaceXAI is a **cloud service** integration (`integration_type: service`, `iot_class: cloud_polling`) that binds one OAuth account to four capability platforms via config **subentries**.

```
┌─────────────────────────────────────────────────────────────┐
│                    Home Assistant Core                      │
│     Assist / ChatLog / LLM APIs · AI Task · STT · TTS       │
└───────────────┬───────────────────┬─────────────┬───────────┘
                │                   │             │
        ┌───────▼────────┐   ┌──────▼──────┐ ┌───▼────┐
        │ Conversation   │   │ AI Task     │ │STT/TTS │
        │ Entity         │   │ Entity      │ │Entity  │
        └───────┬────────┘   └──────┬──────┘ └───┬────┘
                │                   │            │
                └─────────┬─────────┴────────────┘
                          │
                 ┌────────▼────────┐
                 │ SpaceXAIBaseLLM │  (chat path only)
                 │ + platforms     │
                 └────────┬────────┘
                          │
                 ┌────────▼────────┐
                 │ SpaceXAIClient  │  runtime_data
                 │ + OAuth session │
                 └────────┬────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
   auth.x.ai         api.x.ai/v1        api.x.ai/v1
   (OAuth/OIDC)      Responses/SDK      images/stt/tts
                     models.list        (aiohttp)
```

| Layer | Role | Primary modules |
| --- | --- | --- |
| Config / auth | Application Credentials, browser PKCE, device code, reauth | `config_flow.py`, `oauth_device.py`, `application_credentials.py` |
| Runtime ownership | One client + model snapshot per entry | `__init__.py` → `SpaceXAIData` |
| Provider boundary | Tokens, HTTP, error taxonomy | `client.py`, `errors.py` |
| Chat engine | History convert, stream parse, tool loop | `entity.py` |
| Platforms | Conversation, AI Task, STT, TTS | `conversation.py`, `ai_task.py`, `stt.py`, `tts.py` |

External trust boundary is **total**: prompts, tool schemas, attachments, audio, and (when enabled) Assist control intents leave the host.

---

## 2. Core architectural choices (adversarial)

### 2.1 OAuth subscription identity, not API keys

| | |
| --- | --- |
| **Decision** | Application Credentials + Auth Code/PKCE **or** RFC 8628 device code. `unique_id = account.sub`. Tokens in `entry.data["token"]`. |
| **Why it fits HA** | Matches “sign in with subscription” product; device code fits headless installs. |
| **Trade-off** | Refresh, revoke, reauth, Application Credentials UX, and coarse scopes (`openid profile email offline_access grok-cli:access api:access` in `const.OAUTH_SCOPES`). |
| **Weakness** | `grok-cli:access` is product-borrowed until HA gets its own client/scopes. Over-scope is a privacy/compliance debt, not a temporary comment. |

### 2.2 Typed provider errors vs stringy failures

| | |
| --- | --- |
| **Decision** | Closed `ErrorCategory` / `Operation` taxonomy; map HTTP/SDK failures to `SpaceXAIError` subclasses; sanitize context before UI/logs. |
| **Why** | Better than OpenAI conversation’s mostly-string errors; enables reauth vs repair vs retry. |
| **Trade-off** | Classification must track live xAI quirks (e.g. credential rejection as HTTP 400). |
| **Weakness** | Substring / status heuristics (`_is_credential_rejection`, 403 → permanent) can mis-bin entitlement and billing. Dual translators (`client._error_for_status` vs `oauth_device._raise_device_http_error`) can disagree. |

### 2.3 Dual transport: OpenAI SDK + raw aiohttp

| | |
| --- | --- |
| **Decision** | SDK for `models.list` + Responses streaming; aiohttp for userinfo, Imagine, STT, TTS, revoke, device OAuth. |
| **Why** | Reuse Responses event types; cover non-SDK endpoints. |
| **Trade-off** | Two auth refresh, timeout, and parse philosophies. Pinned `openai==2.45.0` couples Core to SDK ↔ xAI drift. |
| **Weakness** | Highest long-term maintainability risk. Stream quirks (e.g. tool `name=None` on args.done) are handled inline in `entity._transform_stream`, not in a library. |

### 2.4 `store=False` + encrypted reasoning continuity

| | |
| --- | --- |
| **Decision** | Responses always `"store": False`; include `reasoning.encrypted_content`; keep reasoning as `AssistantContent.native` for replay. |
| **Why** | Privacy-first; HA owns chat state via ChatLog. |
| **Trade-off** | No provider-side threads; Imagine has no multi-turn edit continuity (unlike OpenAI’s forced store for images). |
| **Weakness** | Encrypted blobs inflate chat memory; history rebuild bugs silently poison later turns (`entity._convert_content`). |

### 2.5 One account entry, four capability subentries

| | |
| --- | --- |
| **Decision** | Parent = OAuth account; default create of conversation + AI Task + STT + TTS; add/reconfigure via subentry flows. |
| **Why** | Same pattern as `openai_conversation`; clean account uniqueness. |
| **Trade-off** | Forced full surface at install; shared `ProviderSnapshot`; reload gated by `_subentry_fingerprint`. |
| **Weakness** | Users who want TTS-only still get conversation scaffolding. Image models are **not** in the snapshot (hardcoded `IMAGE_MODELS`). |

### 2.6 Shared client + `_sdk_lock`

| | |
| --- | --- |
| **Decision** | One `SpaceXAIClient` in `runtime_data`; `asyncio.Lock` around SDK create/mutate. Platforms set `PARALLEL_UPDATES = 0` (unlimited). |
| **Why** | Single token/SDK owner. |
| **Trade-off** | Responses creates serialize under the lock; aiohttp paths do not. |
| **Weakness** | Head-of-line blocking under concurrent Assist + AI Task. Token refresh races still possible across unlocked aiohttp calls. |

### 2.7 Server-side tools as opt-in provider tools

| | |
| --- | --- |
| **Decision** | Per-conversation toggles for `web_search`, `x_search`, `code_interpreter`; streamed as external ChatLog tool results. |
| **Why** | Expose Grok server tools without HA executing them. |
| **Trade-off** | Defaults off (good). Combined with Assist `CONTROL`, one agent can both mutate the home and exfiltrate via search/code. |
| **Weakness** | Capability aggregation is the largest **user-safety** risk. Code interpreter sent as bare `{"type": "code_interpreter"}` — acceptance depends on xAI quirk, not a stable OpenAI-shaped container. |

### 2.8 Imagine as separate REST, not Responses image tool

| | |
| --- | --- |
| **Decision** | `ai_task._async_generate_image` → `client.async_generate_image` (b64 JSON). |
| **Why** | Matches xAI Imagine API; cleaner than OpenAI’s store-forcing image tool path. |
| **Trade-off** | No chat-native image edit loop; curated model list. |
| **Weakness** | `_parse_generated_image` hardcodes `mime_type="image/jpeg"`. No entitlement check against snapshot. Full bytes in memory. |

### 2.9 Soft circuit breaker via entity availability

| | |
| --- | --- |
| **Decision** | Auth/retryable errors → `_mark_unavailable`; success → `_mark_available`. |
| **Why** | Silver-scale unavailable pattern. |
| **Trade-off** | Per-entity, not account-wide. |
| **Weakness** | A 429 can mark conversation unavailable while sibling AI Task keeps burning the same quota. Recovery requires a later successful invoke. |

### 2.10 Hard-fail tool loop (`MAX_TOOL_ITERATIONS = 10`)

| | |
| --- | --- |
| **Decision** | Exceed → `ToolLoopLimitError` (fail closed). |
| **Why** | Avoids silent incomplete tool state (OpenAI conversation often just breaks). |
| **Trade-off** | AI Task uses the **same** cap. OpenAI AI Task uses a much higher iteration budget. |
| **Weakness** | Complex structured/tool-heavy AI Tasks die early — functional regression vs the reference integration. |

---

## 3. Main code paths

### 3.1 Auth (setup)

1. `SpaceXAIConfigFlow.async_step_user` → Application Credentials present  
2. Device: `oauth_device.async_request_device_authorization` → poll `async_poll_device_token`  
   **or** Browser: `AbstractOAuth2FlowHandler` + `SpaceXAIOAuth2Implementation`  
3. `async_step_validate` → `SpaceXAIClient.async_validate` (userinfo + models)  
4. `unique_id = snapshot.account.subject`; create entry + four subentries  
5. `async_setup_entry` → `OAuthAccessTokenProvider` + re-validate → `runtime_data` → forward platforms  

### 3.2 Conversation turn

1. `SpaceXAIConversationEntity._async_handle_message`  
2. User prompt + `_RUNTIME_IDENTITY_PROMPT` → `chat_log.async_provide_llm_data`  
3. `SpaceXAIBaseLLMEntity._async_handle_chat_log`  
4. `_convert_content` → tools (HA ± server tools) → optional `async_prepare_files_for_prompt`  
5. Loop: `client.async_stream_response` → `_transform_stream` → ChatLog deltas/tools  
6. HA tools execute inside ChatLog; append results; iterate until no unresponded tools or cap  
7. Success `_mark_available` / failure → translated `HomeAssistantError` ± reauth  

### 3.3 HA tool call (inside stream)

1. `ResponseOutputItemAddedEvent` (function call)  
2. `ResponseFunctionCallArgumentsDoneEvent` → `llm.ToolInput` (JSON object, id/name checks; tolerate missing `name`)  
3. ChatLog runs tool → `ToolResultContent`  
4. Next Responses iteration if still unresponded; else finish / `ToolLoopLimitError`  

### 3.4 AI Task data / image

- **Data:** `_async_generate_data` → shared chat loop + optional Responses JSON schema (`_format_structured_output`)  
- **Image:** last user text → `async_generate_image` → `GenImageTaskResult` (bytes + JPEG MIME claim)  

### 3.5 STT / TTS

- **STT:** buffer all chunks → WAV wrap in executor (PCM) → multipart `async_transcribe` → on any exception return `SpeechResultState.ERROR` (often **no log**)  
- **TTS:** merge voice/speed → `async_synthesize_speech` → empty body = malformed  

### 3.6 Reauth

Runtime credential rejection (`runtime_session=True`) → `ReauthenticationRequiredError` → `entry.async_start_reauth` + unavailable → flow must match `unique_id` → update tokens → reload.

---

## 4. Data / ownership model

| Asset | Owner | Notes |
| --- | --- | --- |
| OAuth tokens | Config entry `data["token"]` | Refresh via `OAuth2Session`; best-effort revoke on remove |
| Account identity | `unique_id` = OIDC `sub` | Mismatch → auth failed |
| Model catalog | `runtime_data.snapshot` | Chat models + aliases; **not** image models |
| Subentry config | `entry.subentries[*].data` | model, prompt, tools, tokens, image model, voice/speed |
| Reload fingerprint | `runtime_data.subentries` | Avoids reload on token-only updates |
| Chat history | HA `conversation.ChatLog` | Never provider-stored |
| Reasoning continuity | `AssistantContent.native` | Resent each turn |
| Attachments | Local paths → base64 | Filename currently host path string |
| Image bytes | Ephemeral AI Task result | Not stored with provider |
| Repair issues | Issue registry | Subscription / model not entitled |

---

## 5. Weak areas (ranked) — remediation status

Addressed on `cursor/spacexai-optimized-surface-0109` unless noted.

### Tier S — Security / privacy / safety

1. **Capability aggregation** — **Addressed:** explicit `allow_control_with_provider_tools` opt-in required when Assist APIs combine with provider tools.  
2. **Broad OAuth scopes** — **Addressed:** scopes reduced to `openid offline_access api:access`.  
3. **Attachment filename = host path** — **Addressed:** basename only via `files.py`.  
4. **Device-code polling lifetime** — **Addressed:** cancel on retry paths + `DEVICE_CODE_MAX_POLL_SECONDS` ceiling.

### Tier A — Reliability / correctness

5. **Stale entitlement snapshot** — **Addressed:** image/video models partitioned into `ProviderSnapshot`.  
6. **Hardcoded Imagine MIME = JPEG** — **Addressed:** magic-byte MIME sniff + size cap.  
7. **SDK lock + unlimited platform concurrency** — **Addressed:** lock narrowed to SDK client construct/mutate.  
8. **Per-event stream timeout** — **Addressed:** wall-clock + idle timeouts in `stream.py`.  
9. **STT silent `except Exception`** — **Addressed:** `_LOGGER.exception` + audio size cap.  
10. **Bare code_interpreter tool shape** — **Won't-fix / docs-correct:** official xAI Responses form is bare `{"type":"code_interpreter"}`.

### Tier B — Product / HA-fit

11. **AI Task tool-loop cap = 10** — **Addressed:** AI Task uses `MAX_AI_TASK_TOOL_ITERATIONS = 1000`.  
12. **Unavailable-on-429** — **Addressed:** rate limits no longer mark entities unavailable.  
13. **No media size limits** — **Addressed:** attachment/STT/image byte caps.  
14. **`entity.py` concentration** — **Addressed:** split into `stream.py` + `files.py`.  
15. **Forced four subentries** — **Addressed:** install creates conversation + AI Task; STT/TTS opt-in.  
16. **Entry-level agent registration** — **Documented:** Core API is entry-keyed (OpenAI parity); noted on conversation entity.

---

## 6. What is hard to criticize

- Clear layering: flow → `runtime_data` client → entity loop → thin platforms.  
- Error taxonomy with sanitized context is above the OpenAI integration bar.  
- Privacy-default `store=False` with encrypted reasoning round-trip is coherent, not accidental.  
- Auth state machine is thorough: setup vs runtime, account mismatch, reauth, revoke-on-remove, repair issues.  
- Stream parser is provider-adversarial: duplicate tool IDs, post-terminal events, unfinished tools, refusals, JSON args validation, missing tool names.  
- Blocking work (attachment encode, WAV wrap) pushed to the executor.  
- Subentry fingerprint avoids reload storms on token refresh.  
- Chat model discovery with aliases matches xAI catalog reality.  
- Device-code as first-class path is correct for HA installs.

---

## 7. Questions an upstream reviewer will ask

1. Can scopes shrink below `grok-cli:access` before merge?  
2. Is bare `code_interpreter` / `x_search` officially supported by xAI Responses?  
3. Why is Imagine MIME hardcoded, and why aren’t image models discovered/entitled like chat models?  
4. Should AI Task get a separate, higher iteration budget?  
5. Is unavailable-on-retryable-error intentional UX?  
6. Will Core accept permanent dual-stack transport, or must Imagine/STT/TTS unify?  
7. Official HA OAuth client timeline vs shipping Application Credentials forever?  
8. Any UI friction required before enabling Assist CONTROL together with server-side tools?  
9. Snapshot freshness policy: reload-only vs revalidate on reconfigure / periodic?  
10. Device-flow public client: is omitting `client_secret` correct for the eventual HA client?

---

## 8. Verdict

SpaceXAI is a **deliberate, privacy-leaning fork** of the OpenAI Conversation architecture with a stronger error boundary and a real OAuth/account model. The stream/auth work is careful.

The design concentrates residual risk in:

1. **Capability aggregation** (home control + outbound provider tools),  
2. **Dual-transport + SDK coupling**,  
3. **Entitlement/snapshot gaps** (especially images),  
4. **Product defaults** that look under-justified next to the care spent on parsing (tool-loop cap, JPEG MIME, broad scopes, silent STT errors).

Those four themes are where an adversarial review should spend the next engineering pass—not in rearranging platforms.
