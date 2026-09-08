# SpaceXAI first-wave readiness

Verified September 8, 2026. The initial Python package is published and its
post-publication checks pass. Three HA companion contributions remain prepared
for review, not submitted upstream. The contributor has confirmed reading and
understanding the initial Core code, including the generated changes. Fresh
initial-only UI/OAuth acceptance and final submission checks still remain.

## Exact first-wave source

- Python 0.1.0: [release v0.1.0](https://github.com/jeffglousher/spacexai-subscription-client/releases/tag/v0.1.0), `155d76c5b940108be707bb379c02d476b893b758`.
- Core: `codex/spacexai/initial-release-0-1`, `cd495263eed9794a02a19efb797206e4ff67ef8f`.
- Brands: `spacexai-initial`, `e3ac8da8bf579ec54210cc211e1eaa0768052679`.
- Docs: `codex/spacexai/docs-initial-release-0-1`, `44526b046fa26d4ddf0ab037850a54e30ecbf1d0`.

Core has three commits and exactly 18 changed files on the checked official dev
`38aacedef39eb3f077ce4a112a58bf7286af5e2c`. Docs has one commit and one 96-line
page on official next `1b359d16aca5ba2c6b7983fa36c8c5f2334c5c5a`.
Both candidates and their fixed fork review bases are pushed. The prior staged
branches and review bases were preserved, not rewritten or deleted.

The initial replay `7a41a035` preserved the prepared runtime/tests and marked
`dependency-transparency` done. The additive `25e04203` fix uses HA's background
task ownership for device polling so shutdown cancels it at the stop stage;
one public shutdown regression was added. No provider behavior, package version,
or initial scope changed. Generated additions preserve the recorded upstream files.
No initial API migration was identified. The docs page is byte-identical to
`0a5a5dfb`. Recheck upstream freshness at actual submission time.

The third commit, `cd495263`, adds only three parameterized public-flow tests:
omitted Assist selection defaults to enabled, explicit enabled selection is
saved, and explicit disabled selection stays disabled. An independent review
found no issues with these tests. All production files remain byte-identical
to `25e04203`; no runtime deployment or package release is needed for this addition.

## Published dependency verification

[Package PR #1](https://github.com/jeffglousher/spacexai-subscription-client/pull/1)
is merged. Its merge/release tree exactly matches the reviewed `e3269374` source.
[Release run 34243434378](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34243434378)
passes source preflight, Python 3.12/3.13/3.14 release checks, and publishing.
Each Python job passes 127 tests with 100% statement coverage. GitHub records
`jeffglousher` approving the protected `pypi` environment, consistent with the
user's confirmation; no agent approval was performed.

[PyPI 0.1.0](https://pypi.org/project/spacexai-subscription-client/0.1.0/) provides
both unyanked distributions with the expected version, Apache-2.0 license,
Python >=3.12, and project links. Downloaded hashes, exact wheel members, and
required distribution source bytes match the release. Strict Twine passes.

Both files pass official cryptographic attestation verification plus explicit
checks for the signed repository, workflow, tag, release SHA, issuer, and event.
The `pypi` environment is supported by publisher metadata and GitHub approval
records; it is not claimed as cryptographically bound by the verifier.

All six clean post-publication wheel/sdist installations pass on Windows with
Python 3.12.13, 3.13.15, and 3.14.5, including version, public import, typing,
non-editable installation, and exact runtime bytes.
[Package evidence](PACKAGE_REPAIR_EVIDENCE.md) includes hashes and limitations.
This does not re-attest private account security or human license review.

## Current Core verification

The related suite now passes locally on the user's Linux HA host in a separate
development virtual environment: 50 tests, zero failures/errors/skips,
241/241 statements (100%), zero exclusions, and all four modules at 100%.
The source is the exact `25e04203` archive with the sole changed test file from
`cd495263`. The run uses HA's native fixtures and unchanged socket/task safeguards,
single-process `uv run --no-sync pytest`, and the published client 0.1.0.
Dependency consistency checks pass. Neither running HA environment was modified.
This is genuine local automated-test evidence, not a CI run renamed as local.

[Fresh native CI 34260917145](https://github.com/jeffglousher/core/actions/runs/34260917145)
passes both jobs for the full `cd495263` commit identifier: all 50 integration
tests, 100% statement coverage, scoped lint/formatting/MyPy/Pylint, unchanged
development setup, full-tree general hooks, standard contribution hooks, and
clean generated-file/publication validation. The first invocation,
34260599438, supplied an abbreviated ID that checkout treated as a branch/tag
pattern; it failed before tests or setup ran. That invocation is not a code failure.

### Previous production revision verification

[Native run 34251664631](https://github.com/jeffglousher/core/actions/runs/34251664631)
passes the integration job for exact Core `25e04203` with actual PyPI 0.1.0,
verified against release `155d76c5`: 47 tests, zero failures/errors/skips,
241/241 statements (100%), zero exclusions, and all four modules at 100%.
Scoped lint, formatting, MyPy, and Pylint pass. Its negative control runs the
new shutdown test against old `7a41a035` production and produces exactly one
expected failure: cancellation occurs at `not_running`, not `stopping`.
The fixed source is restored before all 47 tests pass. This demonstrates late
cancellation, not a measured long shutdown delay.

The same run also passes unchanged script/setup, the full-tree general-hook
subset, standard native hooks on all contribution files, and generated wiring
and publication validation. Both jobs are successful for the new head.
Harness `15adcb71e31a2ade8db05463da95498082537634` records this verification.
The prior results below remain historical rather than being relabeled.

### Historical release-backed replay verification

[Native run 34244844613](https://github.com/jeffglousher/core/actions/runs/34244844613)
tests Core `7a41a035` with release `155d76c5` using the actual PyPI package.
The scoped job passes 46 tests, zero failures/errors/skips, and 241/241 statements
(100%), with zero missing or excluded statements. Every initial module is 100%.
Ruff, formatting, native MyPy/Pylint, and requirements regeneration pass.

The installed package has no direct-URL/editable metadata and all six runtime
files match the release checkout. The checkout is a verification reference,
not the installed dependency. No local wheelhouse substitutes for PyPI.

[Generated run 34244846528](https://github.com/jeffglousher/core/actions/runs/34244846528)
passes the initial layer with genuinely clean hassfest: exit 0, no findings or
warnings, status `passed`, and no tracked generated-file changes.
The publication exception is not accepted in PyPI mode. Its separate final
stack job still fails only the unpublished-version and speech-naming rules;
that result is not an initial failure or a full-stack approval.

The same exact-source native run also passes unchanged script/setup, the
upstream full-tree general-hook subset, and standard hooks on all 18 contribution
files, including unskipped hassfest. Its strict generated result is also
`passed`, with exit 0 and no findings or tracked changes. The wheelhouse build
is skipped and `UV_FIND_LINKS` is empty in this PyPI-backed run.
The Windows setup attempt cannot activate the POSIX environment layout, and
the local all-files hook attempt fails during uv cache initialization. Local
full hooks are not claimed; the successful native Linux run is the proof.

Coverage measures statements, not branches or every possible behavior.
OAuth device authorization and the approved identity remain unchanged.
The initial integration remains conversation-only and the unofficial library
owns provider communication; no framework layer or new package was introduced.

## Documentation and Brands

The refreshed initial docs page passes local and native remark/textlint with
unchanged content. [Native run 34245078515](https://github.com/jeffglousher/core/actions/runs/34245078515)
builds exact initial docs `44526b04` with the prescribed Jekyll task and passes
the complete Brands validator at `e3ac8da8`: 19,231 images, zero issues.
All four workflow jobs pass. Its final docs and blueprint jobs retain their
older exact sources; they are not evidence for the new initial Core candidate.

The older initial docs preview was visually inspected at desktop/mobile widths.
The new rendered page has identical markup except for one generated doc-data
script reference; all 79 retained non-HTML preview files are byte-identical.
The referenced doc-data scripts are absent from both partial preview artifacts,
so this supports the previous layout baseline, not complete asset equivalence
or a fresh interactive inspection. Public integration logo delivery remains
pending the Brands merge.

## Remaining first-wave gates

### Draft descriptions and checkboxes

The three initial descriptions now contain concise purpose, scope, and testing
summaries. Every original template comment, heading, field, and checkbox is
retained; their source templates still match the official repositories.
The Core development-checklist and manifest boxes are checked from the published
dependency, enabled issue tracker, generated wiring, and native validation.
The docs branch box is checked from its verified `next` base. All five Brands
asset checks are verified. Companion references now point to Core `cd495263`.

Unchecked alternatives are intentional, not missing prose. The dependency-upgrade
comparison does not apply to adding the first version of a library. Actual
companion PR links and the docs Brands-PR checkbox must wait until those PRs exist.
The contributor has now confirmed reading and understanding the current Core
code in response to the question that included the shutdown fix and generated
changes. Both Core review attestations are checked. The manual locally-tested
box is also checked: real-host initial lifecycle checks and successful full-stack
conversation/speech tests are recorded, with their versions and limits explicit.
This general manual-testing checkbox is not the separate fresh initial-only
acceptance gate. The local automated-test box is now checked from the actual
50-test run on the user's Linux host. Review of two other PRs has not been confirmed.

The Core review base remains `38aacedef`. A fresh read of upstream `dev` returned
`15f231017997bef66540416ef82b2011cbd4cb5f`; the candidate was not rebased during
this writing pass. Refresh and revalidate it before upstream submission, rather
than checking perfect-PR compliance while that and live acceptance remain open.

### Steps before upstream submission

1. The contributor has confirmed understanding and reviewing the current Core
   code and generated changes. Review the final descriptions and companion
   contributions before submission; renew that review if code changes afterward.
   Do not infer completion of the separate two-other-PRs checklist item.
2. Complete fresh initial-only browser OAuth login on the separate native
   instance. Exact `25e04203` matches all seven source blobs; 118 dependencies
   and PyPI client 0.1.0 are unchanged, and import/dependency checks pass.
   Configuration validation exits 0, HA is running on loopback-only HTTP,
   and there are no SpaceXAI entries. Real OAuth start reaches device progress;
   cancel yields verified 404 and no entry. Stopping during a second pending
   authorization exits with the process absent, port closed, and no reported
   late-device-task warning; restart returns to running. The first-party
   provider sign-in page awaits human approval. This is not completed login or
   HA UI setup. Verify
   conversation/history, control of the exposed synthetic helper with the
   unexposed helper unchanged, restart/token persistence, and removal.
   Disabled Assist and forced forbidden-tool requests are already covered by
   deterministic tests; no repeated live outage or forced credential expiry is
   required. Existing full-stack credentials are
   not fresh-login proof. Human OAuth approval is still needed; do not replace
   the existing full-stack instance.
3. After creating the companion drafts, replace comparison placeholders with
   actual PR links. Recheck the public integration logo after Brands merges.
4. Before upstream submission, recheck upstream freshness, rerun relevant
   checks if the base changes, and finish the human review gates. Do not open
   dependent follow-on upstream PRs early.

Use the [one-at-a-time fork-draft instructions](README.md#create-the-three-companion-fork-drafts).
No further library tag, release, or publication is needed for this wave.

## Original contribution provenance

The author closed [Core PR #178765](https://github.com/home-assistant/core/pull/178765)
unmerged; no written closure explanation or human maintainer rejection was
found. An original bot-reported OAuth timeout was reproduced and fixed in the
prepared initial source. [The pre-publication record](https://github.com/jeffglousher/core/blob/6ba2c7d337f0d4d3eb3fe036a66aa507a2fa24e6/spacexai-review/FIRST_WAVE_READINESS.md)
retains the detailed evidence; this release does not change those findings.

## Follow-ons and runtime remain separate

The [23-contribution design stack](STACK.md) is preserved. Only its initial
submission candidates were refreshed onto the new upstream tips. Later Core
layers have not inherited or retested the new shutdown fix. Package versions
0.2–0.5 are not published; speech/downstream also retain the independent
`has-entity-name: todo` issue. No Bronze, Gold, or Platinum award is claimed.

The existing dogfood remains `18be3997`, containing old Core `b8be5c4f` and
client `f58ec77a`; it was not replaced by the isolated initial test instance.
[Runtime evidence](RUNTIME_VERIFICATION.md) distinguishes the older full-stack
installation from the separate initial acceptance work.
