<!--
  You are amazing! Thanks for contributing to our project!
  Please, DO NOT DELETE ANY TEXT from this template! (unless instructed).

  Before submitting your pull request, please verify that you have chosen the correct target branch,
  and that the PR preview looks fine and does not include unrelated changes.
-->
## Proposed change
<!-- 
    Describe the big picture of your changes here to communicate to the
    maintainers why we should accept this pull request. If it fixes a bug
    or resolves a feature request, be sure to link to that issue in the 
    additional information section.
-->

Document the administrator-only Generate video and Publish media actions in separate action pages, with UI instructions and existing automation examples. Include one reusable blueprint for a scheduled local-media notification without provider requests or generation charges. Explain billable generation, local source uploads, video polling timing, size limits, and temporary links that grant access to recipients.

Prepared branch: `codex/spacexai/staged-docs-05-video`, commit `f10ee3fb40ccb707cc7e5d66c5a6146fa1bb12b6`. Review its [incremental diff](https://github.com/jeffglousher/home-assistant.io/compare/codex/spacexai/staged-docs-04-speech...codex/spacexai/staged-docs-05-video) against `codex/spacexai/staged-docs-04-speech`. Submit against `next` only after prerequisite documentation and Core changes merge. This exact layer passes remark, textlint, and whitespace checks. Cumulative final docs at `30997c988948e3a3e9f138ed350960cd28ce81b3` passed native linters and the prescribed Jekyll build in [fork validation](https://github.com/jeffglousher/core/actions/runs/34124125762). This is cumulative build evidence, not a separate Jekyll run for this intermediate commit. No newly generated preview has been visually inspected. [Blueprint validation](https://github.com/jeffglousher/core/actions/runs/34124125762) also passed using rebuilt Core09 `07c95d71202a7599cd4f91070df8a41a958a0524` and final docs `30997c988948e3a3e9f138ed350960cd28ce81b3`: two valid input cases, missing media rejected, and zero actions executed. The companion speech and downstream Core layers remain quality-blocked by has-entity-name: todo; this documentation build does not resolve that gate.

## Type of change
<!--
    What types of changes does your PR introduce to our documentation/website?
    Put an `x` in the boxes that apply. You can also fill these out after
    creating the PR.
-->

- [ ] Spelling, grammar or other readability improvements (`current` branch).
- [ ] Adjusted missing or incorrect information in the current documentation (`current` branch).
- [ ] Added documentation for a new integration I'm adding to Home Assistant (`next` branch).
  - [ ] I've opened up a PR to add logos and icons in [Brands repository](https://github.com/home-assistant/brands).
- [x] Added documentation for a new feature I'm adding to Home Assistant (`next` branch).
- [ ] Removed stale or deprecated documentation.

## Additional information
<!--
    Details are important, and help maintainers processing your PR.
    Please be sure to fill out additional details, if applicable.
-->

- Link to parent pull request in the codebase: Not opened; [prepared Core layer 09](https://github.com/jeffglousher/core/compare/codex/spacexai/staged-08-client-0-5...codex/spacexai/staged-09-video).
- Link to parent pull request in the Brands repository: Not applicable; the initial integration supplies the existing assets.
- This PR fixes or closes issue: Not applicable; this documents video generation and media sharing.

## Checklist
<!--
    Put an `x` in the boxes that apply. You can also fill these out after
    creating the PR. If you're unsure about any of them, don't hesitate to ask.
    We're here to help! This is simply a reminder of what we are going to look
    for before merging your code.
-->

- [x] This PR uses the correct branch, based on one of the following:
  - I made a change to the existing documentation and used the `current` branch.
  - I made a change that is related to an upcoming version of Home Assistant and used the `next` branch.
- [x] The documentation follows the Home Assistant documentation [standards].

[standards]: https://developers.home-assistant.io/docs/documenting/standards
