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

Add light- and dark-theme icons and logos for the new SpaceXAI Core integration, with standard and high-density PNG variants.

The artwork comes from the [official SpaceXAI and Grok asset pack](https://data.x.ai/logos/SpaceXAI_Grok_Assets.zip), also identified in [the earlier brands submission](https://github.com/home-assistant/brands/pull/10947). The icons use the black and white square SpaceXAI symbol compositions with the opaque backgrounds removed, resized and centered on transparent square canvases. The landscape logos use the black and white transparent SpaceXAI symbols, trimmed to their artwork and proportionally resized. The source symbols have slightly different bounds, so the light and dark logo widths differ by one pixel at standard resolution.

Verified the eight files' PNG format, transparency, dimensions, unique content, domain placement, and source shapes. The downloaded source archive has SHA256 `db9129acd4efc4c2202d25afe31b70281a79f8507f75520ab5e6b3356895a7e9`; both retained downloads record the official URL in their download metadata. The four landscape-logo alpha channels exactly match the trimmed, resized source PNGs; icon shape comparisons allow for antialiasing.

The repository's native Bash/ImageMagick validator passed for commit `e3ac8da8bf579ec54210cc211e1eaa0768052679` in [fork validation](https://github.com/jeffglousher/core/actions/runs/34078694067): 19,231 images checked, zero issues.

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
- Link to code base pull request: https://github.com/home-assistant/core/compare/dev...jeffglousher:core:codex/spacexai/core-01-ready
- Link to documentation pull request: https://github.com/home-assistant/home-assistant.io/compare/next...jeffglousher:home-assistant.io:codex/spacexai/docs-01-initial-next
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
