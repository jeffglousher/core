# SpaceXAI first-wave readiness

Verified September 7, 2026. The four initial contributions are implemented,
validated, and prepared for human review. They are not upstream-ready:
publication, human review, fresh initial-login proof, and a new docs visual
check remain. No upstream PR or package release was opened by this work.

## Exact first-wave source

- Python 0.1.0: `harden-initial-release`, `f12b460dffecff7ce4f2827fffa8351e06cadcb6`.
- Core: `codex/spacexai/staged-01-initial`, `1be5415320b9f511d568df7990d5f32ffb0df0df`.
- Brands: `spacexai-initial`, `e3ac8da8bf579ec54210cc211e1eaa0768052679`.
- Docs: `codex/spacexai/staged-docs-01-initial`, `0a5a5dfb0f779bf027b609781c5117cc78f9d3a7`.

All four are pushed to the corresponding jeffglousher forks. Core is based on
official dev `be2e14f4273335fb5ef02b7f636cd01800e1491a`: 18 changed files containing
only the initial integration, tests, and generated dependency/ownership/type
wiring. Docs adds one 96-line page on official next
`16ad324d9cbadf6d03b94f12ef278b00c7b9999f`. These are the new canonical refs;
old published history remains available without force pushes.

## Verified checks

- Python: [exact-head CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34168803786)
  passes all Python 3.12/3.13/3.14 jobs. There are 110 tests and 96.59% statement
  coverage, including 28 release-contract tests. Ruff, strict MyPy, builds,
  strict Twine checks, exact distribution contents, and isolated wheel/sdist
  imports pass.
- Initial Core: [exact-pair native run](https://github.com/jeffglousher/core/actions/runs/34169029198)
  passes 41 tests without failures, errors, or skips; 239/241 statements
  (99.1701%), with every module above 95%. Unchanged script/setup, the upstream
  full-tree general-hook subset, and standard contribution-file hooks pass,
  including native MyPy/Pylint, requirements, and typing generation. Tests
  keep the standard socket guard; no Windows compatibility shim is used.
- The same [exact initial native run](https://github.com/jeffglousher/core/actions/runs/34169029198)
  leaves tracked generated files unchanged. Initial Core has exactly the acknowledged
  `dependency-transparency: todo` blocker and no other errors/warnings.
  This is a staging-gate pass, not clean hassfest. Later speech naming remains
  a separate follow-on gate; it is not present in this initial layer.
- [Native docs and Brands validation](https://github.com/jeffglousher/core/actions/runs/34168495512)
  builds the exact new initial and final docs with the prescribed Jekyll command
  and passes prose checks. Brands at the exact SHA above passes the complete
  validator: 19,231 images, zero issues. All six docs layers also pass individual
  prose/whitespace checks. New render artifacts exist but have not been visually
  inspected; prior source-identical previews are not a new visual check.

OAuth device authorization remains the only login path and the approved provider
identity is unchanged. The unofficial package owns protocol handling, absolute
device-code expiry, polling backoff, and distinct permission/authentication
errors. This pass also rejects malformed response fields, unoffered function
calls, unsupported explicit token types, and invalid numeric token metadata.
Real SDK wire tests exercise these boundaries. Core remains the HA adapter:
its only changes in this pass are completed-retry, cancellation, shared-session,
and real Assist exposure tests. Docs clarifies subscription eligibility,
selected-by-default Assist access, and supported first-layer troubleshooting.

## Remaining first-wave gates

1. A human must review, understand, and be able to explain each contribution.
   The initial Core draft accurately links
   [previous Core #178765](https://github.com/home-assistant/core/pull/178765),
   which the author closed. No maintainer approval/rejection or discussion
   exemption is inferred. Personal template attestations remain unchecked.
2. Review and explicitly approve merging the package into main. Its prepared
   source is not merged. Configure the GitHub pypi environment with required
   human approval and verify PyPI account security and the exact pending
   Trusted Publisher. No publishing environment currently exists; private PyPI
   setup cannot be verified from public repository state.
3. Publish 0.1.0 only after those human/account gates. Release automation requires
   the exact current-main SHA, matching version tag, nonempty versioned
   changelog, full exact-SHA three-Python matrix, and exact artifact contract.
   It cannot prove human review. Verify actual PyPI metadata, provenance,
   distributions, and clean installation after publication.
4. Then mark dependency-transparency done in a follow-up Core commit,
   regenerate, and obtain genuinely clean native hassfest and tests with the
   released dependency. A development wheelhouse is not PyPI publication.
5. Verify a fresh initial-only Home Assistant installation and UI OAuth login on
   an isolated native host with an empty dedicated configuration and human
   provider authorization. The existing full-stack OAuth entry is not this
   proof. No suitable isolated native host is presently available here.
6. Visually review the newly generated docs preview and later the public logo
   after Brands merges. Recheck upstream freshness and replace staging links
   with actual PR/release links when human-reviewed submissions are made.

The [release checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/f12b460dffecff7ce4f2827fffa8351e06cadcb6/RELEASING.md)
contains the package publication sequence. Keep follow-ons staged until their
predecessors merge; do not open dependent upstream PRs.

## Follow-ons and runtime are separate gates

The [23-layer map](STACK.md) now separates four Core dependency bumps from their
features. All eleven Core layers pass native integration tests, but speech and
downstream remain quality-blocked by `has-entity-name: todo`. The written rule
has no exception for the current functional TTS naming behavior. The plan keeps
23 prepared contributions plus a conditional HA naming-fix slot beside speech,
if still needed then. It requires no additional Python package and does not
enlarge or block this first wave. No Bronze, Gold, or Platinum award is claimed.

The exact new full-stack dogfood is deployed and running; bounded conversation,
AI text, fresh TTS, audio decoding, and STT round-trip checks pass.
[Runtime evidence](RUNTIME_VERIFICATION.md) records the exact new source and
limits. Existing-account full-stack success does not prove a fresh initial-only login. [Current validation](STAGED_READINESS.md) records exact
source pairs and preserves prior evidence as historical.
