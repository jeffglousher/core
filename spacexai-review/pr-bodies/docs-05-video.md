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

Prepared branch: `codex/spacexai/staged-docs-05-video`, commit `f50938f93797f403cae294f7b790344885180dce`. Review its [incremental diff](https://github.com/jeffglousher/home-assistant.io/compare/7c1846b5924b4c5715c67c8ae3791821668150b9...f50938f93797f403cae294f7b790344885180dce) against `codex/spacexai/staged-docs-04-speech` at `7c1846b5924b4c5715c67c8ae3791821668150b9`. Submit against `next` only after prerequisite documentation and Core changes merge. This exact layer passes remark, textlint, and whitespace checks. Cumulative final docs at `69221dc8a853972e4b4fcbf78d4fbba8047b393d` passed native linters and the prescribed Jekyll build in [fork validation](https://github.com/jeffglousher/core/actions/runs/34168495512). This is cumulative build evidence, not a separate Jekyll run for this intermediate commit. This intermediate commit has not been visually inspected separately; the exact cumulative final integration page has been inspected at desktop width. [Blueprint validation](https://github.com/jeffglousher/core/actions/runs/34168495512) also passed using Core schema source `07c95d71202a7599cd4f91070df8a41a958a0524` and final docs `69221dc8a853972e4b4fcbf78d4fbba8047b393d`: two valid input cases, missing media rejected, and zero actions executed. This is not a blueprint rerun against the current Core09 head. The current speech naming TODO remains unresolved; address it at the speech wave using existing accepted TTS precedent and, only if necessary, a separate minimal HA naming fix. It does not enlarge or block the initial conversation contribution. Neither this documentation build nor passing Core tests establishes compliance with the written naming rule.

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

- Link to parent pull request in the codebase: Not opened; [prepared Core layer 09](https://github.com/jeffglousher/core/compare/a7a0e4b5f6fbad3cc36bec34d4199bb766614735...22180c78bea231061810d1427a4a3acd36014dde).
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
