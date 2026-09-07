> Historical evidence for the superseded pre-September-7 branch chain.
> Do not attribute these old source pairs, counts, or successful runs to the
> rebuilt 23-contribution stack. Use [current validation](STAGED_READINESS.md)
> and the [canonical map](STACK.md). Current final Core still fails the two
> acknowledged quality rules; no clean final hassfest or tier award is claimed.

# Documentation quality repair evidence

Verified 2026-09-07 UTC (2026-09-06 America/Chicago). These are prepared documentation changes on the user's fork, not submitted upstream PRs or a quality-tier award.

## Scope and exact revisions

The initial documentation remains unchanged at `fcc39e84baa705e1c7cdc0eb4102e937dccfe487`. Follow-up commits and parent merges preserve published history.

- `codex/spacexai/docs-02-conversation-next`: `a8cfef8b0c9abd7aeaa4addb67e5be837d85d257`. Explain the conversation Name field and suggested Grok name.
- `codex/spacexai/docs-03-ai-task-next`: `8eef1e07bf77fe355a8fd1e76782c50c98dbca4c`. Extend the explanation to AI tasks and Grok AI Task.
- `codex/spacexai/docs-04-speech-next`: `80c17f28c6744574b9aca12934eb5d4941ccf108`. Explain speech Name fields and match the actual Grok TTS label. Independent review found the former label mismatch; it was corrected in this owning layer.
- `codex/spacexai/docs-05-video-next`: `c24a9d5cc4be4797fd43e5c3ca495afc81ec4a47`. Document video status polling's immediate first check, five-second wait after each pending response, and ten-minute deadline. Add one reusable scheduled local-media notification blueprint and its import badge.
- `codex/spacexai/docs-06-account-next`: `babe0b6292d05002457184872f47e8f8c2e02e0d`. Merge the repaired parent while preserving account-recovery documentation.

All six remote refs were read back and match. The documentation worktree is clean. The cumulative repair changes only the integration page and a new 36-line blueprint: 48 insertions and 2 deletions. It does not add a PR layer.

## Validation

[Native run 34080892563](https://github.com/jeffglousher/core/actions/runs/34080892563) succeeded for initial docs, final docs, the blueprint, and unchanged Brands. The fork-only helper/workflow commit is `3c2dc9355679933eee5bc8af88002f08494986d4` on `codex/spacexai-docs-validation`.

- Local remark, textlint, and whitespace checks pass at each changed layer. The blueprint also passes YAML linting.
- Native remark/textlint and the prescribed `bundle exec rake generate` pass on the exact initial and final revisions. Final build uses Ruby 3.4.8 and Jekyll 4.4.1 and completes in 85.126 seconds.
- The built blueprint is byte-identical to its source. Rendered HTML contains the new Name explanations, corrected Grok TTS label, functional blueprint-import URL, and precise polling guidance.
- Native Home Assistant blueprint metadata/schema and input substitution pass on Python 3.14.5, exact Core Wave 5 `b64085011ba8309005ec645d9500d76c45ba8c64`. Checks cover a PNG with the default 18:00 time, an MP4 with a custom 06:30 time, required-media rejection, selector values, expanded automation/time/action schemas, and response-template rendering. No actions were executed or registered.
- Independent re-review of the final cumulative diff found no remaining material issues. This is source and native-build evidence; final human review remains necessary.

Artifacts are downloaded under `.tmp-spacexai-stack/native-docs-repair-34080892563/`: `blueprint/` records the exact Core/docs/Python versions and zero executed actions; `final/` contains build evidence and rendered files. This records cumulative final rendering, not separate Jekyll runs for every intermediate layer.

## Rule-specific disposition

The three concrete documentation gaps from the read-only audit are now addressed:

- [docs-installation-parameters](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/docs-installation-parameters/): the Name fields introduced by later subentry flows are explained alongside each feature, with defaults checked against the corresponding Core layer.
- [docs-data-update](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/docs-data-update/): video polling timing is explicit and checked against the client implementation. The page retains the correct no-idle-polling explanation.
- [docs-examples](https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/docs-examples/): the page links one actual blueprint under `source/blueprints/integrations/`, as the current rule requests. It only publishes a selected existing local file and creates a Home Assistant notification. No provider requests or content-generation charges occur. The administrator requirement and one-hour bearer-link risk are documented.

The audit also found concrete existing coverage for configuration options, known limitations, supported functionality, troubleshooting, and use cases. No quality-scale source statuses or broad Gold/Platinum claim were changed here. PyPI publication and human submission remain separate gates.
