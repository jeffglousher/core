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
- Validate provider tool-call identifiers, argument objects, and names against the custom functions offered in that request before exposing them to callers.
- Normalize malformed Responses payloads and numeric OAuth expiry/interval overflow into `InvalidResponseError`. An explicitly supplied token type must be Bearer (case-insensitive); an omitted type retains existing Bearer compatibility.
- Honor OAuth slow-down responses and preserve the increased polling interval across retries. Timeout backoff remains bounded by the original device-code expiry.

## Verification

- Two named public OAuth regressions cover oversized JSON integer expiry values in device authorization and token polling. Timestamp arithmetic now shares the existing `InvalidResponseError` normalization; no new abstraction or HA runtime change was needed.

- Real-SDK HTTP transport regressions cover malformed provider fields, unoffered function calls, valid text, and valid offered calls. These synthetic robustness cases do not imply an observed provider outage; the approved OAuth identity and login flow are unchanged.
- 120 tests pass on Python 3.14 locally with 96.62% statement coverage.
- [Public CI at the prepared commit](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34229759065) passes at `410730d2c9803d2a4c83cdeb6ebe7f1f2c0b9dd3` on Python 3.12, 3.13, and 3.14.
- Ruff lint and format checks pass.
- Strict MyPy checks pass.
- The wheel and source distribution build successfully and pass `twine check --strict`.
- CI installs and imports both distributions in isolated environments on every supported Python version.
- The wheel contains `py.typed`; both distributions contain the Apache-2.0 license.
- Retained machine evidence records 25 runtime dependency names, versions, and license metadata on `win32` with Python 3.14.5. This does not establish human license-compatibility approval or cover every platform; that review remains pending.
- GitHub Issues are enabled. Public CI runs on the prepared branches; the release workflow is configured for PyPI trusted publishing.
- The build job has read-only repository access; only the isolated publish job receives `id-token: write`.

- All three Python jobs validate the wheel member set, required wheel/sdist source bytes, release identity, typing marker, license, and isolated imports. The count includes 36 release-contract tests. Extra or duplicate wheel members are rejected; the sdist check is not a universal archive-security audit.
- Release automation requires the exact release SHA to equal current `main` at preflight, a matching version tag, nonempty versioned changelog notes, and a successful exact-SHA three-Python matrix before the isolated publisher can run. Human review is a separate requirement; it is not inferred from ancestry or green CI.

## Release

After genuine maintainer review, merge the reviewed package to `main`, confirm its CI, and have the account owner verify PyPI security and the matching pending publisher. With explicit release authorization, create `v0.1.0` from that exact current-main commit. Wait for preflight and all three release-check jobs, then obtain the maintainer's `pypi` environment approval. An agent must not provide that approval. The release path itself has not been exercised by publishing.

The package is unpublished and the prepared code has not been merged to `main`. GitHub controls are configured and independently verified: a tag-only `v*` publishing environment requiring `jeffglousher` with administrator bypass disabled, protected `main` with three strict Python checks, and version-tag update/deletion protection. These controls do not attest human code review.

Current `main` remains `40e8a3bd46653eecbb6269eb7e59cc9ecf91f75c` with the legacy release workflow; the prepared exact-source and artifact safeguards are not active there until the reviewed source is merged. PyPI account security and pending-publisher binding remain unverified—the account page currently requires sign-in. No release or environment approval has been performed.

Release notes: https://github.com/jeffglousher/spacexai-subscription-client/blob/410730d2c9803d2a4c83cdeb6ebe7f1f2c0b9dd3/CHANGELOG.md

Publication checklist: https://github.com/jeffglousher/spacexai-subscription-client/blob/410730d2c9803d2a4c83cdeb6ebe7f1f2c0b9dd3/RELEASING.md

## Out of scope

- Home Assistant integration code.
- API-key authentication.
- Attachments, image, video, and speech APIs; those remain isolated follow-on releases.
