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
