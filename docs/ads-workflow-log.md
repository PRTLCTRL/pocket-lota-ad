# Ads workflow — reasoning log & operating state

**Started:** 2026-09-13
**Purpose:** Arsal asked for a repeatable ad-publishing workflow (creative → publish → measure), YouTube as a second channel, analytics reporting, and a hard CA$20 spend cap. This doc is the reasoning trace — chat stays short, decisions and live numbers land here.

---

## 1. Current live state (as of 2026-09-13 midday)

| Item | State |
|---|---|
| Boost ad (reel 122111124363452779) | **Active**, goal = website visitors, CTA = Shop now |
| Spend | **CA$0.90** of CA$20 lifetime cap |
| Results | 8 link clicks → 8 landing page views, 47 engagements, 39 3s video plays, 75 viewers |
| Cost per landing page view | ~CA$0.11 — cheap; at this burn the cap lasts ~3 weeks |
| Waitlist signups | 0 real (4 test emails filtered in analytics) |
| Reel #2 (v5b2 creative) | Published organically (free), processing → live on the page |
| Analytics | Daily cron `lota-ads-analytics` 9:15am → iMessage summary |

---

## 2. Workflow: creative → publish → measure (the standing loop)

1. **Pick creative** from `shorts/` — pool: v5b2 (now live as reel #2), v5b, v4 (in the running ad). Rotate next: v5b.
2. **Vet against brand locks** (see ads desk doc §2): extract 4 frames via ffmpeg, vision-check each. No drink-flask read, no bowl/body/peeing, imply-only staging.
3. **Publish reel** via Business Suite composer (CDP Edge). Free organic post; caption = problem-first + waitlist URL.
4. **Boost** — only with Arsal's explicit go (real money). Defaults: website-visitors goal, waitlist URL, Shop now, $5.50/day (CA$6.22 w/GST).
5. **Measure** via daily cron: KV signups + Business Suite metrics. Alert at CA$18; pause only on Arsal's OK.

### Cap math (important constraint)
Boost flow has **no lifetime budget** — daily only. CA$20 cap therefore means:
- One boost at $5.50/day ≈ 3.2 days of run. A second boost at that rate does **not** fit in the remaining cap.
- Rule: finish one boost's planned run, then start the next (staggered), or lower daily budget for round 2. Never run two boosts concurrently at $5.50/day.
- Cumulative spend across ALL ads is what counts.

---

## 3. Decisions & reasoning (2026-09-13 session)

### 3.1 Side-by-side debug Edge (no-kill launch) — key discovery
Old assumption: launch the CDP debug Edge = kill his normal Edge first (script did `taskkill /IM msedge.exe /F`). Tested instead: launching with `--user-data-dir=C:\Users\Arsal\EdgeDebugProfile` **alongside** his running Edge works fine — separate data dirs are allowed. FB session in the clone is still logged in.
→ Consequence: daily analytics never closes his tabs. Analytics jobs are now forbidden from killing msedge. Kill remains necessary only when re-cloning the profile fresh.

### 3.2 Analytics via KV, not the website
Signup data lives in the Worker's KV namespace. Wrangler OAuth is logged in on this machine (PRTL account) → `wrangler kv key list --binding WAITLIST --remote` from the repo dir returns all signups. Analytics script (`~/AppData/Local/hermes/scripts/pocket_lota_analytics.py`) filters known test emails and counts real leads. No webhook wiring needed yet.

### 3.3 Meta metrics via CDP scrape (no API token)
No Meta access token on this machine, so the collector drives the debug Edge to Business Suite → Content → "Recent ads" panel and parses the metrics block. Verified parser offsets against the live page (values sit 1–3 rows after their labels; parser now scans ahead for numeric patterns). Read-only — it never clicks Boost/publish controls.

### 3.4 AI still generation — tested, needs prompt work before use
OpenAI key present → `gpt-image-1` works from this box. First test still: passed imply-only/no-bowl/no-body locks but **failed the not-a-drink-flask lock** — domed cap + glassy gooseneck spout read as thermos/teapot. Fix notes for the next prompt: open flared rim (no cap), single-material matte spout, pronounced arc + shorter stream, keep the dark-tile context. Not posting AI stills until they pass all locks.

### 3.5 Reel #2 publish — wizard quirks captured
Composer route worked start-to-finish (upload 100% → copyright pass in ~9s → caption → Next → Next → Share). Trap: the top "Create | Edit | Share" row is step TABS; the real submit is a second Share button bottom-right (y > 1000 on a 1400px window). First attempt clicked the tab and silently didn't submit — resolved by clicking by geometry. Scripts saved: `reel2_publish.py` (stage), `reel2_wizard.py` (advance), `reel2_share.py` (submit).

---

## 4. YouTube channel — plan + blocker

Brand rule: dedicated **Pocket Lota** channel only (never the football/EPL one). Plan:
1. Arsal logs into Google in the debug Edge window (his hands — one time).
2. Create the Pocket Lota brand channel.
3. Upload Shorts via studio.youtube.com (CDP set_files; test one short — YT's uploader untested, fallback = copy to Downloads + manual click).
4. **Organic only** — no Google Ads spend, keeps total spend inside CA$20.
5. Once the channel exists, add a YT-Studio metrics block to the analytics collector.

**Blocker:** YouTube is signed out in the debug profile. Needs ~2 minutes of Arsal's time.

---

## 5. Open questions for Arsal (answer whenever)

1. YouTube login (above) — when convenient.
2. Round-2 boost preference when round 1 nears its cap: stagger a second $5.50/day boost, or drop daily budget (e.g. $3/day traffic min) to stretch the remaining dollars?
3. Raise the CA$20 cap? Current burn suggests ~CA$0.25–0.30/day — the cap is not the constraint it looked like on Sep 12.

---

## 6. Artifacts index

| What | Where |
|---|---|
| Analytics collector | `~/AppData/Local/hermes/scripts/pocket_lota_analytics.py` |
| Reel publish scripts | `~/AppData/Local/hermes/scripts/reel2_*.py` |
| Daily analytics cron | `lota-ads-analytics` (id 9b87fe3e8284), 9:15am ET |
| Old one-shot watchdog | retired (was 42ae297fe59a) |
| Playbook (skills) | `meta-ads-ops` + `user-browser-automation` skills, updated 2026-09-13 |
| Creative pool | `shorts/lota-problem-{v4,v5b,v5b2}-1080x1920.mp4` |

## 7. Multi-platform pipeline (Arsal's direction, Sep 13 evening)

Goal: one pipeline that distributes Pocket Lota ads across the major platforms,
rolled out **one platform at a time** — test, measure, then add the next.
Content is produced/rotated on the fly from the creative pool + AI stills
(once they pass brand locks). Analytics unified per platform.

Rollout order (reasoning: Meta is live & converting → extend organics first
(free) → then next paid platform only with measured signal):
1. **Meta (live)** — boost reel ad + organic reels. Analytics cron daily.
2. **YouTube (next)** — reuse Arsal's general channel (his OK, Sep 13):
   organic Shorts now; Google Ads later. Organic = free, no cap impact.
   Google Ads needs: his login in debug Edge (blocker) → video campaign
   (in-feed/skippable), billing setup, its own budget line within/near the
   CA$20 philosophy. Decide budget split when we get there.
3. **TikTok** — brand account + organic; TikTok Ads later (needs its own
   billing; watch content rules — imply-only works well there).
4. **Later candidates**: Instagram (only if linked to the Page), X, Pinterest.

Pipeline shape (per platform): creative vet → native upload (organic) →
measure N days → paid boost/campaign decision (Arsal's go, money) →
daily analytics → rotate creative on underperformance.

### YouTube specifics (updated 2026-09-13 — FIRST SHORT PUBLISHED ✅)
- Channel: Arsal's personal channel "Arxa" (`UCZ3fFcppk_0dgQSdOgXZIbQ`) — his
  general channel, explicitly OK'd. The old channel id in docs (UCfzTGK…) is
  NOT the Studio-active one; `studio.youtube.com/` root redirects to the right
  channel. Always follow the redirect.
- **Upload recipe (verified)**: CDP on port 9222 → Studio → Create menu →
  "Upload videos" → **`DOM.setFileInputFiles` on the hidden
  `input[type=file]`** (playwright's expect_file_chooser races and fails;
  raw CDP DOM command works deterministically). Then Details step:
  title/description via `Input.insertText` after focusing contenteditables
  (keyboard typing is fine too), **MUST answer the "made for kids" radio**
  ("No, it's not made for kids" at ~(418,1434)) — Next stays disabled without
  it ("You need to answer this question"), then Next×3 → Visibility step →
  click Public radio → Publish. Confirmation = "All changes saved" + row in
  Content → Shorts with visibility "Public".
- **Studio tab can wedge** after heavy CDP use (Runtime.evaluate times out
  even via raw websocket; body innerText stuck). Recovery: close the dead tab
  via `GET /json/close/<id>`, open fresh via `PUT /json/new?<url>`, attach to
  the new target. Prefer ONE playwright session per script (connect → work →
  disconnect); don't stack debugger sessions — that's what wedged it.
- Visibility default = Private; always flip to Public before Publish.
- Google Ads: still gated on Meta round-1 signal + budget split with Arsal.
- YT analytics: extend pocket_lota_analytics.py with a Studio-scrape block
  (views/impressions on the Short row) next session.

## put.io as source/vault layer (Sep 13)
Arsal wants put.io wired in: magnet downloads + shared vault for shorts/videos
(his preferred file system vs Google/OneDrive). Skill `putio` created (API v2
helper `scripts/putio.py`, token synced to `~/.env` as PUTIO_TOKEN — VERIFIED
live 2026-09-13; /v2/me 404s, use /account/info). Pipeline role: put.io =
media source + team sharing; shorts vault mirrors local `shorts/` with naming
`platform-creative-vN-YYYYMMDD.mp4`.

## Google Ads (YouTube paid) — prep done, waiting on Arsal billing
Full brief in `docs/google-ads-launch-prep.md`. Recommendation: Demand Gen
(Shorts-native, 9:16 creative fits), $3–5/day, US geo, waitlist destination,
link-click proxy goal until a conversion pixel exists. Global paid cap stays
CA$20 until he raises it — at $5/day YT + $6.22/day Meta boost, both don't
fit; stagger or ask for a raise. He sets up billing himself; when he says
go, drive campaign setup in debug Edge (same discipline as Meta).
## Sep 15 — cap raised to CA$30; page de-sketchified; analytics fixed
- Arsal raised lifetime cap CA$20 → CA$30. Watchdog alert now CA$27 (job 9b87fe3e8284 updated). Daily budget unchanged $5.50.
- Analytics fix: Meta moved ads panel off content_center; pocket_lota_analytics.py now reads `business.facebook.com/latest/ad_center/ads_summary?asset_id=1309108135614803`. Card layout = value BEFORE label ("1345\nViews\n972\nViewers\n114\nLanding Page Views\nCA$12.45\nSpent at ..."), anchor on the CA$/Spent-at pair. Verified live: CA$12.48 spend, 1345 views, 972 viewers, 114 LPV, 0 real signups.
- FB page trust pass (was: no avatar, no cover, 0 posts vibe):
  - Avatar: lota-lemon.png auto-cropped to character, 84% fill, 512px → fb-page/fb-avatar-512.jpg. Uploaded via CDP (Profile picture actions → Choose profile picture → input[nth=2] → Save).
  - Cover: designed 1640x624 banner in fb-page/fb-cover-final2.jpg (tote photo left + brighten 1.12, feathered blend, "Pocket Lota" yellow + tagline + CTA right; all text inside mobile-safe x265-1374). Uploaded + saved via crop dialog.
  - Bio set with waitlist URL. Website field: FB about-contact editor didn't render form fields (known FB bug path); add later via Page settings if needed.
  - Verified by screenshot: cover + mascot visible, no add-cover prompt.
- Industry research (conversion diagnosis) dispatched to research subagent; findings to be appended here when it returns.

## Sep 15 — conversion research digest (knowledge-based; verify before betting spend)
Benchmarks: median LP CVR 2-3% (unbounce.com/conversion-benchmark-report/); cold Meta traffic → unknown DTC waitlist typically 1-5%; LPV/link-clicks should be ≥70-80% (Meta). ~95% of Meta traffic is mobile. Visitor-optimized boost targets CLICKERS not converters — root cause of high LPV/0 signups; delivery matches click-prone low-intent users (our 55+/65+ skew confirms).
LP fixes (standard CRO): single email field above fold, <3s mobile load, attention ratio 1:1 (no nav leakage), message match ad↔hero, incentive + launch date + waitlist counter.
FB page trust: users vet page before converting; barebones page depresses CTR+trust (sproutsocial.com/insights); Meta ranks completeness as ad-quality input. → DONE Sep 15: avatar+cover+bio live.
Market: portable bidet buyers = 25-54 slight female skew + travelers/office/postpartum/IBS + religious lota users (grandviewresearch.com). TUSHY=irreverent humor, HappyPo=design, Brondell GoSpa=utility. UGC POV video > polished static.
CTA: "Shop now" on waitlist page = conversion killer (expectation mismatch, Meta matches shoppers who bounce). Fix → "Learn more" or "Sign up" + on-page first-person button copy.
TOP-5 ACTIONS: (1) swap CTA + signup-optimized objective (lead form or LP conversion event) — needs Arsal go (money-adjacent, changes live ad); (2) page first-screen rebuild: email+button+incentive above fold; (3) proof block in one scroll (demo GIF, 3 bullets, privacy note, launch date, counter); (4) FB page trust floor — DONE (avatar/cover/bio; still need 5-10 posts + invites); (5) 3 creative angles: comfort/health 45+ women, office-day agitation, cultural lota angle — UGC style.
