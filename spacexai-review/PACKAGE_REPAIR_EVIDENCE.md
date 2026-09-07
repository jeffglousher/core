# Package repair evidence — 2026-09-06

The prepared Python package stack is committed and pushed to `jeffglousher/spacexai-subscription-client`. This record concerns package implementation and validation, not Home Assistant deployment or completion of PyPI account setup.

## First-wave result

Initial release branch `harden-initial-release` is at `c4fd662c281b5700a5c5d547b4afe097c8e5be22`.

- 59 tests pass locally on Python 3.14.5; statement coverage is 96.51%.
- Ruff lint and formatting and strict MyPy checks pass.
- Wheel and source distribution build; strict Twine validation passes for both.
- Both final distributions install and import in isolated environments. Installed version is 0.1.0 and the installed typing marker exists.
- [Public CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34078265048) passes at that exact commit on Python 3.12, 3.13, and 3.14, including lint, formatting, strict typing, tests, coverage, artifact builds, strict Twine checks, and isolated installation/import of both artifacts.
- Wheel metadata contains the unofficial description, Python `>=3.12`, Apache-2.0 SPDX expression, license file, source/issues/changelog links, and runtime dependencies. It contains `py.typed` and the license.
- The source distribution includes source, tests, README, changelog, release checklist, lockfile, license, and public workflows. Cache, virtual environment, and prior distributions are excluded.

Final local artifacts are under `.tmp-spacexai-client-worktree/dist/repair-20260906-final/`.

## Corrections integrated at 0.1.0

- Device-code expiry is absolute and remains unchanged when the caller resumes polling after a transient failure.
- HTTP and SDK permission failures are distinct from invalid OAuth credentials.
- OAuth slow-down responses always add five seconds, including when the existing interval already exceeds 30 seconds.
- The authorization handle retains its current polling interval across retries. A timeout doubles that interval. A connection failure preserves the existing interval.
- A polling wait cannot extend beyond the original expiry; regression tests cover expiry during the delay and retry after expiry.
- Clock tests patch the package's clock binding rather than the global time module, so asyncio's clock is unaffected.
- CI runs on all prepared package branches. CI and the release build check isolated installation of both wheel and source distribution. Publishing remains isolated in its own job with the OIDC permission.
- Build metadata declares a Hatchling minimum supporting its SPDX license metadata.

The OAuth identity and inference retry policy remain unchanged. No API-key authentication was added. Response models remain frozen; only the authorization handle carries changing protocol state.

## Follow-on layers

Every layer includes the fixes through its predecessor. Existing pushed history was preserved using follow-up commits and parent merges.

- 0.2.0, conversation attachments and provider tools: branch `spacexai/client-02-conversation`, commit `25952c5f839a30cd26e374d1eae6408fa46392c1`; 65 tests, 96.93% local coverage.
- 0.3.0, images: branch `spacexai/client-03-image`, commit `80e36af0863d5b31742fddd6edd0ccdb306f1bcc`; 93 tests, 97.93% local coverage.
- 0.4.0, speech: branch `spacexai/client-04-speech`, commit `9133ea56b89e6b35081f2bb19826bb83088582c8`; 125 tests, 98.47% local coverage.
- 0.5.0, video: branch `spacexai/client-05-video`, commit `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`; 154 tests, 98.17% local coverage.

All four layers pass local lint, formatting, strict typing, tests, wheel/source builds, and strict Twine checks. Earlier artifacts remain in each layer's `dist/repair-20260906-final/`. After the speech-stream repair, the current 0.4.0 files are `dist/spacexai_subscription_client-0.4.0-py3-none-any.whl` and `dist/spacexai_subscription_client-0.4.0.tar.gz`; current 0.5.0 files are under `dist/tts-fix-20260906/`. Do not use earlier artifacts for these two refreshed revisions. All remote branch SHAs were read back and match the local commits. All five package checkouts are clean.

Public CI also passes at every final follow-on SHA on Python 3.12, 3.13, and 3.14, including isolated installation/import of both distributions:

- [0.2.0 CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34078363848).
- [0.3.0 CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34078363629).
- [0.4.0 CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34081007042).
- [0.5.0 CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34081006987).

## Speech-stream repair integrated at 0.4.0

Dogfooding found that a single `aiohttp.StreamReader.read(n)` could return the first available network chunk, producing a truncated MP3. The library now consumes the response through EOF using bounded chunks, rejects an oversized or empty result, and does not return partial audio after an interrupted transfer. No Core adapter, OAuth identity, inference retry, or public API change was needed. The fix belongs to 0.4.0 and is merged into 0.5.0.

Four committed regression cases use a real `aiohttp.StreamReader`: delayed later chunks, timeout after an initial chunk, connection failure after an initial chunk, and a size limit exceeded by cumulative chunks. Independent bounded validation additionally confirmed exact-limit acceptance and propagation of cancellation with response-context cleanup; those extra checks are not claimed as committed regression cases.

The final public matrices pass all checks and isolated wheel/source installation on Python 3.12, 3.13, and 3.14. Python 3.14 reports 125 tests/98.47% for 0.4.0 and 154 tests/98.17% for 0.5.0. Python 3.12 and 3.13 report the same counts with 98.57% and 98.28%, respectively. This supersedes the earlier 121/150-test speech/video evidence without changing the first three package layers.

Refreshed native Home Assistant runs also pass with these exact new client revisions: Wave 4 has 101 tests, Wave 5 has 123, Wave 6 has 134, and the final Wave 7 has 137 tests plus 3 snapshots. The [final native run](https://github.com/jeffglousher/core/actions/runs/34081057144) uses Core `2315fa45b978aa1ebf637c111d0c1410d68d12ea` and client `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`, passes all scoped static checks, and reports 99.2814% aggregate coverage with every integration module above 95%. See `CORE_LINUX_EVIDENCE.md` for every exact source pair and per-module result; no full-repository suite is implied.

## Remaining publication setup

No release, PR, account setting, or PyPI publication was created during this repair.

- GitHub environment count was read as zero. Create the `pypi` environment, restrict it to `v*` tags, and configure the required human reviewer described in `RELEASING.md`.
- Configure the maintainer's PyPI account and matching pending publisher: project `spacexai-subscription-client`, owner `jeffglousher`, repository `spacexai-subscription-client`, workflow `release.yml`, environment `pypi`.
- Human review and merge of the prepared initial release to `main`, successful CI on that merged commit, and approval of release `v0.1.0` remain necessary.
- After publication, verify both PyPI files, attestations, exact tag, metadata, and installation from PyPI. Only then can Home Assistant's dependency-transparency item become done.

The detailed account and publication checklist remains in the package's tracked `RELEASING.md`. The prepared initial package PR body has current validation evidence.

## Guidance used

- [PyPA packaging tutorial](https://packaging.python.org/en/latest/tutorials/packaging-projects/): build configuration, source/wheel distributions, licensing, and clean installation.
- [PyPA pyproject guidance](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/): metadata and dependency declarations.
- [PyPI trusted publishing](https://docs.pypi.org/trusted-publishers/using-a-publisher/): separate publication job and OIDC authentication.
- [OAuth device authorization, RFC 8628 section 3.5](https://www.rfc-editor.org/rfc/rfc8628#section-3.5): minimum interval, repeated slow-down increments, timeout backoff, and expiry.
