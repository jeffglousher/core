# Current runtime evidence — September 8, 2026

## Isolated initial-layer acceptance work

A separate native instance on the user's HA host now runs initial Core
`25e04203dad36c741b56ff7a789b85f6a76b7f7e`, with the published PyPI client
0.1.0. All seven installed integration source files match Git. The client wheel
hash is `2d7e8d92087afc3e72ec5839e93631284c378acd4e21121cbc60dc473c767b32`;
its source bytes were verified. All 118 previously resolved dependency versions
remained unchanged during the Core-only update; dependency checks and all four
integration module imports pass. Generated English data uses HA's own tooling.

The isolated configuration has two synthetic helpers, no copied production
credentials, and no real home devices. Normal HA API onboarding also creates
its stock default integrations; this is not a claim that only SpaceXAI loads.
The instance listens only on loopback and receives no Supervisor credentials.
The main full-stack installation below was not changed, restarted, or replaced;
its management API remained healthy after these tests.

A subsequent read-only check again confirmed one loaded SpaceXAI account with
four subentries on the real system, while the isolated initial instance remained
running with zero account entries and a pending device-authorization flow.
The contributor confirmed using the real system; the earlier successful live
conversation and speech results below remain valid evidence for that full-stack
version, not a completed fresh-login test of the initial-only candidate.

The next readiness check found that pending login had reached `device_timeout`,
with zero SpaceXAI entries. Retrying through the normal flow opened a fresh
provider approval page. The isolated instance remains running with confirmed
loopback HTTP settings. This is a specific missing successful-login test, not
evidence that an account was already configured. The main management API again
reported healthy and its SpaceXAI entry remained loaded with four subentries.

Separately, all 50 automated integration tests now pass directly on the user's
Linux HA host in a new development environment, not in either running HA venv.
The tested source matches `cd495263eed9794a02a19efb797206e4ff67ef8f`: the exact
`25e04203` archive plus its sole changed test file. Three new cases verify the
saved default/enabled/disabled Assist choice. There are zero failures/errors/skips,
241/241 statements covered, zero exclusions, and all four modules at 100%.
Native test guards and dependency pins remain unchanged; dependency checks pass.
Production source is byte-identical to the running initial-only build, so this
test-only addition requires no deployment or new Python release.
The same candidate also passes [both native CI jobs](https://github.com/jeffglousher/core/actions/runs/34260917145),
including all 50 tests, scoped checks, unchanged setup, native hooks, and clean
generated-file/publication validation.

Verified against the updated initial candidate:

- HA's native configuration check succeeds and the runtime reaches `RUNNING`.
- HTTP settings are stable, loopback-only, with no pending reversion timer.
- A real OAuth device flow reaches the approval step. Cancelling it removes
  the flow (subsequent lookup returns 404), with no SpaceXAI account created.
- Stopping HA with another pending device flow terminates the process and
  closes its listener, with zero late device-poll shutdown warnings in that run.
- Restart succeeds and the empty SpaceXAI configuration remains empty.

The first setup trial exposed HA's HTTP configuration safety rollback: an
unconfirmed configuration reverts and requests restart after five minutes.
That stopped trial was preserved. The subsequent configuration was confirmed
through HA's supported HTTP configuration API, without editing stored state.
Its shutdown also exposed a separate SpaceXAI task-ownership defect, corrected
in `25e04203`. [Native run 34251664631](https://github.com/jeffglousher/core/actions/runs/34251664631)
passes all 47 tests with 100% statement coverage, scoped checks, native setup,
standard hooks, and generated/publication validation. The new public regression
fails against the old production code and passes with the fix. This proves
earlier cancellation, not a measured long shutdown delay.

Fresh provider approval is now awaiting the user on the provider's sign-in page.
The current device endpoint is [SpaceXAI Accounts](https://accounts.x.ai/oauth2/device);
the private device code is not included here. This is not completed HA frontend
or fresh-login acceptance. The finite remaining live sequence is conversation
and history, control of the exposed synthetic helper while the unexposed helper
stays unchanged, restart followed by conversation, and account removal.
Disabled Assist and forced forbidden-tool requests already have deterministic
coverage; reproducing every provider failure live is not required.
These remaining successful-account checks need fresh provider approval.
No quality-tier award is claimed.

## Unchanged full-stack deployment — September 7, 2026

The timeout-corrected full stack is deployed and running. This is an
existing-account dogfood deployment, not proof of a fresh initial-only
OAuth installation. This deployment still uses client `f58ec77a` below;
the September 8 package expiry-arithmetic fix at `376fe0c9` has not been deployed.

## Exact source and deployment

- Dogfood branch: `codex/spacexai/dogfood-staged-20260907`.
- Dogfood commit: `18be39973b1361ebe23605dc4a605ae0d69cff43`.
- Canonical final Core: `b8be5c4f783900a8e50db8cb577756d4f8901136`, an ancestor
  of dogfood.
- Client 0.5.0: `f58ec77aebff01fe6bf4b72e97a2370b023647a2`.
- Integration development version: `0.9.0.dev20260907`.
- Existing HA base remains `2026.10.0.dev202608300226`; no base-image,
  security, or stored-credential changes were made.

The reviewed production correction changes two existing timeout-handler lines
in final Core. Only the development manifest version and exact source
requirement pin differ from the canonical integration. All 17 archived files
were byte-compared against Git, and 13 deployed runtime hashes matched.
Compiled translations were verified against unchanged source and the retained
generated English file. The archive was generated without Windows newline
conversion and verified before activation.

[Exact full-stack native validation](https://github.com/jeffglousher/core/actions/runs/34175318077)
and independent re-review passed before activation. Configuration check and
restart passed. Redacted runtime inspection confirmed running state, the
existing OAuth entry loaded, all four platform subentry types, and the exact
development version/source pin. The protected Core container does not expose
installed dependency-file hashes through the SSH app, so this is not an
independent installed-wheel hash check. Exactly one SpaceXAI overlay is active.
The previous overlay is retained outside the custom-components scan directory
for rollback; current credentials were kept.

## Bounded live checks on the new deployment

- Conversation and AI text returned the expected generic responses; together
  they took 9.00 seconds.
- A fresh uncached TTS request returned 34,176 bytes in 0.55 seconds. Complete
  FFmpeg decoding produced 2.136 seconds of audio: 68,352 bytes at 16 kHz,
  mono, 16-bit PCM.
- STT of that exact decoded speech succeeded with the expected normalized
  sentence in 0.53 seconds. This confirms complete audio, not only a media URL
  or first network chunk.
- The 100 available log lines contained zero SpaceXAI errors. This is a bounded
  log inspection, not a whole-lifetime no-error claim.

No image or video regeneration was performed in this batch, and no home
device was controlled. Their native tests pass; earlier live image/video
artifacts below belong to the historical deployment. No real provider outage
or forced credential expiry was induced on the running test system; timeout
failure/recovery is covered by the native public-interface regressions.

Speech entity naming remains quality-blocked despite functional TTS/STT
success. Initial-only acceptance is now being tested separately as recorded
above; the fresh human OAuth approval remains pending. No tokens, entry
identifiers, host addresses, signed URLs, raw logs, or private audio are
included here.

[The previous September 7 runtime record](https://github.com/jeffglousher/core/blob/40e9dc4893fb663b38649145e47e0f7c9bfec019/spacexai-review/RUNTIME_VERIFICATION.md)
retains its own source identities and measurements for dogfood `85ac0fd099cd`.
Its overlay and smoke artifacts were preserved; new receipts use the new
commit ID.

## Historical prior deployment and live checks

The record below concerns dogfood `ae2897793bc9498a0d5714286d57dc21afdc912a`,
old Core `2315fa45b978aa1ebf637c111d0c1410d68d12ea`, and old client
`b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`. It preserves earlier
attribution and is superseded as current runtime status.

# Assembled-stack live verification

Verified September 6, 2026, America/Chicago. This is a test-system result, not an
upstream merge, PyPI publication, or quality-tier award.

- Pushed dogfood branch: `codex/spacexai/dogfood-current-dev`.
- Deployed commit: `ae2897793bc9498a0d5714286d57dc21afdc912a`.
- Canonical final Core ancestor: `2315fa45b978aa1ebf637c111d0c1410d68d12ea`.
- Exact installed package source: `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`, version 0.5.0.
- Custom integration development version: `0.9.0.dev20260906`.

The deployment was checked against committed source hashes. English translations
were generated with Home Assistant's translation tool, including reference
resolution. The configuration check passed, Home Assistant restarted, and the
existing OAuth entry loaded with conversation, AI Task, STT, and TTS entities.
Exactly one integration overlay was present. Backups were kept outside the
custom-component scan directory; no stored credential edits were needed.

## Live results

- Conversation and AI Task text returned the exact requested generic sentence.
- Image generation produced the requested blue circle on white. The saved JPEG
  was retrieved through an authenticated signed Home Assistant media route,
  matched the local file, and was visually inspected.
- Independent recorded speech was successfully transcribed to the expected text.
- A one-second video request produced an H.264 MP4; signed retrieval and a full
  FFmpeg decode succeeded, yielding 25 frames and approximately 1.04 seconds.
- An initial TTS request exposed a real library bug: the response ended after
  the first available chunk, yielding only 768 bytes of audio.
- The fix reads through end-of-stream within the size limit and rejects partial
  success after timeout or connection failure. It was committed at the speech
  package layer, carried forward, tested, pushed, and redeployed.
- The fixed uncached TTS request returned a complete 31,488-byte MP3, decoded at
  24 kHz mono for approximately 1.97 seconds. Converting that exact audio to PCM
  and sending it through STT returned the exact normalized expected sentence.
- Conversation and AI Task text passed again after the final restart. The loaded
  entry, exact fixed dependency pin, and single overlay were rechecked.

## Limits

These are bounded live smoke tests, not a soak test or proof of every possible
provider response, language, voice, tool, or account state. Image and video were
not regenerated after the speech-only package fix; their implementation did not
change. The full automated Core and package suites cover the final source pairs.

The initial Core-only scope was tested separately on native Linux; the live
installation deliberately contains the entire assembled stack. Its source URL
pin and development version are dogfood-only and must not enter an upstream PR.
Raw runtime inventory, credentials, deployment logs, and media artifacts remain
private and are not included in this packet.
