# SpaceXAI first-wave readiness

Verified September 8, 2026. The four initial contributions are implemented
and prepared for human review. They are not upstream-ready: publication,
human review, and fresh initial-login proof remain. The exact initial docs
have now been visually inspected. No upstream PR or package release was
opened by this work.

## Exact first-wave source

- Python 0.1.0: `harden-initial-release`, `410730d2c9803d2a4c83cdeb6ebe7f1f2c0b9dd3`.
- Core: `codex/spacexai/staged-01-initial`, `cbe618c9800419de39601496779da68e5dd8ed23`.
- Brands: `spacexai-initial`, `e3ac8da8bf579ec54210cc211e1eaa0768052679`.
- Docs: `codex/spacexai/staged-docs-01-initial`, `0a5a5dfb0f779bf027b609781c5117cc78f9d3a7`.

All four are pushed to the corresponding jeffglousher forks. Core is based on
official dev `be2e14f4273335fb5ef02b7f636cd01800e1491a`: 18 changed files containing
only the initial integration, tests, and generated dependency/ownership/type
wiring. Docs adds one 96-line page on official next
`16ad324d9cbadf6d03b94f12ef278b00c7b9999f`. These are the new canonical refs;
old published history remains available without force pushes.

These recorded bases are not the current upstream tips. A fresh check found
Core dev `1f889c45a3952af07513e05c51043de86f02c499` 73 commits ahead and docs
next `5b1b0ec30067dcd4840a9446bd054e728612ece7` 12 commits ahead. The docs
changes do not alter the initial page; the shared configuration plugin only
adds an allowed type. Core's used OAuth, Conversation, Assist, and LLM APIs are
unchanged; only generated metadata and aggregate requirements overlap our diff.
No source migration was identified. This static inspection is not a current-tip build.
Refresh and retest before human-reviewed upstream submission.

## Verified checks

- Python: [exact-head CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34229759065)
  passes all Python 3.12/3.13/3.14 jobs. There are 120 tests and 96.62% statement
  coverage, including 36 release-contract tests. Ruff, strict MyPy, builds,
  strict Twine checks, exact wheel members/required source bytes, and isolated wheel/sdist
  imports pass.
- Initial Core with client `410730d2`: [exact-pair native run](https://github.com/jeffglousher/core/actions/runs/34229775265)
  passes 44 tests without failures, errors, or skips; 239/241 statements
  (99.1701%), with every module above 95%. Unchanged script/setup, the upstream
  full-tree general-hook subset, and standard contribution-file hooks pass,
  including native MyPy/Pylint, requirements, and typing generation. Tests
  keep the standard socket guard; no Windows compatibility shim is used.
- The same [exact initial native run](https://github.com/jeffglousher/core/actions/runs/34229775265)
  leaves tracked generated files unchanged. Initial Core has exactly the acknowledged
  `dependency-transparency: todo` blocker and no other errors/warnings.
  This is a staging-gate pass, not clean hassfest. Later speech naming remains
  a separate follow-on gate; it is not present in this initial layer.
- [Native docs and Brands validation](https://github.com/jeffglousher/core/actions/runs/34168495512)
  builds the exact new initial and final docs with the prescribed Jekyll command
  and passes prose checks. Brands at the exact SHA above passes the complete
  validator: 19,231 images, zero issues. All six docs layers also pass individual
  prose/whitespace checks. The exact initial docs `0a5a5dfb` from this run were
  visually inspected at desktop width 1280 and mobile width 390: readable,
  without overlapping content. The unpublished integration logo is expected
  to be unavailable from the public Brands CDN. A missing footer image belongs
  to the downloaded preview artifact, not the integration prose. The exact
  final docs `69221dc8` were also inspected at desktop width 1280: readable
  headings, tables, cards, privacy, and troubleshooting, without overlap.
  This checks those two rendered pages, not interactive controls or separate
  previews of all six docs layers.

OAuth device authorization remains the only login path and the approved provider
identity is unchanged. The unofficial package owns protocol handling, absolute
device-code expiry, polling backoff, and distinct permission/authentication
errors. This pass also rejects malformed response fields, unoffered function
calls, unsupported explicit token types, and invalid numeric token metadata.
Real SDK wire tests exercise these boundaries. The latest repair moves two
expiry timestamp computations into existing normalization and adds two named
public OAuth regressions for oversized JSON integers. This is a malformed-response
contract fix, not an observed provider outage; HA runtime code is unchanged.
Core remains the HA adapter:
this pass additionally maps OAuth refresh timeouts to normal retry/API errors.
Public endpoint regressions verify retained tokens, successful retry, and
cancellation. Existing shared-session and real Assist exposure tests still pass. Docs clarifies subscription eligibility,
selected-by-default Assist access, and supported first-layer troubleshooting.

## Original contribution provenance

The public author search found one `jeffglousher` Core submission:
[#178765, Add SpaceXAI Conversation integration.](https://github.com/home-assistant/core/pull/178765),
opened August 11, 2026. The author account closed it unmerged on August 18.
There is no written closure explanation and no human maintainer review to
attribute a rejection to. All 77 review records and 24 inline threads are
from bots; the [single-platform request](https://github.com/home-assistant/core/pull/178765#pullrequestreview-4908920675)
was Home Assistant automation. The author's [scope explanation](https://github.com/home-assistant/core/pull/178765#issuecomment-5259723684)
is not a closure explanation. Historical unresolved thread markers are not
proof that the rewritten initial code still has those defects.

One original [timeout finding](https://github.com/home-assistant/core/pull/178765#discussion_r3760223813)
was still valid. A [native pre-fix run](https://github.com/jeffglousher/core/actions/runs/34174576579)
reproduced setup entering SETUP_ERROR and conversation leaking TimeoutError.
The corrected initial [run](https://github.com/jeffglousher/core/actions/runs/34175174869)
passes both recoveries and cancellation. An intermediate recovery test used the
wrong HA lifecycle method; that test was corrected to public async_reload before
claiming success. This is a verified bot finding, not a maintainer rejection.

## Verified publication controls and limits

Read-only GitHub verification confirms the `pypi` environment requires
`jeffglousher` approval, allows that sole maintainer to approve their own run,
disallows administrator bypass, and accepts only `v*` tags. Protected `main`
requires a PR, resolved conversations, and strict `Python 3.12`, `Python 3.13`,
and `Python 3.14` checks from GitHub Actions app 15368. Those exact checks were
observed passing. Administrators are covered; force pushes and deletion are
forbidden. Required external approvals are zero, so this is not independent
human review. The [version-tag ruleset](https://github.com/jeffglousher/spacexai-subscription-client/rules/22495983)
forbids updates/deletion without bypass; it does not make release assets immutable.

The owner approval is an account permission, not proof that a human rather
than an agent is using that identity. An agent must not approve publication
on the owner's behalf. PyPI account security and the pending publisher remain
unverified: the browser reached sign-in, and no login was attempted.

## Remaining first-wave gates

1. A human must review, understand, and be able to explain each contribution.
   Personal template attestations remain unchecked; green checks do not make
   those attestations.
2. Review and explicitly approve merging the prepared package into main, and
   verify PyPI account security and the exact pending Trusted Publisher,
   including its `pypi` environment binding. The prepared source is not merged.
3. Publish 0.1.0 only after those human/account gates. Current main still has the
   legacy release workflow: it uses the protected `pypi` environment, but lacks
   the prepared exact-main preflight, release-test matrix, and artifact contract.
   Merge the reviewed prepared workflow before releasing. That workflow requires
   the exact current-main SHA, matching version tag, nonempty versioned changelog,
   full exact-SHA three-Python matrix, and artifact checks before owner approval.
   Verify actual PyPI metadata, provenance, distributions, and clean installation
   after publication.
4. Then mark dependency-transparency done in a follow-up Core commit,
   regenerate, and obtain genuinely clean native hassfest and tests with the
   released dependency. A development wheelhouse is not PyPI publication.
5. Verify a fresh initial-only Home Assistant installation and UI OAuth login on
   an isolated native host with an empty dedicated configuration and human
   provider authorization. The existing full-stack OAuth entry is not this
   proof. No suitable isolated native host is presently available here.
6. Recheck the public integration logo after Brands merges. The initial docs
   visual check is complete; final-stack visual review is not initial-login
   proof. Recheck upstream freshness and replace staging links with actual
   PR/release links when human-reviewed submissions are made.

The [release checklist](https://github.com/jeffglousher/spacexai-subscription-client/blob/410730d2c9803d2a4c83cdeb6ebe7f1f2c0b9dd3/RELEASING.md)
contains the package publication sequence. Keep follow-ons staged until their
predecessors merge; do not open dependent upstream PRs.

## Follow-ons and runtime are separate gates

The [23-layer map](STACK.md) now separates four Core dependency bumps from their
features. All eleven Core layers passed native tests with the explicitly recorded
previous package pairs; the initial pair is now retested with the expiry fix.
The remaining ten pairs have not been rerun with the new package heads. Speech and
downstream remain quality-blocked by `has-entity-name: todo`. The written rule
has no exception for the current functional TTS naming behavior. The plan keeps
23 prepared contributions plus a conditional HA naming-fix slot beside speech,
if still needed then. It requires no additional Python package and does not
enlarge or block this first wave. No Bronze, Gold, or Platinum award is claimed.

The existing full-stack dogfood remains on client `f58ec77a`, not the new
`376fe0c9` expiry-fix head. Its bounded conversation,
AI text, fresh TTS, audio decoding, and STT round-trip checks pass.
[Runtime evidence](RUNTIME_VERIFICATION.md) records that deployed source and
limits. Existing-account full-stack success does not prove a fresh initial-only login. [Current validation](STAGED_READINESS.md) records exact
source pairs and preserves prior evidence as historical.
