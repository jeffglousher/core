# SpaceXAI first-wave review packet

Current packet: September 8, 2026. Python 0.1.0 is published and verified.
The remaining contributions are initial Core, Brands, and documentation.
These are prepared for human review on your forks; no companion PR was opened.
Published 0.1.0 fails conversation with HTTP 426. The committed 0.1.1 candidate
passes bounded initial-only HA acceptance, but is not published and Core still
pins 0.1.0. The next human step is the library correction, not Core.

OAuth device authorization remains the only login path. There is no API-key
fallback or runtime Grok CLI dependency.

## Completed: Python 0.1.0 publication

[Package PR #1](https://github.com/jeffglousher/spacexai-subscription-client/pull/1)
is merged. [Release v0.1.0](https://github.com/jeffglousher/spacexai-subscription-client/releases/tag/v0.1.0)
and [PyPI 0.1.0](https://pypi.org/project/spacexai-subscription-client/0.1.0/)
come from `155d76c5b940108be707bb379c02d476b893b758`, whose tree exactly matches
the reviewed source. Both distribution files passed source-byte and cryptographic
attestation checks; all six clean wheel/sdist installations passed on Python
3.12–3.14. [Publication evidence](PACKAGE_REPAIR_EVIDENCE.md) records the scope.

Do not recreate the merged 0.1.0 draft or republish that version.

## Next: review the Python 0.1.1 correction

Review the [completed PR write-up](pr-bodies/python-01-compatibility.md) and
[candidate diff](https://github.com/jeffglousher/spacexai-subscription-client/compare/main...codex/initial-client-compatibility)
at `a7f7afb514e6a0362d927124fd01b75d25885af9`, then create and merge its library
PR after review. No 0.1.1 PR or release has been created.
[CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34290919712)
passes all three Python jobs: 130 tests and 100% statement coverage each.
Local Python 3.12–3.14 checks, six clean artifact installations, and independent
code review also pass. After merging, publish through the protected release
workflow with human approval. Only then update Core's pin and rerun its
exact-published-dependency checks. The temporary live-test override is not a
shipping dependency change.

<a id="create-the-three-companion-fork-drafts"></a>

## Prepared Core fork draft — after the corrected dependency is published

For the later Core step, read its [write-up](pr-bodies/core-01-initial.md)
and [exact diff](https://github.com/jeffglousher/core/compare/codex/spacexai/review-base-release-0-1...codex/spacexai/initial-release-0-1)
and make sure you understand the change before creating the draft.

The title is **Add SpaceXAI conversation integration**. This command creates a
draft in `jeffglousher/core`, not `home-assistant/core`. Its absolute body-file
path works from any directory on this device. It is provided for you to run;
it has not been executed.

```shell
gh pr create --draft --repo jeffglousher/core --base codex/spacexai/review-base-release-0-1 --head codex/spacexai/initial-release-0-1 --title "Add SpaceXAI conversation integration" --body-file "C:/Users/jeffg/dev/core/.worktrees/spacexai-validation/spacexai-review/pr-bodies/core-01-initial.md"
```

Share the resulting Core draft URL before proceeding to the next contribution.
Your Core code-understanding and generated-code-review confirmations are now
recorded. The 0.1.1 candidate passes bounded live checks, but the published-client
correction and Core dependency update remain outstanding. Creating this fork
draft is not upstream submission.
The [checkbox notes](FIRST_WAVE_READINESS.md#draft-descriptions-and-checkboxes)
explain which items are verified, which do not apply, and which still need
actual testing, PR creation, or your personal confirmation.

## Queued companions

Keep these separate for later, one-at-a-time review and creation:

- **Add SpaceXAI integration branding** — [write-up](pr-bodies/brands-01-initial.md), [preview](https://github.com/jeffglousher/brands/compare/codex/spacexai/review-base...spacexai-initial).
- **Document the SpaceXAI conversation integration** — [write-up](pr-bodies/docs-01-initial.md), [preview](https://github.com/jeffglousher/home-assistant.io/compare/codex/spacexai/review-base-release-0-1...codex/spacexai/docs-initial-release-0-1).

The Core candidate contains three commits: the initial integration, its focused
shutdown fix, and three Assist-choice setup tests. Docs contains one commit. Their checked official upstream
bases are `38aacedef39eb3f077ce4a112a58bf7286af5e2c` and
`1b359d16aca5ba2c6b7983fa36c8c5f2334c5c5a`. Their new fixed review-base branches
produce exactly 18 Core files and one docs page. Brands retains its existing
fixed base `2751989265f1e13fa596dbdec9363b7bed0f0f48` and eight assets.

All old staging branches and review bases are preserved. Do not use the fork
default branches or move these fixed review bases. Replace companion comparison
links with actual draft PR links after you create them.

## Readiness and boundaries

[First-wave readiness](FIRST_WAVE_READINESS.md) records the current checks and
remaining gates. Current Core `cd495263eed9794a02a19efb797206e4ff67ef8f` passes
50 related tests locally on the user's Linux HA host, with zero failures,
errors, or skips and 241/241 statements covered (100%, zero exclusions).
The three new tests verify default, enabled, and disabled Assist settings saved
through the real configuration flow. Production files are unchanged from `25e04203`.
[Fresh native CI](https://github.com/jeffglousher/core/actions/runs/34260917145)
passes both jobs for this exact revision, including all 50 tests, scoped checks,
unchanged setup, native hooks, and generated-file validation. The previous
[native integration job](https://github.com/jeffglousher/core/actions/runs/34251664631)
passes 47 tests with 241/241 statements covered (100%, zero exclusions).
The new test fails against the previous production code and passes with the fix.
The same run also passes unchanged native setup, full-tree general hooks,
standard contribution hooks, and clean generated/publication validation.
These automated checks remain valid; they did not detect the live proxy's
client-version rejection of published 0.1.0.

Fresh OAuth in external Chrome now completes on the isolated native instance
at `25e04203`. HA saves one loaded account and one conversation subentry with
default Assist enabled. A normal restart preserved that same entry and subentry;
this does not prove token rotation. The first chat failed with HTTP 426. A separate
call using the exact published client, selected `grok-4.6`, and no tools fails
identically: the provider interprets version `0.1.0` as an outdated CLI build
and requires at least `0.1.202`.

The locally built 0.1.1 candidate wheel is installed only in the isolated runtime and
its development-test environment. Only the client version changed; all seven
Core source files remain unchanged. Native Core tests pass again: 50 tests,
241/241 statements, no failures/errors/skips. Live chat/history pass in 8.72
seconds; Assist controls the exposed helper through a native tool call/result,
while the unexposed helper stays unchanged. The exposed helper was restored off.
Normal restart preserves the same account/subentry and chat/history pass again
in 9.29 seconds. Normal removal deletes the disposable account and conversation
entity without requiring restart. The empty isolated instance was then stopped
normally; its process is absent and port closed, with zero late-task warnings.
[Runtime evidence](RUNTIME_VERIFICATION.md) records the wheel and temporary
override; the [redacted receipt](INITIAL_LIVE_ACCEPTANCE_20260908.json) records
the bounded results. Upstream submission remains on hold for publication, the corrected
Core pin and validation, upstream freshness, and human review. Public logo
delivery still needs checking after the Brands merge.

[The 23-contribution design stack](STACK.md) remains preserved. The new initial
submission candidates do not claim that all later layers were replayed onto
today's upstream. The shutdown fix still needs carrying into those later layers
and retesting; no all-stack green claim is made. Package versions 0.2–0.5 remain
unpublished; speech and later Core layers retain the separate
`has-entity-name: todo` blocker. No Bronze,
Gold, or Platinum award is claimed.

[Current native evidence](STAGED_READINESS.md) distinguishes the release-backed
first wave from historical source-checkout runs. [Runtime verification](RUNTIME_VERIFICATION.md)
separates the isolated initial checks from the earlier full-stack deployment:
dogfood `18be3997`, Core `b8be5c4f`, and client `f58ec77a`.
This work did not redeploy or replace that full stack.

Under [Home Assistant's AI policy](https://developers.home-assistant.io/docs/ai_policy),
a human must review, understand, and be able to explain every submitted change.
Private credentials, host inventory, raw deployment logs, and media samples
are excluded from this public packet.
