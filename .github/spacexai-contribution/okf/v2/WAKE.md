# SpaceXAI OKF v2 — read this first

Official Home Assistant contribution knowledge for the SpaceXAI super
stack. Retrieved **2026-08-15**. Kit-only: never commit this folder onto
Core-bound slices.

## Before you change code

1. Read `rules.yaml` for MUST/SHOULD items that apply to this change.
2. Read `GAPS.md` so you do not re-litigate scored collisions.
3. Keep kit / `.cursor/` / OKF files off Core-bound PRs.

If this path is missing on the current branch:

```text
git show origin/cursor/spacexai-contribution-kit-2f69:.github/spacexai-contribution/okf/v2/WAKE.md
```

## Hard stops

- Do not touch official Core `#178765` (conversation-only).
- Do not put OKF, kit, or `.cursor/` files on `#14`, `#23`–`#24`,
  `#28`–`#32`, `#34`–`#37`, or later Core-bound tips.
- Do not extract a PyPI `spacexai` library this pass. Peer is
  `openai_conversation` + pinned `openai==2.45.0`.
- Do not drop OAuth `conversations:read/write` without a reauth plan.
- Do not mark `#37` ready or merge any wave.
- Do not rewrite already-pushed commits on open PR branches.
- New commits: HA imperative, no trailing period.
- Autonomous official PRs/comments are forbidden (OHF AI policy).

## Where work goes

| Work | Branch / PR |
| --- | --- |
| OKF, WAKE, STACK, TRACKING | `cursor/spacexai-contribution-kit-2f69` / `#15` |
| Confirmed code/test hygiene | tip on `cursor/spacexai-media-friction-2f69` |
| Brands / docs | `brands#10947`, `docs#47349` — published URLs still 404 |

## Score the stack honestly

Official review rules collide with a stacked local campaign:

- Dependent PRs and more than five open PRs are forbidden on
  `home-assistant/core`. Local fork staging is allowed.
- Protocol code belongs on PyPI. We keep a thin `openai` wrapper and
  document the peer exception until a later library extraction.
- Platinum is claimed while brands/docs CDNs 404. Keep `done` plus
  comments. Do not flip those rules to `todo` on Core slices.
- Wave 1 is ~5.7k. Trim exotic tests later, not production modules.

Sources and hashes: `manifest.yaml`, `sources.yaml`, `snapshots/`.
