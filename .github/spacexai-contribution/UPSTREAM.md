# Retargeting the SpaceXAI stack to `home-assistant/core`

Companion to [HUMAN_CHECKLIST.md](HUMAN_CHECKLIST.md). Agent prep notes; human owns the submit.

## Canonical branches (already built)

| Role | Branch |
| --- | --- |
| Base (= `upstream/dev`) | `cursor/spacexai-up-base-2f69` |
| Wave 1 … 7 | `cursor/spacexai-up-conversation-2f69` … `cursor/spacexai-up-optimized-surface-2f69` |
| Wave 8 platinum | `cursor/spacexai-up-platinum-2f69` |
| Kit meta (not for Core) | `cursor/spacexai-contribution-kit-2f69` |

Rebuild script (Windows): `agent-tools/build_upstream_stack.ps1`  
Host validate: `agent-tools/validate_up_tip.sh`

## Exclude from every Core branch

```
.github/spacexai-contribution/
.github/spacexai-pr-media/
homeassistant/components/spacexai/brand/
agent-tools/
tmp-brand-check/
```

Keep on Core: `homeassistant/components/spacexai/**` (minus `brand/`), `tests/components/spacexai/**`, plus generated wiring (`CODEOWNERS`, `.strict-typing`, `mypy.ini`, `requirements_all.txt`, `homeassistant/generated/*`).

## Flip to Core

1. Clear checklist **A1** (OAuth) and **A4** (brands/docs). **A5 CLA** is cleared during the brands edition (not on Core).  
2. `git fetch upstream dev` — if `up-base` diverged, re-run the build script.  
3. Retarget each stacked fork draft: base becomes the previous wave’s **Core** PR branch (wave 1 → `home-assistant/core` `dev`).  
4. Human undrafts in order; agent does not undraft Core PRs.

## External PRs

| Repo | Draft | Base | Notes |
| --- | --- | --- | --- |
| brands | https://github.com/home-assistant/brands/pull/10947 | `master` | **Sign CLA here** when marking ready for review |
| docs | https://github.com/home-assistant/home-assistant.io/pull/47349 | `current` | After brands + CLA |

## OAuth

Until xAI issues a Home Assistant client, Core maintainers may reject the hardcoded Grok CLI client id / User-Agent. Resolve policy before opening wave 4 upstream (CLI proxy headers land with device-code / entitlement on wave 4).
