> Historical evidence for the superseded pre-September-7 branch chain.
> Do not attribute these old source pairs, counts, or successful runs to the
> rebuilt 23-contribution stack. Use [current validation](STAGED_READINESS.md)
> and the [canonical map](STACK.md). Current final Core still fails the two
> acknowledged quality rules; no clean final hassfest or tier award is claimed.

# Native generated wiring validation — 2026-09-07 UTC

[Fork-only validation run 34081231119](https://github.com/jeffglousher/core/actions/runs/34081231119) completed successfully for the exact current canonical initial and final Core/client pairs on Ubuntu 24.04 with Python 3.14.5. The workflow success means generated wiring matches and the only scoped hassfest finding is the explicitly recorded unpublished dependency; it is not a clean hassfest or merge-readiness claim.

## Exact sources

- Initial Core: `c9e6db462a36cd5a70e12672d09579bd757f0e1b`; initial client: `c4fd662c281b5700a5c5d547b4afe097c8e5be22`.
- Final Core: `2315fa45b978aa1ebf637c111d0c1410d68d12ea`; final client: `b2d823452e5054ece8b7a90fb7b172f5ac1d1a7c`.
- Validation harness: `be03b46b6701e86b5149c5b36d8f8eb5d4d41f27`, isolated on `codex/spacexai-validation`.

This rerun supersedes run 34079419226 for current-head evidence. It includes the
follow-on coverage regressions and the client TTS complete-stream repair; no
initial source changes were required.

## Confirmed results

- Native `script.gen_requirements_all` regeneration and its validation mode both pass.
- Native hassfest generation for translations, codeowners, config flows/integration metadata, and strict typing/MyPy runs across all 1,515 integrations with zero invalid integrations.
- Tracked Git diff is empty before regeneration, after regeneration, and after final validation for both tested Core commits. All six saved diff files are zero bytes.
- Full default integration-scoped hassfest validation reports exactly one error and zero warnings for both commits: `Quality scale tier bronze requires quality scale rules to be met: dependency-transparency: todo`.
- There are no general errors. Structured capture includes fixable findings normally hidden in CLI reporting; no additional findings were ignored.

The helper leaves the source quality-scale declaration intact. It permits only that exact single dependency-publication error or a genuinely clean hassfest result. Any other finding or generated-file difference fails the job.

## Initial wiring audit

The initial canonical commit adds 18 changed files and is directly based on upstream `dev` at `d8840c58794`. Six existing wiring files receive only the expected SpaceXAI entries: `.strict-typing`, `CODEOWNERS`, generated config flows, generated integration metadata, `mypy.ini`, and `requirements_all.txt`. Other changes are the integration and its tests. The rebuilt chain initially contained one focused commit per layer. Later-layer authentication regression tests and their verified coverage status were subsequently added with follow-up commits and parent merges, preserving the published history. The initial commit and all generated wiring remain unchanged.

All six Core follow-on draft comparison links now use the canonical ready branch chain and include their exact commit links. The first Core draft and shared readiness documents remain owned by the parent task.

## Evidence files

Downloaded artifacts are in `.tmp-spacexai-stack/native-generated-34081231119/`, under `spacexai-generated-initial-34081231119/` and `spacexai-generated-final-34081231119/`. Each includes source identities, complete generator logs, all tracked diff checks, and structured hassfest findings. Both structured results explicitly report `blocked_only_on_dependency_publication` with hassfest exit code 1; the narrowly scoped staging workflow allows only that exact known blocker.

PyPI publication and verification are still required before changing dependency-transparency to done and obtaining a clean final hassfest result.
