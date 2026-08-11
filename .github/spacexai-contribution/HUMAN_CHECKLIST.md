# SpaceXAI — human-in-the-loop checklist

**Owner:** you (the human submitting author)  
**Agent role:** prepare branches, tests, kit, draft PRs, fill *technical* checklist boxes only.  
**You must:** understand every change, speak for the PRs, and perform the items below.

Canonical AI policy: [Open Home Foundation AI Policy](https://developers.home-assistant.io/docs/ai_policy) / [`AI_POLICY.md`](../../AI_POLICY.md).

---

## Status snapshot (fork)

| Track | State |
| --- | --- |
| Feature stack waves 1–7 | Draft PRs `#1`–`#7` on `jeffglousher/core` |
| Quality waves 8–9 | Draft PRs `#13` → `#12` |
| Brands | Draft [home-assistant/brands#10947](https://github.com/home-assistant/brands/pull/10947) |
| Docs | Draft [home-assistant.io#47349](https://github.com/home-assistant/home-assistant.io/pull/47349) |
| Fork `dev` vs upstream `dev` | **~109 commits behind** — must rebase before Core retarget |
| Dedicated HA OAuth client | **BLOCKER** — still using Grok CLI public client id |

Do **not** open or undraft against `home-assistant/core` until sections A–C below are done.

---

## A. Hard blockers (must clear before Core retarget)

- [ ] **A1. Dedicated Home Assistant OAuth client from xAI**  
      Replace borrowed Grok CLI client id / CLI identity headers with an HA-issued public client (or document temporary Application Credentials path maintainers accept).  
      Code today: `GROK_CLI_OAUTH_CLIENT_ID` / `GROK_CLI_REQUEST_HEADERS` in `homeassistant/components/spacexai/const.py`.

- [ ] **A2. Rebase entire stack onto current `home-assistant/core` `dev`**  
      Fork `dev` is stale. After rebase, every wave’s PR base must be the *previous wave’s upstream PR branch* (or `dev` for wave 1), not `jeffglousher` feature tips alone.

- [ ] **A3. Strip fork-only paths from every upstreamable branch**  
      Must **not** appear on Core PRs:
      - `.github/spacexai-contribution/**`
      - `.github/spacexai-pr-media/**`
      - `homeassistant/components/spacexai/brand/**` (custom overlay; Core uses `home-assistant/brands`)
      - local junk: `agent-tools/`, `tmp-brand-check/`

- [ ] **A4. Brands + docs land (or are accepted as merge-ready)**  
      - Undraft / merge [brands#10947](https://github.com/home-assistant/brands/pull/10947)  
      - Undraft / merge [docs#47349](https://github.com/home-assistant/home-assistant.io/pull/47349) (bronze front matter is correct for the docs PR)  
      Wave 8’s `brands` / `docs-*` = `done` is only honest **after** those merge (or the same release train).

- [ ] **A5. CLA signed** for the GitHub account that will author Core PRs  
      Sign via the CLA bot when the first upstream PR opens (if not already).

---

## B. Before each Core PR is opened / undrafted

Repeat per wave (`#1` … `#7`, then `#13`/`#12` equivalents on Core):

- [ ] **B1. You can explain the wave’s diff in your own words** (AI policy).  
      Practice: purpose, main modules, failure modes, what this wave adds vs prior.

- [ ] **B2. You wrote or fully rewrote the PR description** (agent draft is only a starting point).

- [ ] **B3. Check the human-only PR template boxes yourself**  
      Leave agent-filled technical boxes as-is only if you agree they are true:
      - [ ] *I understand the code I am submitting and can explain how it works.* ← **you**
      - [ ] *I have followed the development checklist*
      - [ ] *I have followed the perfect PR recommendations*
      - [ ] *Any generated code has been carefully reviewed…*
      - [ ] *I have reviewed two other open pull requests*

- [ ] **B4. Confirm stack base**  
      Wave *N* targets previous wave’s **Core** PR branch (wave 1 → `dev`).

- [ ] **B5. No fork media required for review**  
      Optional: host GIFs elsewhere or attach manually; do not ship `.github/spacexai-pr-media/` into Core.

---

## C. Submission order (intricate stack)

Do **not** skip ahead.

### Critical hassfest note

New integrations that declare `quality_scale: bronze` **must** have every Bronze rule `done`/`exempt`.  
On the fork, waves 1–7 still leave `brands` / `docs-*` as `todo` until wave 8 — that **fails** Core CI.

**Upstream cut therefore folds wave 8 into wave 1** (after brands + docs merge): wave 1’s `quality_scale.yaml` already has `brands` + applicable `docs-*` = `done`. Keep a tiny wave 8 only if something remains to flip; otherwise skip straight from feature tip (wave 7) to platinum (wave 9).

### Order

1. [ ] **Brands** undraft → address review → merge  
2. [ ] **Docs** undraft → address review → merge (keep `ha_quality_scale: bronze` until platinum docs follow-up)  
3. [ ] **Core wave 1** → `home-assistant/core` `dev`  
      Conversation + Bronze declaration with brands/docs rules already `done` (wave-8 content included). Link merged brands + docs PRs.  
4. [ ] **Core wave 2** → base = wave 1 branch  
5. [ ] **Core wave 3** → base = wave 2  
6. [ ] **Core wave 4** → base = wave 3 (device-code + OAuth — only after A1 is clear)  
7. [ ] **Core wave 5** → base = wave 4  
8. [ ] **Core wave 6** → base = wave 5  
9. [ ] **Core wave 7** → base = wave 6 (feature tip)  
10. [ ] **Core wave 9 (platinum)** → base = wave 7 (or wave 8 if used)  
11. [ ] **Docs follow-up** — bump `ha_quality_scale` to `platinum` to match Core wave 9  

While a wave is under review, do not force-push rebased history without coordinating with reviewers.

---

## D. Live smoke you should re-confirm on a clean Core-like install

(Agent already smoked the HAOS overlay; you should be able to demo these.)

- [ ] Device-code sign-in (or browser) with Application Credentials  
- [ ] Conversation / Assist HA control  
- [ ] AI Task `generate_data` + `generate_image`  
- [ ] `spacexai.generate_video`  
- [ ] STT / TTS selectable; preferred Assist pipeline wiring if you opt in  
- [ ] Diagnostics redact tokens; reauth path  

Notes: [TRACKING.md](TRACKING.md).

---

## E. Agent-completed (do not redo unless something regresses)

These are done on the fork tip / drafts as of wave 9 `cursor/spacexai-quality-platinum-0109`:

| Item | Evidence |
| --- | --- |
| Integration + tests | `homeassistant/components/spacexai/`, `tests/components/spacexai/` |
| Pytest spacexai | **241 passed** (HA host clone) |
| Ruff clean on spacexai | checked |
| Hassfest `quality_scale` (wave 9 tip) | Invalid integrations: 0 |
| Brands pack dimensions | 256/512 icons; logos shortest side 256/512 |
| Brands draft PR | [#10947](https://github.com/home-assistant/brands/pull/10947) |
| Docs draft PR | [#47349](https://github.com/home-assistant/home-assistant.io/pull/47349) |
| Fork stack PRs | `#1`–`#7`, `#13`, `#12` (draft) |
| Quality flips | Wave 8 brands/docs `done`; wave 9 `platinum` |
| Assist speech sync | Preferred pipeline can wire `stt.grok_stt` / `tts.grok_tts` |
| Technical PR checklist boxes | Agent filled on fork drafts where factually true |

---

## F. When you are ready to retarget Core

Ask the agent (or run yourself) only after **A1–A5** are checked:

1. Sync `upstream/dev`.  
2. Rebuild **clean** stacked branches (no kit/media/`brand/`).  
3. Open draft PRs on `home-assistant/core` in order C.  
4. You undraft wave 1 only when you can defend it live in review.

Until then, keep everything on `jeffglousher/*` drafts.
