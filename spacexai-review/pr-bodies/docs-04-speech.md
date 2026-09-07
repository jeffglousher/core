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

Document adding and naming the Grok speech entities, selecting them for Assist, supported recording formats, voices, and speed. Match the suggested Grok TTS name shown in Home Assistant. Explain that speech recognition sends recordings and speech synthesis sends text to xAI.

Prepared branch: `codex/spacexai/docs-04-speech-next`, commit `80c17f28c6744574b9aca12934eb5d4941ccf108`. Review its incremental diff against `codex/spacexai/docs-03-ai-task-next`. Submit against `next` after the prerequisite documentation and Core changes merge. Local remark, textlint, and whitespace checks pass. This layer is included in final docs commit `babe0b6292d05002457184872f47e8f8c2e02e0d`, whose native linters and prescribed Jekyll build passed in [fork validation](https://github.com/jeffglousher/core/actions/runs/34080892563). This is cumulative render evidence, not a separate Jekyll run for this intermediate commit.

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

- Link to parent pull request in the codebase: https://github.com/jeffglousher/core/compare/codex/spacexai/core-03-ai-task-ready...codex/spacexai/core-04-speech-ready
- Link to parent pull request in the Brands repository: Not applicable; the initial integration supplies the existing assets.
- This PR fixes or closes issue: Not applicable; this documents speech support.

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
