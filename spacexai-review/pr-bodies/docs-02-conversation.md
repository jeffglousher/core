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

Explain multiple conversation agents, the Name field and its suggested value, reconfiguration, JPEG/PNG/PDF attachments, and optional provider tools. Document which attachment content and tool queries leave Home Assistant.

Prepared branch: `codex/spacexai/staged-docs-02-conversation`, commit `ce493b6c2d545d3f0b0b8f887a01c140b4e35347`. Review its [incremental diff](https://github.com/jeffglousher/home-assistant.io/compare/0a5a5dfb0f779bf027b609781c5117cc78f9d3a7...ce493b6c2d545d3f0b0b8f887a01c140b4e35347) against `codex/spacexai/staged-docs-01-initial` at `0a5a5dfb0f779bf027b609781c5117cc78f9d3a7`. Submit against `next` only after prerequisite documentation and Core changes merge. This exact layer passes remark, textlint, and whitespace checks. Cumulative final docs at `69221dc8a853972e4b4fcbf78d4fbba8047b393d` passed native linters and the prescribed Jekyll build in [fork validation](https://github.com/jeffglousher/core/actions/runs/34168495512). This is cumulative build evidence, not a separate Jekyll run for this intermediate commit. This intermediate commit has not been visually inspected separately; the exact cumulative final integration page has been inspected at desktop width.

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

- Link to parent pull request in the codebase: Not opened; [prepared Core layer 03](https://github.com/jeffglousher/core/compare/bfb6bf9ccb55d1e42267175201affdd9d642c052...a3adf7f56bb35d70b8b4db5acb1a59709574245e).
- Link to parent pull request in the Brands repository: Not applicable; the initial integration supplies the existing assets.
- This PR fixes or closes issue: Not applicable; this documents conversation attachments and tools.

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
