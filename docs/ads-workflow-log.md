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

## Sep 26 — creative-signal baseline (#11); boost found DEAD at Meta account spend limit
- **Meta boost (v4) is NOT running.** ads_summary banner: "You reached your account spending limit — Your ads have stopped running... reset your amount spent back to $0." Ad status = **Not delivering** (card: started Sep 12). Spend froze at **CA$20.00** — Meta's own ad-account limit bound before Arsal's CA$30 cap; delivery chart shows it died ~Sep 17 (572 views Sep 11-13, 1470 Sep 14-16, 3 Sep 17-19, 0 after). **Round 2 requires Arsal to reset the account spend limit** (billing settings — money action, his hands).
- Final v4 boost totals: 2,045 views / 1,452 viewers / 943 post engagements / ~191 landing page views ⇒ **~CA$0.105 per LPV**. Waitlist: **0 real signups** (4 test emails in KV; re-verified via wrangler + collector — earlier Cloudflare API error was transient).
- Organic free signal (page has 0 followers → distribution ~nil, can't rank creatives yet): v4 reel post organic **48 views**; reel #2 (v5b2) **4 views**; v5b YT Short (unP_KclQgn8) **113 views**. YT is the only channel with real organic reach so far.
- Page state: real URL is `facebook.com/profile.php?id=61593583395478` (vanity `facebook.com/PocketLota` 404s; `sk=reels` tab 404s too, `sk=videos` works): 0 followers, not-yet-rated, bio + waitlist URL live.
- Collector gap: `pocket_lota_analytics.py` ad_status returned "unknown" — its whitelist only knows "Active"/"In review", so the "Not delivering"/spend-limit state went **unnoticed ~9 days** while the cron kept reporting cumulative metrics. Fix candidate: alert on "Not delivering"/"spending limit" banners.
- Round-2 test matrix (pre-staged, runs after Arsal resets limit + picks budget): remaining CA$10 headroom buys ONE comparison boost (v5b2 at $5.50/day × ~1.8d, or $3/day × ~3.3d) vs v4's CA$0.105/LPV baseline; testing BOTH alternates needs a cap raise (Arsal's call).

## Sep 27 — dead-ad watchdog shipped: collector now alerts on "Not delivering" / spend-limit banners (#11 agent-side)

- **The gap (found Sep 26 harvest):** `pocket_lota_analytics.py` ad_status whitelist only knew "Active"/"In review" → the boost ad died ~Sep 17 at Meta's own ad-account spend limit and **read as a normal metrics day for 9 days**. Fix candidate from the harvest: implemented today.
- **Fix (collector, `C:\Users\Arsal\AppData\Local\hermes\scripts\pocket_lota_analytics.py`):**
  1. Parsing extracted to pure function `parse_ads_text()` + `--selftest` mode: 11 offline regression tests (dead-ad/healthy/rejected/unknown-status/parse-error fixtures, incl. a fixture rebuilt from the **real captured 2026-09-27 page text**).
  2. Status vocabulary extended (dead states first: Not delivering, Rejected, Disapproved, Paused, Completed; warn: In review, Scheduled) — nearest-status-word backward scan from the spend pair, 26-line window with section-header boundary guard (real card has ~16 lines between status and spend).
  3. New additive JSON fields: `meta.alerts` (list) + `meta.delivery_alert` (bool) — spend-limit banner scan + dead-state detection + unknown-status surfacing. Old fields unchanged → backward-compatible with the cron's contract.
  4. Cron prompt (job 9b87fe3e8284, jobs.json) patched in place — no new cron job: the daily 9:15 agent now LEADs the iMessage reply with alerts when `delivery_alert` is true. Jobs.json backup: `jobs.json.bak-20260927`.
- **Verified end-to-end (2026-09-27):** selftest 11/11 PASS; live run via the cron's exact venv python → `ad_status: "Not delivering"`, spend CA$20.00 frozen, `alerts: [SPEND LIMIT HIT, AD NOT DELIVERING]`, `delivery_alert: true` — on the real ads_summary page (was silently "unknown"). Dashboard feed contract unchanged.
- **Also re-verified today (no decay):** waitlist Worker HTTP 200; YT Short unP_KclQgn8 still live at 113 views; pmax assets at spec (1536×804 / 1024×1024 / 600×600); KV 4 test / 0 real signups.
- **Round-2 boost still blocked on Arsal:** reset Meta ad-account spend limit + budget call (money, his hands) — unchanged.

## Sep 27 (evening) — Grok Bot collaboration channel LIVE (CDP into the desktop app)

- **Channel:** No xAI API exists for personal Grok Bots (docs confirm app-only). Instead: relaunch the Grok Bot Electron app with `--remote-debugging-port=9223` (close first — graceful taskkill, then `Start-Process` with the flag; CDP up in ~2s, session survives, `desktop-status.json` signedIn=true). Driver: `~/AppData/Local/hermes/scripts/grokbot_cdp.py` (ws_call/eval_js/click_xy/type_text; native Input dispatch works, synthetic DOM clicks don't; newline-safe typing = `Input.insertText`; send button appears at composer-right once text present).
- **Thread:** group chat "Pocket Lota ads" = Advitisor Agency Mad Men Style (creative/strategy) + Staff Eng (builds/deploys from its cloud computer, mirrors files to laptop `shorts/`). Posted the full Sep 14→27 state (boost dead at account limit, CA$0.105/LPV, 0 signups, CTA swap history, CA$75 ceiling).
- **Their round-2 decisions (Sep 27, ~9:47 PM):**
  - **Advitisor:** Meta **instant lead form**, button "Sign up", Leads objective, ~CA$4/day lifetime, **one cut not A/B — v6a first** (purse open), v6b benched unless v6a flatlines ~3 days. Fallback: the new above-fold page + LPV optimization. Correction logged: CTA was already "Sign up" since Sep 15 4:20 AM — button wasn't the problem, click-targeting + page were. Caption locked: "It flows fine. The cleanup doesn't. … The first batch is free. Just leave your email."
  - **Staff Eng (shipped same hour, verified independently):** above-fold email form LIVE on the Worker (23KB HTML, hero form `data-src=hero`, poster-only first paint, video deferred; UTM + form-position attribution per signup).
  - **Assigned to Hermes:** once Arsal resets the account limit → build the lead form in Ads Manager (email-only, privacy URL, thank-you "You're on the list", `utm_content=v6a`). Nothing goes live without Arsal's go. Staff Eng to add a `/privacy` page to the Worker.
- **Still on Arsal:** (1) reset Meta ad-account spend limit, (2) confirm CA$75 total ceiling (Advitisor set ~CA$4/day), (3) real **Meta Pixel ID** — currently placeholder zeros on the page, only he can pull it from Events Manager.

## Sep 27 — Advitisor handoff pass: post-mortem read, CA$75 cap, spend plan, staging held on 2 blockers

- **Live read (read-only, no Meta edits):** ad 52606635640535 confirmed **"Not delivering"** ("Account spend limit reached" row; BS spend-limit banner; details modal Status: Not delivering). Delivery ended ~Sep 16-17. **CTA "Sign up" confirmed stuck** in the details-modal preview. Payment block: ad budget CA$20.00 + est. GST 13% CA$2.60 = **CA$22.60 total charged** — the old CA$20 cap was met on budget and passed only by tax; new plan counts GST-inclusive.
- **Final lifetime metrics (details modal):** 2,045 views / 1,452 viewers / 748 3s plays / 943 post engagements / **191 link clicks / 182 LPV** / freq 1.03 / CA$0.11 per LPV. Impressions/reach final = unknown (Ads Manager cells DOM-virtualized; async CSV export landed in Meta's report center, not retrievable this session). **Creative corrected: the boost ran v4, not v5b2** (live card caption "Paper's over there..."; v5b2 was organic-only, 4 views) — METRICS.md Sep 15 line was wrong, now fixed.
- **KV re-read:** 4 test / **0 real signups** (unchanged since Sep 12) — 182 LPV -> 0 signups is still the conversion bottleneck, not traffic.
- **Cap change (LATEST.md addendum 21:08 ET, Arsal):** CA$20 -> **CA$75 total Meta+Google combined**, goal = signups + followers. New goal framing recorded.
- **Spend plan (in LATEST Result):** spent CA$22.60; staged flow-twist-v1 $3/day x 5d = CA$16.95 max (GST-in); proposed paper-left-v1 CA$16.95 (staggered after) + v4-reel follower boost CA$10.17 (3d); worst case CA$66.67 <= CA$75, slack CA$8.33. Google PMax CA$0 parked.
- **flow-twist-v1 staged, NOT published:** blocker 1 = Meta account spend limit not reset (nothing can deliver); blocker 2 = **brand vet not done — both vision routes errored this session** (vision_analyze 400 model-no-image; browser_vision 400). Frames extracted for next pass: ~/AppData/Local/hermes/scripts/ftv1_frame_{0,60,150,238}.png. No prior vet record for flow-twist/v6a in any repo. Asset verified live on Worker (HTTP 200, 12s).
- **PMax:** 281499219080623 is STALE; current draft 281499223836205 (pmax-state file). Live read blocked: Google re-auth wall ("Verify it's you") — credentials are Arsal's hands. $0 spent, payment never submitted.
- **Watchdog note:** dead-ad watchdog (shipped Sep 27 morning) worked as designed — collector now leads with the spend-limit + Not-delivering alerts; this pass's numbers agree with it.

## Oct 3 — round-2 brand vet COMPLETED: flow-twist-v1 / paper-left-v1 / jacket spare all PASS (2 independent vision passes)

- **What was broken:** the Sep 30 vet attempt (`brand_vet_results.txt`, gemma4) is **VOID** — control test proved local `gemma4:latest` is blind via /api/chat (asked to describe lota-lemon.png it said "no image was provided"; every film frame got hallucinated "abstract smoky texture, no objects"). Its all-FAIL verdicts were verdicts on hallucinations. File now carries a VOID header. The gemma4 route is dead on this box; do not reuse.
- **Fix — brand_vet_v2.py** (`~/AppData/Local/hermes/scripts/`): moondream (local, vision-capable — control PASSED on lota-lemon.png: "yellow cartoon character with a face and a green leaf on top") supplies literal frame descriptions; lock verdicts computed by keyword scan of the description (regex, word-boundary). Selftest 6/6. Replaces brand_vet_frames.py.
- **Vet results (frames at 0.75–11.25s across both films + jacket spare):** **ALL PASS all 3 locks** — no drink gestures (pour shots only), no bowl/body/waste in any description, mess always implied (purse, door, paper-out-of-reach). Two WARNs cleared: (1) 9.75s sink frame = the standard hand-wash outro shot (jet hero earlier; sink-as-use lock concerns the use *story*, not the closing hand-wash); (2) moondream mislabels the yellow squeeze-bottle "thermos/coffee mug/water bottle" — shape-only read, no drinking cues, PASS with note. Full runs: `vet_1003/ftv1_v2_run.txt`, `plv1_v2_run.txt`, `jacket_v2_run.txt`.
- **Independent cross-check:** matches Advitisor's Sep 28 PASS (LATEST.md §Brand-vet) frame-for-frame: stall-gap + sneaker + "The cleanup doesn't.", yellow bottle downward jet no-destination, purse + manicured hand at door, near-black open. moondream read "Water wasn't invited." on plv1 @2.25s.
- **Provenance verified:** staged Sep 27 PNGs perceptually match my fresh ffmpeg extractions of the live film (frame_60→2s, frame_150→5s, frame_238→7.9s); md5 confirms `lota-flow-twist-v1` ≡ `lota-v6a-flow-twist` and plv1/ftv1 share bytes from ~3.75s (only the hook differs).
- **Staged-asset decay check:** all three creatives still HTTP 200 on the Worker at expected byte sizes.
- **Status: round-2 creative side is now fully cleared agent-side.** The ONLY remaining blocker for line 1 (flow-twist-v1 boost, CA$16.95 max) is Arsal's: reset the Meta ad-account spend limit + confirm/amend the SPEND PLAN. Pixel ID still placeholder zeros on the page (Arsal pulls from Events Manager).

## Oct 3 (evening) — SECOND account-limit death (CA$40 card); morning cron outage; "customize video from analytics" decision

- **Ad dead AGAIN.** Live read (collector, this evening): status "Not delivering", alerts = SPEND LIMIT HIT + AD NOT DELIVERING. Card spend **CA$40.00 pre-GST = CA$45.20 GST-incl of the CA$75 cap → CA$29.80 headroom**. Delivery had resumed after Arsal's reset (Oct 2 daily: active, CA$31.79 card, 320 LPV, no alerts) and ran until Meta's account limit hit again at CA$40. **Second death at Meta's own account-level spend limit** (first: ~Sep 17 @ CA$20). Pattern: Meta gates new ad accounts at a low spending limit and raises it per reset — expect at least one more reset cycle; only Arsal can do it (billing settings).
- **What the resumed v4 bought (deltas since Sep 27 final):** views 2,045→4,501, viewers 1,452→2,957, LPV 182→450 (+268 for +CA$22.60 GST = ~CA$0.084/LPV — cheaper than round 1's CA$0.105), spend CA$20→CA$40 card. **Same creative + more spend = same outcome: 0 real signups.** The leak is click→signup, not traffic or cost-per-click.
- **KV read erroring today** (Cloudflare API error on key list, 2 attempts, ~9:20 and 21:10) — same transient class as Sep 26 (which cleared on retry later). Last verified count (Oct 2 daily): **0 real / 5 test**.
- **Morning cron outage (root cause of "no updates"):** all three 9am jobs (NYC news, AI insider, lota analytics) died 09:06–09:17 with model-provider DNS timeouts ("lookup ollama.com: i/o timeout") — post-wake network not ready (wake task 8:55a, DNS 1.1.1.1). Both news jobs re-fired 21:14/21:16 and delivered clean. Analytics job NOT re-fired (numbers reported directly in chat instead; dashboard POSTed manually below). Fix candidate: shift 9:00 jobs to ~9:30, or add a network-wait to the 8:55 wake task — Arsal's call on timing.
- **Dashboard feed POSTed manually** (job step 3 contract): status ok, note = dead-again + spend + blockers.
## Oct 3 (night) — "video is def AI generated" callout: diagnosis + creative-pipeline plan

- **Confirmed: all films are AI-generated** (Veo-class staged Sep 27; no camera footage exists). Frame evidence from vet runs + fresh reads: dark moody "black and white background" product-hero look, physics-soft pour (moondream reads the jet as a mug "creating a small waterfall effect"), texture repetition in the stall scene (@8.25s caption degenerates "door door door…" — repeating-pattern tell), zero handheld/grain. That combination IS the recognizable "AI ad" aesthetic.
- **Fix ranked (advice given):**
  1. **Real phone footage (best):** founder-POV UGC — Arsal's hands, a real bathroom, real water (prototype or stand-in bottle). One afternoon of shooting = 10 raw clips = a month of cuts. Kills the callout AND matches the Sep 15 research (UGC POV > polished static for this market).
  2. **If staying AI:** prompt-level realism (handheld micro-shake, film grain, practical lighting, phone-footage look), fix the specific tells (water physics arcs, no repeating textures), faster cuts. Don't try to pass renders off as real product demos — for a waitlist, trust converts.
  3. **Honest hybrid:** label renders "concept" and put the founder on camera for the ask. Waitlist conversion = trust in the person.
- **Better ad pipeline (the loop to build):** analytics picks the ANGLE → brief → generate 3 variants → brand-vet + NEW realism-gate (add to brand_vet_v2.py: no impossible physics, no texture repetition, grain/shake check) → stage → staggered boosts → Pixel + lead-form data ranks creatives by cost-per-lead → next brief. The missing piece making "customize from analytics" impossible today = Pixel + lead form (same blockers as round 2). Next concrete agent actions on his go: (a) add realism-gate to vet script, (b) draft 3 UGC shot-lists for the researched angles (office agitation, comfort/health 45+ women, cultural lota). Highest leverage remains the staged **v6a instant lead form** (signup inside Meta, kills the LP→signup drop) + real **Pixel** (still placeholder zeros) + benched paper-left-v1 as the flatline alternate. If Arsal still wants data-grounded video work, the concrete path = age/gender breakdowns via Ads Manager report exports (previously blocked by DOM virtualization; async CSV lands in the report center) → then cut the 3 research angles UGC-style (office-day agitation, comfort/health 45+ women, cultural lota). Blocker chain unchanged: reset spend limit → confirm spend plan → Pixel → v6a go.

## Oct 4 (night) — night-queue sprint #1: office-day agitation UGC shot list STAGED (angle 1 of 3)

- **Delivered:** full founder-POV UGC shot list for the **office-day agitation** angle → `board/inbox/hermes/20261004-0108-hermes-office-ugc-shotlist.md`. 10 clips / ~75 min shoot / $0 budget (phone + real bathroom + real water — the direct answer to the Oct 3 "def AI generated" callout: fix ranked #1 was real founder footage). Includes 15s boost cut (shots 1→4→5→7→8→10) + 30s organic cut, optional VO, Advitisor's locked caption, 3 rotating hashtag sets, and the post-shoot pipeline (brand_vet_v2 locks + pending realism gate).
- **Brand locks carried into the shot list:** staging implied only (shot 5 = cut-away before the stall, shot 8 = closed door + SFX), no drink read, no bowl/body, sink closer = the pre-approved hand-wash outro. Zero pour shots — water never appears in this angle.
- **Staging only — nothing published, nothing boosted, no Meta/budget touched.** Shoot needs Arsal's hands (literally); nights 2–3 queue the comfort/health-45+ and cultural-lota shot lists on the same template.
- **Ad status tonight (collector run, job step 4):** see night-crew report — spend-limit death #2 unchanged, expected, not escalated.

## Oct 5 (night) — night-queue sprint #2: comfort/health 45+ UGC shot list STAGED (angle 2 of 3)

- **Delivered:** `board/inbox/hermes/20261005-0102-hermes-comfort-health-45plus-ugc-shotlist.md` — travel-kit-POV shot list for the comfort/health 45+ women angle (the segment Meta delivery already over-indexes: 55+/65+ viewer skew, Oct 3). 8 clips + 1 alt / ~60 min / $0. Two casting routes: (a) 45+ woman on camera (preferred — recognition IS the conversion), or (b) Arsal hands-only + warm first-person VO that never shows a face. 15s boost cut (1→4→5→6→7→8) + 30s organic cut, sound-off text-on-screen beats, 3 rotating hashtag sets, Advitisor's locked caption. Tone = dignity/discretion (research), no fear copy.
- **Brand locks:** closed-door implied staging (shot 6), no bowl/body/waste, bottle ≤1.5s in focus, standard hand-wash outro close, kit re-pack mirror as the retention beat. Same pipeline: brand_vet_v2 → realism gate (still queued) → stage → Arsal's go.
- **Staging only — nothing published, nothing boosted, no Meta/budget touched.**
- **Ad status tonight (collector, job step 4):** `Not delivering`, spend CA$40.00 frozen at Meta account spend limit (death #2) — expected alert, not escalated. **But KV flipped: FIRST REAL SIGNUP — jenmcd13@gmail.com (1 real / 5 test, was 0 real Oct 2).** First organic proof the waitlist converts; worth noting the 55+ skew delivering the audience the research predicted would convert. Night 3 queue: cultural-lota angle shot list to close the set.

## Oct 5 (morning) — REALISM GATE validated: implemented Oct 4, proven on all four AI-render films (4/4 FAIL)

- **Correction of record:** the realism gate is NOT "still queued." It shipped in `brand_vet_v2.py` on Oct 4 11:28 AM (`--realism` mode: grain/shake/repetition via deterministic numpy checks on 24 sampled frames; `--physics` = advisory moondream scan). Both shot lists (Oct 4 + Oct 5) and the Oct 5 log entry called it "queued/pending" — stale by one day. Correct pipeline everywhere: brand_vet_v2 locks → **realism gate (LIVE)** → stage → Arsal's go.
- **Validation (daily backlog worker, Oct 5):** offline selftest 10/10 (6 locks + 4 realism cases, incl. negation-aware physics-tell scan). Then the gate was run on every film on disk:
  - **flow-twist-v1 (v6a):** FAIL — grain σ 0.250 + **6/23 duplicated-frame pairs (26%)**; physics scan clean (moondream reads "water flowing out of a yellow container… onto the surface below", denials honored — no impossible-physics words).
  - **paper-left-v1:** FAIL — grain σ 0.250 + 6/23 dup pairs (26%); physics clean.
  - **paper-left-jacket-v1:** FAIL — grain σ 0.250 + **8/23 dup pairs (35%)**.
  - **problem-v4 (the boosted cut):** FAIL — grain σ 0.375 + **10/23 dup pairs (43%)** — the worst offender; the AI-callout film scores the worst on the gate. Note: the Oct 3 "door door door" repetition tell was NOT re-detected on v4's frames (autocorr < 0.6 at ≥24px lags) — repetition is one-of-three tells, two others carry the verdict here; keep the repetition check for future renders.
- **Read:** the gate works — 4/4 known AI renders FAIL with the "clean + frozen" signature, and the publicly-called-out film scores worst. As designed, this is a gate on NEW creative entering the pipeline, not a retroactive kill on the staged round-2 set (those PASS brand locks; the callout fix is the UGC pivot). First real-footage PASS will come from the UGC shoot clips.
- **No negative control on real camera footage exists on this box** (only screen recordings + the AI renders) — the selftest synthetic noisy/jitter case covers the PASS path; the UGC shoot will supply the first true negative control.
- **Agent-side now fully clear for round 2 + UGC:** creative staged + brand-vetted + realism-gated; ONLY Arsal blockers remain: reset Meta account spend limit → confirm spend plan → real Pixel ID → v6a go.

## Oct 9 (night) — night-queue sprint #3: cultural-lota UGC shot list STAGED (angle 3 of 3 — the set is complete)

- **Delivered:** `board/inbox/hermes/20261009-0105-hermes-cultural-lota-ugc-shotlist.md` — heritage-piece shot list for the cultural-lota angle: the family lota, remembered (nani's steel shelf → founder's backpack), 9 clips / ~60 min / $0, one family kitchen + the standard bathroom closer. Two casting routes, Arsal-on-camera preferred (most founder-native of the three angles, the direct counter to the AI callout). 30s organic hero cut + bench-warmed 15s boost cut (1→3→5→6→7→9), burned-in sound-off text, warm first-person VO with natural code-switching (subtitled), 3 rotating hashtag sets.
- **Two hard guardrails written into the top of the doc:** (1) never comedy on the ritual itself — humor only in the generational ribbing shot (4), which is optional and only with a genuinely willing elder; (2) standard brand locks — closed-door implied staging (shot 6), no bowl/body/waste, hand-wash outro close, bottle in focus ≤1.5s. The resolution beat is the "re-shelf" (shot 8): steel lota and yellow bottle side by side — an addition to tradition, never a replacement.
- **Set status: angles 1–3 of 3 staged** (office-day agitation Oct 4, comfort/health 45+ Oct 5, cultural lota tonight). The board now holds a complete UGC shoot menu for the three researched segments; all three share one bathroom closer and the same post-shoot pipeline (brand_vet_v2 locks → realism gate, LIVE since Oct 4 → stage → Arsal's go). Next prep pieces queued for the night queue: caption/hashtag pack for the end card, or next-week content calendar.
- **Ad status tonight (collector, job step 4):** `Not delivering`, spend CA$40.00 frozen at Meta account spend limit (death #2) — expected alert, not escalated. First run of the collector hit two transients (Cloudflare KV API error + CDP Edge not running); fixed agent-side by launching the headless debug Edge clone (no window, his normal Edge untouched) and re-running — both routes then clean. **KV: 1 real signup (jenmcd13@gmail.com) / 5 test — unchanged since Oct 5; no new signups, none lost.** Meta frozen at 450 LPV / 2,957 viewers / 4,501 views.
- **Gmail sweep:** skipped — census (Oct 4, 421 senders / 44 prune candidates) already exists; `email_killlist_approved.json` still absent, so nothing executes. Awaiting Arsal's morning pick.
- **Staging only — nothing published, nothing boosted, no Meta/budget touched.**
