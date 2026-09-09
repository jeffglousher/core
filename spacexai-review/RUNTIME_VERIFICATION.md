# Current runtime evidence — September 8, 2026

Current Core `82984cdde6d0801e2d79753ce39645bc658a3266` requires client 0.1.1
and keeps its publication rule open. Its matching-pin native run passes all
50 tests with 241/241 statements covered and no failures/errors/skips; installed
candidate 0.1.1 matches the requirement without an override. Only three metadata/
generated files changed, not runtime Python. See [current readiness](FIRST_WAVE_READINESS.md)
and the [separate matching-pin receipt](INITIAL_PIN_VALIDATION_20260908.json)
for the validation scope. The live receipt below is preserved history: it tested
the same client candidate with an explicit override of the older Core pin.
The test service remains stopped; this packet update did not deploy new code.

## Historical isolated initial-layer acceptance

A separate native test instance on the user's HA host used initial Core production
`25e04203dad36c741b56ff7a789b85f6a76b7f7e`, now with the unpublished client 0.1.1
candidate from `a7f7afb514e6a0362d927124fd01b75d25885af9`. Its locally built
candidate wheel SHA-256 is
`33e45dd66a5c3e23058bab8a2dd6cc68ad609b62939981a49abbee753ca362d2`.
All six installed client files match that wheel and its Windows working-tree
source; all seven Core source files remain unchanged. The local source uses
CRLF while Git/Linux uses LF, so this hash does not predict a future Linux-built
release wheel. Only client 0.1.0 → 0.1.1 changed in the isolated runtime and
development-test environment; dependency checks pass. The live test used the explicit
temporary `--skip-pip-packages spacexai-subscription-client` override because
that tested manifest pinned 0.1.0. This was not a released-dependency check.
Generated English data uses HA's own tooling. Final state: the disposable
account is removed and the empty test service is stopped. The installed
environment and evidence are preserved; the main HA service remains healthy.

The isolated configuration has two synthetic helpers, no copied production
credentials, and no real home devices. Normal HA API onboarding also creates
its stock default integrations; this is not a claim that only SpaceXAI loads.
The instance listens only on loopback and receives no Supervisor credentials.
The main full-stack installation below was not changed, restarted, or replaced;
its management API remained healthy after these tests.

An earlier read-only check confirmed one loaded SpaceXAI account with
four subentries on the real system, while the isolated initial instance remained
running with zero account entries and a pending device-authorization flow.
The contributor confirmed using the real system; the earlier successful live
conversation and speech results below remain valid evidence for that full-stack
version, not a completed fresh-login test of the initial-only candidate.

The next historical readiness check found that pending login had reached `device_timeout`,
with zero SpaceXAI entries. Retrying through the normal flow opened a fresh
provider approval page. At that checkpoint the isolated instance had confirmed
loopback HTTP settings but no successful login. The main management API again
reported healthy and its SpaceXAI entry remained loaded with four subentries.

### Published 0.1.0 failure and candidate correction

Fresh provider approval in external Chrome completed through HA's normal flow.
HA created one loaded account entry and one conversation subentry with default
Assist enabled and selected model `grok-4.6`. A normal stop, clean termination,
and restart returned HA to running with stable loopback HTTP settings. The same
saved account and conversation subentry loaded, with Assist control still enabled.
This verifies saved-credential persistence, not live token rotation.

The first synthetic chat failed with HA's translated API error. A separate call
through the exact published client 0.1.0, using the same model and no tools,
also returned HTTP 426 (Upgrade Required). The provider's plain-text response
identifies `0.1.0` as an outdated Grok CLI version and requires at least `0.1.202`.
The package sends its own version as `x-grok-client-version`; the official
[sampler uses this header for proxy version gating](https://github.com/xai-org/grok-build/blob/75810042ca2762aa0b0fa17864f3f68823ccbea5/crates/codegen/xai-grok-sampler/src/client.rs#L554).
Its [version source describes the installed CLI build](https://github.com/xai-org/grok-build/blob/75810042ca2762aa0b0fa17864f3f68823ccbea5/crates/codegen/xai-grok-version/src/lib.rs#L1),
not a documented third-party protocol version. The published initial package is
functionally blocked despite passing automated tests and publication checks.

A separate process changed only that header to `1.0.24`, the pinned official
[source-build version](https://github.com/xai-org/grok-build/blob/75810042ca2762aa0b0fa17864f3f68823ccbea5/crates/codegen/xai-grok-version/Cargo.toml#L4),
while retaining the truthful `0.1.0` package User-Agent and unofficial identifier.
It returned the expected synthetic text. That earlier probe alone did not prove
HA acceptance. The subsequent 0.1.1 candidate adds this compatibility declaration,
keeps a truthful 0.1.1 User-Agent and unofficial identifier, and requests
`store=False`. It makes no official protocol or general retention guarantee.

### Current candidate acceptance

With the locally built wheel above, actual HA conversation and history pass in
8.72 seconds, with default Assist control enabled. A native tool call and
successful result control the exposed synthetic helper; the unexposed helper
remains unchanged. The exposed helper was restored off.

A normal stop terminates the process and closes its listener with zero late
device-task warnings. Restart loads the same saved account and conversation
subentry with default Assist still enabled; chat/history pass again in 9.29
seconds. Normal API removal then succeeds without requiring restart: no SpaceXAI
account remains and its conversation entity is removed. The isolated instance
was confirmed running with stable loopback settings, then stopped normally for
housekeeping. Final checks confirm process absent, port closed, and zero late
shutdown warnings. Only this disposable account was removed; no files or the
main HA account were removed. No live token rotation or forced expiry is claimed. The cause of earlier
in-app approval attempts remaining pending has not been established; external
Chrome succeeded.

[Candidate package CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34290919712)
passes all three Python jobs with 130 tests and 100% statement coverage each,
including Linux-built wheel/sdist installation checks. Local Windows Python
3.12–3.14 runs also pass 130 tests at 100%; six clean artifact installations,
lint, typing, strict Twine, build/preflight, and independent review pass. The
candidate is committed and pushed clean, but no PR or release exists. Its
isolated native Core replay passes 50 tests, 241/241 statements, without failures,
errors, or skips. The main HA remains healthy with its one loaded account and
four subentries, unchanged by candidate installation or acceptance testing.

The next human step is to review/create/merge the 0.1.1 library PR, then approve
its protected release. Verify those published artifacts, complete Core's dependency
publication rule, and revalidate against the released package; the temporary override
and local wheel cannot establish that gate.

Before the candidate installation, all 50 automated integration tests passed on the user's
Linux HA host in a new development environment, not in either running HA venv.
The tested source matches `cd495263eed9794a02a19efb797206e4ff67ef8f`: the exact
`25e04203` archive plus its sole changed test file. Three new cases verify the
saved default/enabled/disabled Assist choice. There are zero failures/errors/skips,
241/241 statements covered, zero exclusions, and all four modules at 100%.
Native test guards and dependency pins remain unchanged; dependency checks pass.
Production source is byte-identical to the running initial-only build, so this
test-only addition requires no deployment or new Python release.
That Core revision with published 0.1.0 also passes [both native CI jobs](https://github.com/jeffglousher/core/actions/runs/34260917145),
including all 50 tests, scoped checks, unchanged setup, native hooks, and clean
generated-file/publication validation.

Historical pre-login lifecycle checks against the updated initial candidate:

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

Disabled Assist and forced forbidden-tool requests already have deterministic
coverage; reproducing every provider failure live is not required.
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
above; bounded candidate acceptance passes, while the published dependency
remains blocked by HTTP 426.
No tokens, entry
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
