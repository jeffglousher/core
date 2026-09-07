# SpaceXAI first-wave readiness

Verified September 6, 2026. This supersedes the September 2 readiness report.
The first four contributions are implemented, validated, and staged for human
review. Publication and human submission gates remain. No upstream PR or
PyPI release was opened by this work.

## Canonical first-wave heads

- Python: `harden-initial-release`, `c4fd662c281b5700a5c5d547b4afe097c8e5be22`, version 0.1.0.
- Core: `codex/spacexai/core-01-ready`, `c9e6db462a36cd5a70e12672d09579bd757f0e1b`.
- Brands: `spacexai-initial`, `e3ac8da8bf579ec54210cc211e1eaa0768052679`.
- Docs: `codex/spacexai/docs-01-initial-next`, `fcc39e84baa705e1c7cdc0eb4102e937dccfe487`.

All four heads are pushed to the corresponding jeffglousher forks.
Core is one focused commit directly on official dev at
`d8840c5879458bd2dd504587f4d57cb6b1dfe4f9`. Its 18-file diff contains only the
integration, tests, and generated ownership/dependency/typing wiring.
Docs is one new 96-line page on official next at
`2e9d474293b521eba15699e397b4ee7881074cc0`.

Old published Core and docs refs are preserved historical copies, not a second
active submission chain. Published history was not rewritten or deleted.

## Verified evidence

- Python: 59 tests, 96.51% local coverage; strict types, lint, formatting, wheel
  and source builds, strict Twine checks, and isolated installs pass.
  [Public CI](https://github.com/jeffglousher/spacexai-subscription-client/actions/runs/34078265048)
  passes at the exact head on Python 3.12, 3.13, and 3.14. Unofficial identity,
  SPDX licensing, source/issues links, and PEP 561 typing marker are verified.
- Initial Core:
  [native Linux validation](https://github.com/jeffglousher/core/actions/runs/34078831785)
  passes at the exact pair above: 39 tests, no failures/errors/skips. Setup,
  config flow, and constants have 100% coverage; conversation 97.70%; overall
  99.17%. Native Ruff 0.16.5, formatting, MyPy, and Pylint pass.
- All seven Core layers pass native Linux tests: 39, 53, 85, 101, 123, 134,
  and 137 tests respectively, with no failures/errors/skips. The final layer
  also verifies three snapshots. Every integration module exceeds 95%; final
  aggregate coverage is 99.28%. Native Ruff, formatting, MyPy, and Pylint pass
  at every layer. CORE_LINUX_EVIDENCE.md records exact source pairs and runs.
- Docs and Brands:
  [native validation](https://github.com/jeffglousher/core/actions/runs/34080892563)
  passes full initial/final Jekyll builds, prose linters, and the complete
  Bash/ImageMagick validator (19,231 images, zero issues). All six docs heads
  also pass individual prose checks. The final blueprint passes native HA
  schema/input/template validation without executing actions. Eight assets have verified retained
  official-source provenance and were not changed.
- The initial rendered page was opened in a browser: layout and October release
  metadata render correctly. The public brand CDN displays its expected
  placeholder until the separate Brands contribution merges.

OAuth device authorization remains the only login path. Provider identity approval
is unchanged. Absolute device-code expiry and backoff survive retries; permission
denial is distinct from invalid credentials. Core remains a thin HA adapter.

## Remaining gates

1. Publish Python 0.1.0 after personal review/merge and setup of the exact
   approval-gated GitHub pypi environment and pending publisher. Verify both
   distributions, provenance, immutable tag, metadata, and clean PyPI install.
   The checked-in RELEASING.md contains the full checklist.
2. Only then mark dependency-transparency done. It intentionally remains todo
   and blocks Bronze hassfest. [Native generated validation](https://github.com/jeffglousher/core/actions/runs/34081231119)
   passes for initial and final: regeneration leaves tracked files unchanged,
   and scoped hassfest reports exactly this one error with no other findings.
3. Complete human review under HA's AI policy, confirm relevant prior discussion,
   replace staging comparisons with actual PR/release links, and personally
   complete template attestations.
4. Recheck upstream freshness immediately before submitting. Keep follow-ons
   staged until their predecessors merge; do not open dependent upstream PRs.

## Refreshed test system

Dogfood commit `ae2897793bc9498a0d5714286d57dc21afdc912a` includes final Core
`2315fa45b978aa1ebf637c111d0c1410d68d12ea` and fixed package
`b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`. It is pushed and deployed. Source
hashes, generated translations, configuration check, restart, loaded OAuth
entry, and the single-overlay condition were verified.

Live conversation, AI text, image generation and signed retrieval, independent
STT, and video passed. TTS initially exposed a first-chunk truncation bug. The
repair landed in package 0.4.0 and propagated to 0.5.0, with real stream regression
tests and updated public CI. After redeployment, an uncached speech request
returned 31,488 bytes of valid MP3, about 1.97 seconds; STT of that exact audio
returned the expected sentence. Conversation and AI text also passed again.
RUNTIME_VERIFICATION.md gives a sanitized account of the exact checks and limits.

## Validation limits corrected

Earlier Windows HA test counts used compatibility shims including a disabled
pytest socket guard. They are retired as native HA evidence. All Linux runs
above use the original safeguards and exact installed package versions. The
old shim directory was moved to retired-win-test-shims in this local staging
directory, outside the test launch path, and remains recoverable.

script/setup was attempted in the new Windows worktree: it fails because it
expects .venv/bin/activate while Windows creates .venv/Scripts/activate.
Linux CI uses a scoped native environment with the exact unpublished client;
full bootstrap cannot install the PyPI pin until publication.

The required local uv run --no-sync prek run --all-files was attempted.
Ruff, formatting, codespell, zizmor, JSON, branch, YAML, and prettier checks pass;
the MyPy hook launcher stops with program not found. This is not a full prek
pass. Integration-specific native Linux lint and type checks do pass.

## Publication sequence

1. Human-review and publish Python 0.1.0; verify the actual PyPI artifacts.
2. Satisfy dependency-transparency in a follow-up Core commit; regenerate and
   rerun hassfest and native checks.
3. Human-review and submit the initial Core, Brands, and Docs, cross-link their
   actual PRs, and verify the rendered page after Brands lands.
4. Keep the other layers on the fork, submitting only after prerequisites merge.

STACK.md maps all layers. PACKAGE_REPAIR_EVIDENCE.md and
DOCS_BRANDS_REPAIR_EVIDENCE.md contain detailed checks and exact sources.
DOCS_QUALITY_REPAIR_EVIDENCE.md records the final follow-on documentation repairs.
DOGFOOD_DEPLOYMENT.md remains explicitly historical. The September 6 deployment
and live checks are recorded separately in DOGFOOD_DEPLOYMENT_20260906.md.
