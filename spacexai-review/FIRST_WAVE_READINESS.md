# SpaceXAI first-wave readiness

Verified September 8, 2026. The initial Python package is published and its
post-publication checks pass. Three HA companion contributions remain prepared
for review, not submitted upstream. The contributor has confirmed reading and
understanding the initial Core code, including the generated changes. Fresh
initial-only OAuth and setup succeed. Published client 0.1.0 fails conversation
with HTTP 426; the committed, unpublished 0.1.1 candidate now passes bounded HA
acceptance. Core now prepares the matching 0.1.1 pin, with dependency transparency
explicitly `todo` until publication and verification. The next human step is
the 0.1.1 library PR and release, not upstream Core submission.

## Exact first-wave source

- Python 0.1.0: [release v0.1.0](https://github.com/jeffglousher/spacexai-subscription-client/releases/tag/v0.1.0), `155d76c5b940108be707bb379c02d476b893b758`.
- Python 0.1.1 candidate: `codex/initial-client-compatibility`, `a7f7afb514e6a0362d927124fd01b75d25885af9`; committed and pushed clean, not published.
- Core: `codex/spacexai/initial-release-0-1`, `82984cdde6d0801e2d79753ce39645bc658a3266`.
- Brands: `spacexai-initial`, `e3ac8da8bf579ec54210cc211e1eaa0768052679`.
- Docs: `codex/spacexai/docs-initial-release-0-1`, `44526b046fa26d4ddf0ab037850a54e30ecbf1d0`.

Core has four commits and retains exactly 18 changed files on the checked official dev
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
found no issues with these tests. At that checkpoint all production files were byte-identical
to `25e04203`; no runtime deployment or package release is needed for this addition.

The fourth commit, `82984cdd`, updates only the manifest's 0.1.1 requirement,
generated requirements, and dependency-transparency status. Runtime Python and
tests are unchanged. This is still one new-integration contribution, not a
separate initial Core dependency-upgrade PR.

## Historical published dependency verification — 0.1.0

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
Publication integrity does not establish live compatibility: the initial
acceptance test below found a provider version-gating failure in this release.

## Unpublished 0.1.1 correction

[Candidate CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34290919712)
passes all three Python jobs: 130 tests and 100% statement coverage each.
Local Windows Python 3.12–3.14 runs also pass 130 tests at 100%, with six clean
wheel/sdist installations, lint, typing, strict Twine, build, and preflight checks.
Independent LLM review found no blockers. The fix separates the pinned, tested
Grok Build compatibility value from the truthful package identity and sets
`store=False`; it introduces no CLI dependency and claims neither an official
third-party protocol contract nor a guarantee about other provider retention.

The locally built candidate wheel passes isolated HA chat/history, exposed-helper
control with the unexposed helper unchanged, saved-account restart followed by
chat/history, and normal removal. Its earlier native Core run passed 50 tests,
241/241 statements, without failures/errors/skips. Those live checks used an
explicit temporary override of the earlier 0.1.0 manifest pin. The current
prepared requirement is 0.1.1. See [runtime evidence](RUNTIME_VERIFICATION.md) for the exact
wheel and bounded checks. The emptied test instance is now stopped, with its
environment and evidence preserved. No 0.1.1 PR or release exists yet.

## Current Core verification

Exact Core `82984cdde6d0801e2d79753ce39645bc658a3266` is committed and pushed
clean. Native testing on the user's Linux host passes 50 tests in 2.47 seconds:
241/241 statements, 100% coverage, zero exclusions/failures/errors/skips.
Ruff check/format and dependency consistency checks pass. All 27,778 tracked
files were compared; only the three intended metadata/generated files differ
from the prior candidate. Installed client 0.1.1 matches the requirement with
no override. Hassfest reports exactly one known finding: the publication `todo`.
[Current CI 34298154970](https://github.com/jeffglousher/core/actions/runs/34298154970)
passes both jobs for exact Core `82984cdd`, client `a7f7afb5`, and installed
0.1.1: 50 tests, 241/241 statements, all four modules at 100%, Ruff, MyPy,
Pylint, and generated requirements. Unchanged native setup, full-tree general
checks, and native contribution hooks pass on all 18 contribution files.
The independent hassfest report has status `blocked_only_on_dependency_publication`,
exit 1, exactly the dependency-transparency finding, and no warnings. Green CI
is a candidate validation pass, not a completed Bronze/publication gate.
This is source-checkout validation against the fixed
`38aacedef` base, not published-artifact validation. Harness
`47cb076e7bb` defaults to this current pair and passes actionlint.
Use `spacexai-validation.yaml` for current first-wave validation; the separate
`spacexai-generated-validation.yaml` matrix is a historical fixed initial/final
checkpoint, not certification of this candidate.
The [separate matching-pin receipt](INITIAL_PIN_VALIDATION_20260908.json) records
the new run without changing the prior live receipt. Clean release-backed
validation must wait until 0.1.1 is on PyPI.

## Historical Core verification with published 0.1.0

The related suite passed locally on the user's Linux HA host in a separate
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
The Core development-checklist and perfect-PR boxes remain open: client 0.1.1
must be published and verified before the dependency rule is complete. The
manifest and generated-requirement boxes describe their prepared metadata;
they do not claim the unpublished version is available from PyPI.
The docs branch box is checked from its verified `next` base. All five Brands
asset checks are verified. Companion references now point to Core `82984cdd`.

Unchecked alternatives are intentional, not missing prose. The dependency-upgrade
comparison does not apply to adding the first version of a library. Actual
companion PR links and the docs Brands-PR checkbox must wait until those PRs exist.
The contributor previously confirmed reading and understanding the initial Core
code in response to the question that included the shutdown fix and generated
changes. Those confirmations remain recorded, but both human-review boxes are
cleared for this refreshed draft until the contributor reviews its new metadata
and generated requirement. Real-host manual testing
confirms fresh login, the published-client failure, and successful bounded
acceptance with the 0.1.1 candidate override. The new metadata now prepares that
same version; its current native verification is recorded above. The works-locally
box is checked from matching-pin native verification and unchanged runtime Python's
successful live acceptance. This is not publication or upstream readiness.
Final human review must include the metadata and library correction.
Earlier full-stack conversation/speech results remain historical, versioned
evidence, not a substitute for initial-only acceptance. The local automated-test
box is checked from the actual 50-test run on the user's Linux host. Review of
two other PRs has not been confirmed; that community contribution is not a
technical merge gate.

The Core review base remains `38aacedef`. The remote upstream `dev` check for
this checkpoint returned `ec4406798b387a6b2ed85f2bd35835d55dc4d484`; the candidate was not rebased during
this writing pass. Refresh and revalidate it before upstream submission, rather
than checking perfect-PR compliance while that and the corrected dependency's
publication and release-backed validation remain open.

### Steps before upstream submission

1. The contributor previously confirmed understanding and reviewing the earlier
   implementation and generated changes. Review this refreshed draft's dependency
   metadata and generated requirement, the library correction, final descriptions,
   and companion contributions before submission; renew review if code changes afterward.
   Do not infer completion of the separate two-other-PRs checklist item.
2. Review, create, and merge the 0.1.1 library PR, then publish through the protected
   release workflow with human approval. Its candidate is committed, pushed,
   independently reviewed, and green on all three CI Python versions. Bounded
   acceptance passes: fresh OAuth, default Assist, chat/history, exposed-helper
   control with the unexposed helper unchanged, same-account restart with further
   chat/history, and normal removal. The exposed helper was restored off; the
   isolated instance was stopped after confirming no account or conversation
   entity remains. Its environment and evidence are preserved.
   Verify the published artifacts, complete the prepared 0.1.1 dependency's
   publication rule, and rerun exact-published-dependency Core validation.
   Disabled Assist and forced forbidden-tool requests are already covered by
   deterministic tests; no repeated live outage or forced credential expiry is
   required. No live token rotation or forced-expiry success is claimed.
   Do not replace the existing full-stack instance. Earlier pending-flow
   cancellation/shutdown checks remain recorded in the runtime history.
3. After creating the companion drafts, replace comparison placeholders with
   actual PR links. Recheck the public integration logo after Brands merges.
4. Before upstream submission, recheck upstream freshness, rerun relevant
   checks if the base changes, and finish the human review gates. Do not open
   dependent follow-on upstream PRs early.

Use the [one-at-a-time fork-draft instructions](README.md#create-the-three-companion-fork-drafts).
Do not overwrite or republish 0.1.0. Any corrected release needs its own package
validation and publication, followed by exact-dependency Core verification.

## Original contribution provenance

The author closed [Core PR #178765](https://github.com/home-assistant/core/pull/178765)
unmerged; no written closure explanation or human maintainer rejection was
found. An original bot-reported OAuth timeout was reproduced and fixed in the
prepared initial source. [The pre-publication record](https://github.com/jeffglousher/core/blob/6ba2c7d337f0d4d3eb3fe036a66aa507a2fa24e6/spacexai-review/FIRST_WAVE_READINESS.md)
retains the detailed evidence; this release does not change those findings.

## Follow-ons and runtime remain separate

The [23-contribution design stack](STACK.md) is preserved. Only its initial
submission candidates were refreshed onto the new upstream tips. Later Core
layers have not inherited or retested the shutdown fix or the client's new
compatibility/storage correction. Package versions
0.2–0.5 are not published; speech/downstream also retain the independent
`has-entity-name: todo` issue. No Bronze, Gold, or Platinum award is claimed.

The existing dogfood remains `18be3997`, containing old Core `b8be5c4f` and
client `f58ec77a`; it was not replaced by the isolated initial test instance.
[Runtime evidence](RUNTIME_VERIFICATION.md) distinguishes the older full-stack
installation from the separate initial acceptance work.
