# SpaceXAI brands source notes

Target repository: [`home-assistant/brands`](https://github.com/home-assistant/brands)  
Target path: `core_integrations/spacexai/`  
Integration domain: `spacexai`

## Official pack

| Field | Value |
| --- | --- |
| Pack | [`SpaceXAI_Grok_Assets.zip`](https://data.x.ai/logos/SpaceXAI_Grok_Assets.zip) |
| Brand guidelines | [xAI Brand Guidelines](https://x.ai/legal/brand-guidelines) |
| Retrieved | 2026-08-09 |
| Variant used | **SpaceXAI symbol** (not the Grok monogram) |

Guidelines require using logos exactly as provided, without alteration. For Home Assistant brands we only **uniformly scale** / letterbox onto the required canvas (contain-fit, no crop, no distortion). Solid squared backgrounds from the pack are converted to transparent so HA light/dark themes work; mark geometry is unchanged.

## Source files kept in this folder

| File | Role |
| --- | --- |
| `original_spacexai_symbol_black_squared.png` | Light icon source (black mark, squared) |
| `original_spacexai_symbol_white_squared.png` | Dark icon source (white mark, squared) |
| `original_spacexai_symbol_black_transparent.png` | Light logo source (black mark) |
| `original_spacexai_symbol_white_transparent.png` | Dark logo source (white mark) |
| `original_spacexai_symbol_black_transparent.svg` | Vector reference |
| `original_spacexai_symbol_white_transparent.svg` | Vector reference |

## Generated Home Assistant sizes

Produced under `core_integrations/spacexai/`:

| File | Spec |
| --- | --- |
| `icon.png` / `icon@2x.png` | 256 / 512 square, black SpaceXAI symbol, transparent |
| `dark_icon.png` / `dark_icon@2x.png` | 256 / 512 square, white SpaceXAI symbol, transparent |
| `logo.png` / `logo@2x.png` | shortest side 256 / 512, black SpaceXAI symbol |
| `dark_logo.png` / `dark_logo@2x.png` | shortest side 256 / 512, white SpaceXAI symbol |

## Submission checklist

- [ ] Open PR to `home-assistant/brands` against `master` with only `core_integrations/spacexai/*`
- [ ] Link that PR from the `home-assistant.io` docs PR and from core wave 1
- [ ] After merge, flip `brands: done` in core quality_scale (wave 8)
