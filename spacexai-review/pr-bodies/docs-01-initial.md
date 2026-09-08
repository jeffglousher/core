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

Document the new SpaceXAI integration so people with an eligible xAI subscription can add Grok as a conversation agent in Home Assistant. The page covers browser sign-in, model and instruction settings, Assist access, troubleshooting, and removal.

I'm keeping this first contribution focused on conversation. The page explains that Assist is selected by default, how to disable it, and which messages and entity data are sent to xAI. It also makes clear that this is a community-maintained integration and links to the provider's privacy information and terms.

This is one new integration page, based on `next`. The documentation checks and prescribed Jekyll build pass. The [review record](https://github.com/jeffglousher/core/blob/codex/spacexai-validation/spacexai-review/FIRST_WAVE_READINESS.md#documentation-and-brands) contains the exact-source results and remaining preview checks.

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

- Link to parent pull request in the codebase: Not opened yet; [prepared Core changes](https://github.com/jeffglousher/core/compare/38aacedef39eb3f077ce4a112a58bf7286af5e2c...cd495263eed9794a02a19efb797206e4ff67ef8f) on `codex/spacexai/initial-release-0-1`.
- Link to parent pull request in the Brands repository: Not opened yet; [prepared Brands changes](https://github.com/jeffglousher/brands/compare/codex/spacexai/review-base...spacexai-initial).
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
