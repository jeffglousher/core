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

Document the new SpaceXAI conversation integration: browser sign-in, eligible subscription prerequisites, the default Assist selection and how to disable it, configuration, troubleshooting, and removal. Explain which conversation and entity data is sent to xAI, link to provider privacy information and terms, and identify the integration as community-maintained.

This fork draft accompanies only the initial conversation platform. Attachments, provider-hosted tools, AI Task, image/video generation, speech, and later account features are not documented here. The parent Core and Brands changes remain separate prepared contributions, not open upstream PRs.

Prepared from official `next` at `1b359d16aca5ba2c6b7983fa36c8c5f2334c5c5a` on branch `codex/spacexai/docs-initial-release-0-1`, commit `44526b046fa26d4ddf0ab037850a54e30ecbf1d0`. The diff contains only the new 96-line integration page, byte-identical to the previously reviewed initial page. The release is quoted as '2026.10' so YAML preserves October; confirm the target release when preparing upstream submission.

Local and native remark/textlint checks pass for the new candidate. Its exact-source [native Jekyll validation](https://github.com/jeffglousher/core/actions/runs/34245078515) passed with Ruby 3.4.8, Jekyll 4.4.1, and Node.js 20.20.2; the prescribed site build completed in 110.475 seconds and produced the integration page.

The earlier `0a5a5dfb` render from [historical validation](https://github.com/jeffglousher/core/actions/runs/34168495512) was visually inspected at desktop and mobile widths: content and configuration cards were readable without overlap. That is not a visual inspection of the refreshed candidate, even though the page source is unchanged. Interactive controls were not exercised. Public logo delivery remains pending the separate Brands merge. Recheck upstream freshness and replace staging comparisons with actual companion PR links before upstream submission.

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

- Link to parent pull request in the codebase: Not opened; [prepared current-tip initial Core](https://github.com/jeffglousher/core/compare/38aacedef39eb3f077ce4a112a58bf7286af5e2c...7a41a0358c01a58700bde227fa0a951d28f5e638) on `codex/spacexai/initial-release-0-1`.
- Link to parent pull request in the Brands repository: Not opened; [prepared Brands comparison](https://github.com/jeffglousher/brands/compare/codex/spacexai/review-base...spacexai-initial).
- This PR fixes or closes issue: Not applicable; this documents a new integration.

## Checklist
<!--
    Put an `x` in the boxes that apply. You can also fill these out after
    creating the PR. If you're unsure about any of them, don't hesitate to ask.
    We're here to help! This is simply a reminder of what we are going to look
    for before merging your code.
-->

- [ ] This PR uses the correct branch, based on one of the following:
  - I made a change to the existing documentation and used the `current` branch.
  - I made a change that is related to an upcoming version of Home Assistant and used the `next` branch.
- [x] The documentation follows the Home Assistant documentation [standards].

[standards]: https://developers.home-assistant.io/docs/documenting/standards
