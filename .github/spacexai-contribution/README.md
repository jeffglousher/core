# SpaceXAI contribution kit

Preconfigured materials for submitting the `spacexai` integration as an
individual stacked contribution.

| Path | Purpose |
| --- | --- |
| [`HUMAN_CHECKLIST.md`](HUMAN_CHECKLIST.md) | **You (human)** — blockers, order, boxes only you can check |
| [`UPSTREAM.md`](UPSTREAM.md) | How to retarget clean branches onto `home-assistant/core` |
| [`STACK.md`](STACK.md) | Wave plan, validations, quality-scale flip PRs |
| [`TRACKING.md`](TRACKING.md) | Live smoke + external/Core draft PR links |
| [`brands/`](brands/) | Ready-to-PR Home Assistant brands assets + source notes |
| [`docs/spacexai.markdown`](docs/spacexai.markdown) | Drop-in page for `home-assistant.io` (`current`) |
| [`ARCHITECTURE_ADVERSARIAL_REVIEW.md`](ARCHITECTURE_ADVERSARIAL_REVIEW.md) | Architecture adversarial review (source of truth) |
| [`ARCHITECTURE_SITREP.html`](ARCHITECTURE_SITREP.html) | Visual sitrep linked from the review |

## Discovery

When auditing architecture recommendations, read the **in-repo** paths above.
Do not rely on `/opt/cursor/artifacts/` copies — those are VM-local and may be
absent on other checkouts or mid-stack branches.

Core implementation remains under `homeassistant/components/spacexai/` on the
feature stack branches. Demo PR media stays under `.github/spacexai-pr-media/`.

When deploying the Core tree as a HAOS `custom_components/spacexai` overlay for
live smoke, the overlay `manifest.json` must include a `"version"` field
(required for custom integrations). Upstream Core manifests omit it.
