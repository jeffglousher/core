# Current verified runtime — September 7, 2026

The rebuilt full stack is deployed and running. This is an existing-account
dogfood deployment, not proof of a fresh initial-only OAuth installation.

## Exact source and deployment

- Dogfood branch: `codex/spacexai/dogfood-staged-20260907`.
- Dogfood commit: `08b259eed599e5d0e15a386d015244afa2221bba`.
- Canonical final Core: `298a208679829f70a8c6c424d1ab5471e8c6da15`, an ancestor
  of dogfood.
- Client 0.5.0: `5bfafeceeca8a32ae6ace6d4471764c64ff86d69`.
- Integration development version: `0.9.0.dev20260907`.
- Existing HA base remains `2026.10.0.dev202608300226`; no base-image,
  security, or stored-credential changes were made.

Only the development manifest version and exact source requirement pin differ
from the canonical integration. All 17 archived files were byte-compared
against Git, and 13 deployed runtime hashes matched the remote files.
Compiled translations were verified from the exact source.

Configuration check and restart passed. Redacted runtime API inspection
confirmed running state, the existing OAuth entry loaded, all four platform
subentry types, and the exact development version/source pin. Exactly one
SpaceXAI overlay is active. The previous overlay is retained outside the
custom-components scan directory for rollback; current credentials were kept.

## Bounded live checks on the new deployment

- Conversation and AI text returned the expected generic responses; together
  they took 8.08 seconds.
- A fresh uncached TTS request returned 34,176 bytes in 0.68 seconds. Full
  FFmpeg decoding produced 2.136 seconds of audio: 68,352 bytes at 16 kHz,
  mono, 16-bit PCM.
- STT of that exact decoded speech succeeded with the expected normalized
  sentence in 0.28 seconds. This confirms complete audio, not only a media URL
  or first network chunk.
- The 100 available log lines contained zero SpaceXAI errors. This is a bounded
  log inspection, not a whole-lifetime no-error claim.

No paid image or video regeneration was performed in this batch, and no home
device was controlled. Their new native success/failure tests pass; the earlier
live image/video artifacts below belong to the previous deployment. Do not
relabel those old smokes as running this exact new stack.

The speech entity-naming quality gate remains unresolved despite functional
TTS/STT success. A fresh initial-only Home Assistant setup and human OAuth login
still require an isolated native host. No tokens, entry identifiers, host
addresses, signed URLs, raw logs, or private audio are included here.

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
