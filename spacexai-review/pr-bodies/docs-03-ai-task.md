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

Document text and structured data tasks and image generation through the standard AI Task actions. Explain the Name field when adding an AI task. Image editing accepts one to five JPEG or PNG images. Explain that task instructions and source files are sent to xAI.

Prepared branch: `codex/spacexai/staged-docs-03-ai-task`, commit `fc805f1dd2565f5d9fdecd3c08a6b8f806c5cc96`. Review its [incremental diff](https://github.com/jeffglousher/home-assistant.io/compare/ce493b6c2d545d3f0b0b8f887a01c140b4e35347...fc805f1dd2565f5d9fdecd3c08a6b8f806c5cc96) against `codex/spacexai/staged-docs-02-conversation` at `ce493b6c2d545d3f0b0b8f887a01c140b4e35347`. Submit against `next` only after prerequisite documentation and Core changes merge. This exact layer passes remark, textlint, and whitespace checks. Cumulative final docs at `69221dc8a853972e4b4fcbf78d4fbba8047b393d` passed native linters and the prescribed Jekyll build in [fork validation](https://github.com/jeffglousher/core/actions/runs/34168495512). This is cumulative build evidence, not a separate Jekyll run for this intermediate commit. No newly generated preview has been visually inspected.

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

- Link to parent pull request in the codebase: Not opened; [prepared Core layer 05](https://github.com/jeffglousher/core/compare/33d48cf808320e6123cc6141fd759c75cb49afea...4046b353e5b74553bfea2eaa30e4884e0e41ebc9).
- Link to parent pull request in the Brands repository: Not applicable; the initial integration supplies the existing assets.
- This PR fixes or closes issue: Not applicable; this documents AI tasks.

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
