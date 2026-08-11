# SpaceXAI — human-in-the-loop checklist

**Owner:** you (the human submitting author)  
**Agent role:** prepare branches, tests, kit, draft PRs, fill *technical* checklist boxes only.  
**You must:** understand every change, speak for the PRs, and perform the items below.

Canonical AI policy: [Open Home Foundation AI Policy](https://developers.home-assistant.io/docs/ai_policy) / [`AI_POLICY.md`](../../AI_POLICY.md).

---

## Status snapshot (fork)

| Track | State |
| --- | --- |
| Upstream-ready stack | `cursor/spacexai-up-*-2f69` on `jeffglousher/core` (base = current `upstream/dev`) |
| Fork draft PRs | `#14`→`#18`→`#17`→`#16`→`#21`→`#19`→`#22`→`#20` (+ kit `#15`); legacy `#1`–`#7`/`#12`/`#13` closed |
| Brands + CLA | [home-assistant/brands#10947](https://github.com/home-assistant/brands/pull/10947) ready-for-review — **sign CLA here** |
| Docs | Draft [home-assistant.io#47349](https://github.com/home-assistant/home-assistant.io/pull/47349) |
| Rebase onto `upstream/dev` | **DONE** @ `96092a2d` (full `up-*` rebuild 2026-08-11) |
| Strip fork-only paths | **DONE** on all `up-*` waves |
| Wave 1 bronze-first cleanup | **DONE** — honest bronze QS; clean `requirements_all` (+1 comment line); no Assist after-deps yet |
| Wave 1 pytest | **133 passed** @ `2023ad01` |
| First Core PR | **Ready for YOU to open as DRAFT** — branch `jeffglousher:cursor/spacexai-up-conversation-2f69` → `home-assistant/core` `dev` (~5660 / −16). Agent will not open Core PRs (AI policy). |
| Dedicated HA OAuth client | **Not required for wave 1** (Application Credentials). **A1 still blocks wave 4+** (device-code / CLI proxy headers). |

Open Core wave 1 as **draft** after you rewrite the PR body. Prefer CLA on brands; Core draft also triggers CLA if needed. Do **not** undraft until B1–B3 are true for you.

---

## A. Hard blockers (must clear before Core retarget)

- [ ] **A1. Dedicated Home Assistant OAuth client from xAI**  
      Replace borrowed Grok CLI client id / CLI identity headers with an HA-issued public client (or document temporary Application Credentials path maintainers accept).  
      Code today: `GROK_CLI_OAUTH_CLIENT_ID` / `GROK_CLI_REQUEST_HEADERS` in `homeassistant/components/spacexai/const.py`.

- [x] **A2. Rebase entire stack onto current `home-assistant/core` `dev`**  
      Done: `cursor/spacexai-up-base-2f69` tracks `upstream/dev`; waves 1–8 stack linearly on top.

- [x] **A3. Strip fork-only paths from every upstreamable branch**  
      Verified absent on `up-*` tips:
      - `.github/spacexai-contribution/**` (lives only on kit meta branch)
      - `.github/spacexai-pr-media/**`
      - `homeassistant/components/spacexai/brand/**`
      - local junk: `agent-tools/`, `tmp-brand-check/`

- [ ] **A4. Brands + docs land (or are accepted as merge-ready)**  
      - Complete the **brands edition** on [brands#10947](https://github.com/home-assistant/brands/pull/10947) (includes **A5 CLA** — see below)  
      - Undraft / merge [docs#47349](https://github.com/home-assistant/home-assistant.io/pull/47349) (bronze front matter is correct for the docs PR)  
      Wave 1 already marks `brands` / `docs-*` = `done` so Core Bronze CI can pass once those merge (or the same release train).

- [ ] **A5. CLA signed on the brands PR** (not deferred to Core)  
      Vehicle: [home-assistant/brands#10947](https://github.com/home-assistant/brands/pull/10947) under account `jeffglousher`.  
      Steps (you click; agent cannot write to the brands repo from this session):
      1. Open the PR → **Ready for review** (leave draft so the CLA bot may not fire).  
      2. Wait for the Home Assistant CLA bot comment / check.  
      3. Follow its link and sign [`CLA.md`](../../CLA.md) once for this GitHub account.  
      4. Confirm the CLA check is green, then continue brands review → merge.  
      Same signature covers later Core / docs PRs from this account.

---

## B. Before each Core PR is opened / undrafted

Repeat per wave (`up-conversation` … `up-platinum`):

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

- [ ] **B5. No fork media / kit required for review**  
      Do not ship `.github/spacexai-contribution/` or `.github/spacexai-pr-media/` into Core.

---

## C. Submission order (rearranged stack)

Do **not** skip ahead.

### Critical hassfest note

New integrations that declare `quality_scale: bronze` **must** have every Bronze rule `done`/`exempt`.  
Former separate “wave 8” brands/docs flip is **already folded into wave 1** on the `up-*` cut.

### Order

1. [ ] **Brands edition** on [brands#10947](https://github.com/home-assistant/brands/pull/10947)  
       Ready for review → **sign CLA (A5)** → address review → merge  
2. [ ] **Docs** undraft → address review → merge (keep `ha_quality_scale: bronze` until platinum docs follow-up)  
3. [ ] **A1 OAuth client** resolved in `const.py` (rebuild/push wave 4+ if needed)  
4. [ ] **Core wave 1** → `home-assistant/core` `dev`  
      Branch: `cursor/spacexai-up-conversation-2f69`. Conversation + Bronze with brands/docs rules already `done`. Link merged brands + docs PRs.  
5. [ ] **Core wave 2** → `cursor/spacexai-up-ai-task-2f69`  
6. [ ] **Core wave 3** → `cursor/spacexai-up-capabilities-2f69`  
7. [ ] **Core wave 4** → `cursor/spacexai-up-device-code-2f69` (only after A1)  
8. [ ] **Core wave 5** → `cursor/spacexai-up-hardening-2f69`  
9. [ ] **Core wave 6** → `cursor/spacexai-up-full-capabilities-2f69`  
10. [ ] **Core wave 7** → `cursor/spacexai-up-optimized-surface-2f69` (feature tip)  
11. [ ] **Core wave 8 (platinum)** → `cursor/spacexai-up-platinum-2f69`  
12. [ ] **Docs follow-up** — bump `ha_quality_scale` to `platinum` to match Core wave 8  

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

| Item | Evidence |
| --- | --- |
| Clean `up-*` stack from `upstream/dev` | `cursor/spacexai-up-base-2f69` … `cursor/spacexai-up-platinum-2f69` |
| Fork-only paths stripped | No kit/media/`brand/` on `up-*` tips |
| Wave 8 folded into wave 1 | w1 `brands: done` + bronze `docs-*`; tip `quality_scale: platinum` |
| Integration + tests | `homeassistant/components/spacexai/`, `tests/components/spacexai/` |
| Pytest spacexai (wave 1) | **133 passed** @ `2023ad01` (HA host) |
| Pytest spacexai (full tip, prior) | **241 passed** on earlier tip rebuild |
| Hassfest quality_scale (up tip) | Invalid integrations: 0 |
| Brands draft PR | [#10947](https://github.com/home-assistant/brands/pull/10947) |
| Docs draft PR | [#47349](https://github.com/home-assistant/home-assistant.io/pull/47349) |
| Contribution kit meta | [`#15`](https://github.com/jeffglousher/core/pull/15) `cursor/spacexai-contribution-kit-2f69` |
| Upstream-ready fork drafts | `#14` `#18` `#17` `#16` `#21` `#19` `#22` `#20` (see TRACKING) |

---

## F. When you are ready to retarget Core

After **A1**, **A4**, and **A5** are checked:

1. Confirm `up-base` still matches `upstream/dev` (rebase/rebuild if not).  
2. Open draft PRs on `home-assistant/core` in order C (retarget the existing `up-*` fork drafts).  
3. You undraft wave 1 only when you can defend it live in review.

Until then, keep everything on `jeffglousher/*` drafts.
