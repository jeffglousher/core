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

Document same-account browser reauthentication while preserving entity settings. Explain automatic token refresh, authorization storage, and why a different account cannot replace an existing account during reauthentication.

Prepared branch: `codex/spacexai/docs-06-account-next`. Review its incremental diff against `codex/spacexai/docs-05-video-next`. Submit against `next` after the prerequisite documentation and Core changes merge. Native remark/textlint and the prescribed Jekyll build passed for commit `babe0b6292d05002457184872f47e8f8c2e02e0d` in [fork validation](https://github.com/jeffglousher/core/actions/runs/34080892563). The native Home Assistant blueprint schema, input substitution, and response-template checks also passed, with no actions executed. The rendered page contains the repaired names, import badge, and polling guidance; final human review remains required.

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

- Link to parent pull request in the codebase: https://github.com/jeffglousher/core/compare/codex/spacexai/core-05-video-ready...codex/spacexai/core-06-account-ready
- Link to parent pull request in the Brands repository: Not applicable; the initial integration supplies the existing assets.
- This PR fixes or closes issue: Not applicable; this documents account recovery.

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
