# Retargeting the SpaceXAI stack to `home-assistant/core`

Companion to [HUMAN_CHECKLIST.md](HUMAN_CHECKLIST.md). Agent prep notes; human owns the submit.

## Exclude from every Core branch

```
.github/spacexai-contribution/
.github/spacexai-pr-media/
homeassistant/components/spacexai/brand/
agent-tools/
tmp-brand-check/
```

Keep on Core: `homeassistant/components/spacexai/**` (minus `brand/`), `tests/components/spacexai/**`, plus generated wiring (`CODEOWNERS`, `.strict-typing`, `mypy.ini`, `requirements_all.txt`, `homeassistant/generated/*`).

## Suggested clean rebuild (after checklist A1–A5)

```bash
git fetch upstream dev
# For each wave tip commit, create a clean branch from upstream/dev (wave 1)
# or previous clean wave (waves 2+), then:
git checkout -b upstream/spacexai-wave1 upstream/dev
git checkout <fork-wave1-tip> -- homeassistant/components/spacexai tests/components/spacexai
# apply generated file updates via hassfest / gen scripts
# ensure quality_scale brands/docs are done on wave 1 for CI
# do NOT checkout .github/spacexai-* or components/spacexai/brand
```

Repeat per wave with only that wave’s incremental paths from `git diff --name-only waveN-1..waveN`.

## External PRs

| Repo | Draft | Base |
| --- | --- | --- |
| brands | https://github.com/home-assistant/brands/pull/10947 | `master` |
| docs | https://github.com/home-assistant/home-assistant.io/pull/47349 | `current` |

## OAuth

Until xAI issues a Home Assistant client, Core maintainers may reject the hardcoded Grok CLI client id / User-Agent. Resolve policy before opening wave 4 upstream (or wave 1 if entitlement headers are already present in early waves — today CLI proxy headers land with device-code / entitlement work on wave 4+).
