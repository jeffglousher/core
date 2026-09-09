<!--
  You are amazing! Thanks for contributing to our project!
  Please, DO NOT DELETE ANY TEXT from this template! (unless instructed).

  Pull requests for adding new custom components will no longer be accepted. Please refer to the Brands Proxy API announcement for more details:
  https://developers.home-assistant.io/blog/2026/02/24/brands-proxy-api
-->

## Proposed change

<!-- 
  Describe the big picture of your changes here to communicate to the
  maintainers why we should accept this pull request.
-->

I'm adding icons and logos for the SpaceXAI conversation integration. The eight PNG assets under `core_integrations/spacexai` include light and dark variants at standard and high-density resolutions.

The artwork uses the [official SpaceXAI and Grok asset pack](https://data.x.ai/logos/SpaceXAI_Grok_Assets.zip). Icons are centered on transparent canvases; logos are trimmed and scaled proportionally. The integration is community-maintained, not an official xAI product.

The complete [Brands validation](https://github.com/jeffglousher/core/actions/runs/34245078515) passes with zero issues.

## Type of change

<!--
  What type of change does your PR introduce to the Home Assistant Brands?
  NOTE: Please, check only 1! box! 
  If your PR requires multiple boxes to be checked, you'll most likely need to
  split it into multiple PRs. This makes things easier and faster to code review.
-->

- [x] Add a new logo or icon for a new core integration
- [ ] Add a missing icon or logo for an existing core integration
- [ ] Replace an existing icon or logo with a higher quality version
- [ ] Replace an existing icon or logo after a branding change
- [ ] Removing an icon or logo

## Additional information

<!--
  Details are important, and help maintainers processing your PR.
  Please be sure to fill out additional details, if applicable.
-->

- This PR fixes or closes issue: Not applicable; these assets accompany a new integration.
- Link to code base pull request: [jeffglousher/core#39](https://github.com/jeffglousher/core/pull/39).
- Link to documentation pull request: [jeffglousher/home-assistant.io#1](https://github.com/jeffglousher/home-assistant.io/pull/1).
- Link to integration documentation on our website: Not available until the new integration is merged.

## Checklist

<!--
  Put an `x` in the boxes that apply. You can also fill these out after
  creating the PR. If you're unsure about any of them, don't hesitate to ask.
  We're here to help! This is simply a reminder of what we are going to look
  for before merging your contribution.
-->

- [x] The added/replaced image(s) are **PNG**
- [x] Icon image size is 256x256px (`icon.png`)
- [x] hDPI icon image size is 512x512px for  (`icon@2x.png`)
- [x] Logo image size has min 128px, but max 256px, on the shortest side (`logo.png`)
- [x] hDPI logo image size has min 256px, but max 512px, on the shortest side (`logo@2x.png`)

<!--
  Thank you for contributing <3
-->
