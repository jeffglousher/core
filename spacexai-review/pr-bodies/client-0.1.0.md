# Prepare spacexai-subscription-client 0.1.0

## Purpose

Prepare the first public release of `spacexai-subscription-client`, an explicitly unofficial, small asynchronous Python client for the OAuth-authenticated Grok subscription surface used by the Home Assistant SpaceXAI integration.

The package owns provider communication so the Home Assistant integration remains a thin adapter. It implements OAuth device authorization, token polling, account identity, entitled model discovery, Responses API messages, and local function-tool calls. Authentication is OAuth-only: the public API does not accept an API key and has no API-key fallback.

## Design

- Accept caller-owned `aiohttp` and `httpx` sessions instead of creating hidden long-lived sessions.
- Keep the public Grok CLI OAuth identity and provider endpoints in one constants module so a future xAI identity decision does not change the public API.
- Normalize provider payloads into immutable typed response models; retain device authorization expiry and polling backoff in its reusable authorization handle.
- Translate authentication failures, permission failures, authorization denial, device-code expiry, rate limits, timeouts, connection failures, and malformed responses into stable package exceptions.
- Bound provider requests with explicit timeouts and disable SDK retries so callers own retry policy.
- Create request-scoped SDK clients so refreshed OAuth credentials cannot race through shared mutable state.
- Validate provider tool calls before exposing them to callers.
- Honor OAuth slow-down responses and preserve the increased polling interval across retries. Timeout backoff remains bounded by the original device-code expiry.

## Verification

- 59 tests pass on Python 3.14 locally with 96.51% statement coverage.
- [Public CI at the reviewed commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34078265048) passes on Python 3.12, 3.13, and 3.14.
- Ruff lint and format checks pass.
- Strict MyPy checks pass.
- The wheel and source distribution build successfully and pass `twine check --strict`.
- CI installs and imports both distributions in isolated environments on every supported Python version.
- The wheel contains `py.typed`; both distributions contain the Apache-2.0 license.
- The locked direct and transitive runtime dependency licenses were audited for Home Assistant compatibility.
- GitHub Issues are enabled. Public CI runs on the prepared branches; the release workflow is configured for PyPI trusted publishing.
- The build job has read-only repository access; only the isolated publish job receives `id-token: write`.

## Release

After human review, merge this PR, confirm CI on `main`, configure the `pypi` environment with a required human reviewer and a matching PyPI pending publisher, and publish GitHub release `v0.1.0`. The release workflow verifies that the tag matches `pyproject.toml`, validates and installs both artifacts, and publishes `spacexai-subscription-client==0.1.0` to PyPI through Trusted Publishing.

The package has not been published. The GitHub publishing environment and PyPI pending publisher still need account setup before the release is ready to approve.

Release notes: https://github.com/jeffglousher/spacexai-subscription-client/blob/harden-initial-release/CHANGELOG.md

Publication checklist: https://github.com/jeffglousher/spacexai-subscription-client/blob/harden-initial-release/RELEASING.md

## Out of scope

- Home Assistant integration code.
- API-key authentication.
- Attachments, image, video, and speech APIs; those remain isolated follow-on releases.
