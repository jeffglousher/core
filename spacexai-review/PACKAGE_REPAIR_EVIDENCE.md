# Current package boundary and release evidence — September 7, 2026

The following exact prepared heads supersede the package SHAs/counts in the
historical record below. All are pushed; main is not merged and no version
has been published.

- Version 0.1.0: `b5513112b12a14baa43c295cf82cec8be3604ba7`; 118 tests, 96.59% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174829112).
- Version 0.2.0: `fc13749a2d9befa62b9581ccd4e3a60a9ef3c54e`; 127 tests, 96.99% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992495).
- Version 0.3.0: `44e84f8b4962dfd52098f5520655bdddc3def88b`; 155 tests, 97.96% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992428).
- Version 0.4.0: `b6b1d7d301b66bd29e24d2c0c309fa3e775f9881`; 187 tests, 98.49% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992423).
- Version 0.5.0: `f58ec77aebff01fe6bf4b72e97a2370b023647a2`; 216 tests, 98.19% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34174992203).

All fifteen public Python jobs pass lint/format, strict MyPy, tests, wheel/sdist
builds, strict Twine, the wheel-member/required-source contracts, and isolated imports.
Coverage above is from Python 3.14.5; the same test counts pass on all three
versions. Python 3.12/3.13 coverage is 96.85%, 97.23%, 98.11%, 98.59%, and
98.30% in release order. Every job's test, artifact contract, strict Twine,
and isolated wheel/sdist installation steps were read back as successful.
All five remote branch heads match local Git; all package checkouts are clean.

The 36 release-contract tests exercise invalid source/tag/main combinations,
missing release notes, missing or unexpected wheel members, duplicate wheel
names, changed required source bytes, metadata mismatches, and extra distributions.
Eight new cases failed before this repair and pass afterward. The wheel allows
only the package source, typing marker, license, and standard METADATA/WHEEL/RECORD
members produced by the actual builds; duplicate names are rejected before reads.
Required source bytes are also checked in the sdist, without claiming a universal
archive-security audit or exhaustive WHEEL/RECORD content validation.

The latest additive initial commit and parent merges changed only
`script/check_release.py`, `tests/test_release.py`, and `RELEASING.md`.
Exact comparisons against the preceding provider-boundary checkpoint confirm
runtime source, package versions, metadata, lockfile, and workflows are unchanged
in all five layers. The previously repaired provider behavior below remains
included. Independent read-only review found no issue in this narrow change.
Release workflow actionlint 1.7.12 evidence remains from the preceding,
unchanged workflow revision.

## Provider-boundary repairs

The initial layer now converts malformed consumed SDK response fields into
`InvalidResponseError`, validates nonempty string function-call IDs/names and
JSON argument objects, and rejects custom function names absent from the
request. Real OpenAI SDK decoding through an in-memory HTTP transport reproduces
the former uncaught `TypeError` cases and unoffered-call acceptance. It also
verifies valid text and offered calls; no provider requests were made by these
regressions. Home Assistant still owns tool exposure and execution permissions.

Explicit OAuth token types must be case-insensitive Bearer; missing token type
retains existing compatibility. Non-finite expiry/interval conversion errors are
normalized to `InvalidResponseError`. These are synthetic robustness cases, not
an observed provider outage. The initial suite adds 23 regression cases.

At 0.2.0 the offered-name set includes only custom `Tool` objects, not provider
`BuiltinTool` objects. Three additional real-SDK regressions preserve hosted-only
and mixed hosted/custom output, and prove that enabling a built-in tool does not
authorize a same-named local function. All later releases inherit both repairs.
The existing complete, bounded speech-stream implementation is unchanged and
its real-aiohttp regressions still pass.

Local Python 3.14.5 checks also pass full tests, Ruff lint/format, strict MyPy,
wheel/sdist builds, strict Twine, artifact contracts, and separate isolated
installation/import of each artifact. The generic `prek` command could not run
in the package environment because `prek` is not installed; it is not claimed as
a completed check. The package's declared CI checks all pass.

## Release gates

Release preflight checks the actual release SHA against main at preflight and the
version/changelog contract. Publisher gating requires the complete exact-SHA
three-Python matrix; only the isolated publisher receives OIDC permission.
The wheel member set and required package-source bytes are checked. The sdist
check covers required source, tests, scripts, docs, workflows, lock, and license
bytes. Builds/imports run independently for both artifacts.

During the preceding release-hardening validation, the prepared-source
preflight was exercised against main
`40e8a3bd46653eecbb6269eb7e59cc9ecf91f75c` and correctly rejected the
unmerged prepared release. This does not replace human review: ancestry,
source equality, and CI cannot establish that a person understands the code.

GitHub controls are now configured and independently verified. The retained
local receipt `PUBLICATION_CONTROLS_20260907.json` records the 2026-09-08
00:56:47 UTC readback: the `pypi` environment accepts only `v*` tags,
requires `jeffglousher`, and disables administrator bypass. Protected `main`
requires a PR and the three strict GitHub Actions Python checks, enforces the
rules for administrators, and blocks force pushes/deletion. The `v*` tag
ruleset blocks updates/deletion with no bypass actors. It does not prohibit tag
creation or establish GitHub release-asset immutability.

The sole maintainer can approve their own environment deployment, and the
required PR approval count is zero; neither setting establishes independent
human code review or distinguishes a person from an agent using their account.
An agent must never supply the maintainer's code-review attestation or deployment
approval. No such approval or publication was performed.

Current `main` is still `40e8a3bd46653eecbb6269eb7e59cc9ecf91f75c` with
the legacy release workflow. The prepared initial source `b5513112b12a14baa43c295cf82cec8be3604ba7`
contains the exact-current-main preflight and complete matrix/artifact contract;
those prepared guarantees are not active on main until genuine human review and
merge. The environment gate covers both inspected workflows.

Retained local `PACKAGE_RUNTIME_LICENSES_20260907.json` records 25 actual
runtime dependency names, versions, and raw license metadata on `win32` with
Python 3.14.5, together with the extraction code and `uv tree --locked --no-dev`
output. Its lockfile SHA-256 is
`a87e2ff2ca6f9f87735c0154add9d6a2a43a96f089de09bc88428bb46134c1e8`.
This is reproducible machine evidence, not completed human compatibility review
or proof covering every operating system, Python version, or optional extra.

Remaining work: genuine maintainer code and license-compatibility review; merge
reviewed source to main; account-owner verification of PyPI security and the exact
pending Trusted Publisher binding; explicit release authorization and human
environment approval; publication; and PyPI metadata, provenance, distributions,
and clean-install verification afterward. Private PyPI account state remains
unverified: the available account page requires sign-in. The publisher has not
been exercised by a release.

[Current release checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/b5513112b12a14baa43c295cf82cec8be3604ba7/RELEASING.md)
and [current stack proof](STAGED_READINESS.md) distinguish these gates from
completed automated checks. Follow-on releases inherit the same safeguards.

## Historical provider-boundary checkpoint — September 7, 2026

These previously successful runs precede the publication-only wheel-contract
repair. They are historical evidence, not the current prepared source heads.

- Version 0.1.0: `f12b460dffecff7ce4f2827fffa8351e06cadcb6`; 110 tests, 96.59% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34168803786).
- Version 0.2.0: `573e22c48b9e182ab27fcc0d3d4027d0e9e4a142`; 119 tests, 96.99% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169272336).
- Version 0.3.0: `f98151c06729b7bb5a930bc863075cc396b25bf6`; 147 tests, 97.96% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169495197).
- Version 0.4.0: `b29c66df6833a2527fa4835aef10c46c26ed49ed`; 179 tests, 98.49% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169671109).
- Version 0.5.0: `b6087bbd49428839cc4db845f0c5ec33ef3025fd`; 208 tests, 98.19% statement coverage; [three-Python CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34169834827).

## Historical package repair record

The text below preserves earlier source/test/runtime attribution. Those SHAs
and old successful runs are historical, not the current five prepared heads.

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
