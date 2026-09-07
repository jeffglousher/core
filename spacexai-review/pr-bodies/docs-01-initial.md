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

Document the new SpaceXAI conversation integration: browser sign-in, account prerequisites, optional Assist access, configuration, troubleshooting, and removal. Explain which conversation and entity data is sent to xAI, link to provider privacy information and terms, and identify the integration as community-maintained.

Prepared from `next` on branch `codex/spacexai/docs-01-initial-next`. The diff contains only the new integration page. The release is quoted as `'2026.10'` so YAML preserves October. Native remark/textlint and the prescribed Jekyll build passed for commit `fcc39e84baa705e1c7cdc0eb4102e937dccfe487` in [fork validation](https://github.com/jeffglousher/core/actions/runs/34078694067); the rendered initial page was also inspected in a browser. The public brand logo remains pending the separate Brands merge.

## Type of change
<!--
    What types of changes does your PR introduce to our documentation/website?
    Put an `x` in the boxes that apply. You can also fill these out after
    creating the PR.
-->

- [ ] Spelling, grammar or other readability improvements (`current` branch).
- [ ] Adjusted missing or incorrect information in the current documentation (`current` branch).
- [x] Added documentation for a new integration I'm adding to Home Assistant (`next` branch).
  - [ ] I've opened up a PR to add logos and icons in [Brands repository](https://github.com/home-assistant/brands).
- [ ] Added documentation for a new feature I'm adding to Home Assistant (`next` branch).
- [ ] Removed stale or deprecated documentation.

## Additional information
<!--
    Details are important, and help maintainers processing your PR.
    Please be sure to fill out additional details, if applicable.
-->

- Link to parent pull request in the codebase: https://github.com/home-assistant/core/compare/dev...jeffglousher:core:codex/spacexai/core-01-ready
- Link to parent pull request in the Brands repository: https://github.com/home-assistant/brands/compare/master...jeffglousher:brands:spacexai-initial
- This PR fixes or closes issue: Not applicable; this documents a new integration.

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
