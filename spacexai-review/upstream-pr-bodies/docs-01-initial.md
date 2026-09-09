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

I'm documenting the SpaceXAI conversation integration for people with an eligible xAI subscription. The page covers browser sign-in, model and instruction settings, Assist access, troubleshooting, and removal.

The page explains that Assist is enabled by default, how to disable it, and which messages and entity data are sent to xAI. It identifies the integration as community-maintained and links to the provider's privacy information and terms.

This adds one integration page for an upcoming Home Assistant release. The prose checks and prescribed [Jekyll build](https://github.com/jeffglousher/core/actions/runs/34347046875) pass.

## Type of change

<!--
    What types of changes does your PR introduce to our documentation/website?
    Put an `x` in the boxes that apply. You can also fill these out after
    creating the PR.
-->

- [ ] Spelling, grammar or other readability improvements (`current` branch).
- [ ] Adjusted missing or incorrect information in the current documentation (`current` branch).
- [x] Added documentation for a new integration I'm adding to Home Assistant (`next` branch).
  - [x] I've opened up a PR to add logos and icons in [Brands repository](https://github.com/home-assistant/brands).
- [ ] Added documentation for a new feature I'm adding to Home Assistant (`next` branch).
- [ ] Removed stale or deprecated documentation.

## Additional information

<!--
    Details are important, and help maintainers processing your PR.
    Please be sure to fill out additional details, if applicable.
-->

- Link to parent pull request in the codebase: [home-assistant/core#181709](https://github.com/home-assistant/core/pull/181709).
- Link to parent pull request in the Brands repository: [home-assistant/brands#11129](https://github.com/home-assistant/brands/pull/11129).
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
