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

Prepared branch: `codex/spacexai/staged-docs-04-speech`, commit `7c1846b5924b4c5715c67c8ae3791821668150b9`. Review its [incremental diff](https://github.com/jeffglousher/home-assistant.io/compare/fc805f1dd2565f5d9fdecd3c08a6b8f806c5cc96...7c1846b5924b4c5715c67c8ae3791821668150b9) against `codex/spacexai/staged-docs-03-ai-task` at `fc805f1dd2565f5d9fdecd3c08a6b8f806c5cc96`. Submit against `next` only after prerequisite documentation and Core changes merge. This exact layer passes remark, textlint, and whitespace checks. Cumulative final docs at `69221dc8a853972e4b4fcbf78d4fbba8047b393d` passed native linters and the prescribed Jekyll build in [fork validation](https://github.com/jeffglousher/core/actions/runs/34168495512). This is cumulative build evidence, not a separate Jekyll run for this intermediate commit. No newly generated preview has been visually inspected. The current speech naming TODO remains unresolved; address it at the speech wave using existing accepted TTS precedent and, only if necessary, a separate minimal HA naming fix. It does not enlarge or block the initial conversation contribution. Neither this documentation build nor passing Core tests establishes compliance with the written naming rule.

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

- Link to parent pull request in the codebase: Not opened; [prepared Core layer 07](https://github.com/jeffglousher/core/compare/5e86d419c261bf98f92ed199b4f09e9ba7300c26...2c59f3dc5e7ad02e12eeea8072e25a804ce5c698).
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
