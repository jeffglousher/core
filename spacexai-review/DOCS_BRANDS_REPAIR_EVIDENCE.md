# Documentation and Brands repair evidence

Verified September 6, 2026. This file records completed work and remaining validation honestly; it is not an upstream submission.

This is the first completed documentation/Brands build record. The initial page
and Brands commit remain current. Subsequent follow-on documentation fixes,
current branch heads, and the refreshed native build are recorded in
[DOCS_QUALITY_REPAIR_EVIDENCE.md](DOCS_QUALITY_REPAIR_EVIDENCE.md); the later-layer
SHAs below are preserved historical evidence, not the active heads.

## Canonical documentation chain

The canonical documentation stack now uses six new `codex/spacexai/docs-*-next` branches. They are based on `upstream/next` at `2e9d474293b521eba15699e397b4ee7881074cc0`, refreshed from the official remote during this repair. The [official contribution guide](https://developers.home-assistant.io/docs/documenting/) requires `next` for new integrations and features.

All six branches were committed and atomically pushed to `jeffglousher/home-assistant.io`. A fresh remote listing returned these exact heads:

- `codex/spacexai/docs-01-initial-next`: `fcc39e84baa705e1c7cdc0eb4102e937dccfe487`. Initial conversation documentation, community-maintained relationship, messages/history/instructions/exposed entity data disclosure, provider privacy/terms links, account-permission troubleshooting, and quoted October release metadata. The complete initial diff is one new page, 96 lines.
- `codex/spacexai/docs-02-conversation-next`: `8bccd2013faa94782766cfb584236e80af456561`. Multiple agents, conversation attachments, tools, and their data sharing.
- `codex/spacexai/docs-03-ai-task-next`: `85b937de43f28224db14a9b7ed8e19591be11c9a`. AI tasks and image generation/editing, including source-file disclosure and the existing five-image limit.
- `codex/spacexai/docs-04-speech-next`: `a2806ce2b30c56c41d565964ac8541a69dcd2fc6`. Speech entities and disclosure of recorded audio and text sent for speech synthesis.
- `codex/spacexai/docs-05-video-next`: `f340cd9c39d0849416e54ca25088624acfeb6114`. Two action pages, video/source-image disclosure, and temporary media access explanation.
- `codex/spacexai/docs-06-account-next`: `28a35e6d433cef61639ad3f5c1a956dc653b4b97`. Same-account recovery, preserved entity settings, stored authorization, and automatic refresh explanation.

The previously published `spacexai-initial` and `spacexai/docs-02-conversation` through `spacexai/docs-06-account` remote refs are preserved, superseded historical copies. They are not a second active submission chain. No existing remote history was rewritten or deleted. The initial and final local worktrees now check out their corresponding canonical branches.

## Documentation verification

- Each canonical branch was checked out and validated independently against its immediate parent.
- The repository's native remark and textlint passed on every changed page at all six heads.
- Whitespace checks passed on each incremental diff.
- Each branch descends from the preceding canonical layer; the first descends from the official `next` ref.
- Native YAML parsing confirms `ha_release` is the string `2026.10` in every layer. The old unquoted value parsed as `2026.1`; the [official page-header guide](https://developers.home-assistant.io/docs/documenting/create-page/) explicitly requires quoting October releases.
- The integration page follows the existing template structure. No device/trigger/condition sections were invented for unsupported categories. Existing video action pages and examples were retained.
- Five missing follow-on documentation PR bodies were created. All six documentation drafts preserve every original template comment and checkbox, checked with a text comparison.
- No documentation PR, issue, comment, or release was opened.

The initial and final documentation now pass full native Jekyll builds on Ubuntu CI. Rendered HTML and assets are downloaded for visual inspection; a successful build is not recorded as a completed visual review.

## Brands source and verification

The existing Brands branch remains `spacexai-initial` at `e3ac8da8bf579ec54210cc211e1eaa0768052679`; a fresh remote listing confirms the same SHA, and the worktree is clean. No bitmap was altered.

The [previous Brands PR](https://github.com/home-assistant/brands/pull/10947) identifies the [official SpaceXAI and Grok archive](https://data.x.ai/logos/SpaceXAI_Grok_Assets.zip). Both retained downloads are available under `C:/Users/jeffg/Downloads`, have SHA256 `db9129acd4efc4c2202d25afe31b70281a79f8507f75520ab5e6b3356895a7e9`, and contain Windows download metadata with that official source URL. One records `https://x.ai/` as its referrer; the other records the earlier Brands PR. A fresh direct download was blocked by the provider's Cloudflare response, so this audit used the retained source archive and extracted originals.

The icons match the archive's black/white square symbol compositions, with opaque backgrounds removed and the symbols resized and centered on transparent square canvases. The logos match the archive's transparent black/white full symbols, cropped to their bounds and proportionally resized. The four logo alpha channels exactly match these source transformations; icon alpha-channel mean absolute differences are below 0.53/255, consistent with edge antialiasing. This is a source-shape comparison, not a claim of identical image encoding.

`verify_brand_assets.py` performs read-only checks. All eight files passed:

- Correct PNG names, domain directory, and no conflicting custom-integration directory.
- RGBA transparency and eight distinct file hashes.
- Icons at 256 by 256 and 512 by 512 pixels.
- Light logos at 670 by 256 and 1340 by 512 pixels; dark logos at 669 by 256 and 1339 by 512 pixels.
- Logos trimmed to their full alpha bounds and symbols recognizable in visual inspection.
- Comparison with the corresponding retained official source artwork.

The Brands draft now names the source and transformations instead of making an unsupported source assertion.

The repository's complete Bash/ImageMagick validator passed on native Ubuntu CI: 19,231 images checked, zero issues. Its log contains PNG-profile warnings for unrelated existing `moogo` and `ivideon` custom-integration assets, with no SpaceXAI warnings. Local ImageMagick/WSL availability is no longer a blocker to native verification.

## Native CI follow-through

The isolated fork-only validation branch `codex/spacexai-docs-validation` at `b05a0e23d7a2866c64bbec2a5f039b22f7f6ca48` adds only `.github/workflows/spacexai-docs-brands-validation.yaml`. It checks out the exact published initial/final documentation and Brands SHAs above, installs Ruby 3.4.8 with locked Bundler dependencies and ImageMagick on Ubuntu, runs native linters and `bundle exec rake generate`, and saves rendered pages/assets plus build evidence. It does not submit any upstream contribution.

Run: [SpaceXAI documentation and Brands validation](https://github.com/jeffglousher/core/actions/runs/34078694067). **Completed successfully** at 2026-09-07 03:13:47 UTC (September 6 in the local time zone). All three jobs passed: initial documentation in 3m14s, final documentation in 3m22s, and Brands in 3m58s. Both documentation jobs passed native remark/textlint and the repository-prescribed `bundle exec rake generate` without replacing or bypassing the build tasks.

Downloaded evidence is under `.tmp-spacexai-stack/native-docs-brands-34078694067/`. The initial preview root is `spacexai-docs-initial-34078694067/public/`, and the final preview root is `spacexai-docs-final-34078694067/public/`. Each contains `integrations/spacexai/index.html` and common assets; the final preview also contains both action pages. Serve each `public` root to inspect it with correct absolute asset paths. This evidence does not claim a visual inspection has happened.

During the root agent's initial-page visual check, the public Brands CDN reported the logo unavailable. This is the expected dependency on the unmerged Brands contribution, not a Jekyll rendering failure. The eight prepared local assets passed source and native validation; a public-CDN preview must not be reported as having displayed those pending assets.

Local workflow validation: YAML parsed and whitespace checks passed. The requested Core `script/setup` was attempted in the isolated worktree but failed because Windows uv creates `.venv/Scripts/activate` while that script requires `.venv/bin/activate`. The required `uv run --no-sync prek run --all-files` then failed because `prek` was not installed in that uninitialized environment. These are recorded as unavailable local checks, not passing checks.

## Prepared files

The primary agent independently opened the exact downloaded initial and final
Jekyll integration pages and both final action pages in a browser. Page headings,
configuration/disclosure content, sidebar layout, action descriptions, and the
October release render correctly. The public Brands CDN still supplies a logo
placeholder until the separate Brands contribution merges; this check does not
claim the prepared logo was served by that CDN. Temporary preview servers and
tabs were used only for inspection.

- `pr-bodies/docs-01-initial.md` through `pr-bodies/docs-06-account.md`.
- `pr-bodies/brands-01-initial.md`.
- `verify_brand_assets.py`.

Copies of the review descriptions are published in the separate fork-only review
packet. The upstream-shaped documentation branches contain only user
documentation, and the Brands branch contains only the eight approved assets.
