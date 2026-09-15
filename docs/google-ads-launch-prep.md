# Google Ads launch prep — Pocket Lota on YouTube

**Status:** WAITING ON ARSAL — billing setup on his side.
**Date prepared:** 2026-09-13
**Spend rules:** Google Ads is a NEW money surface. Cap discipline: global paid
spend stays ≤ CA$20 until Arsal explicitly raises it. Arsal sets up billing
himself; agent never touches card/credentials.

## What's ready (agent side)
- Creative: `shorts/lota-problem-v5b-1080x1920.mp4` (LIVE as organic Short) —
  v5b2 is the backup candidate. Brand-lock vetting already passed both.
- Channel: Arxa (`UCZ3fFcppk_0dgQSdOgXZIbQ`), Short published Public.
- Destination: `https://pocket-lota-ad.prtl.workers.dev` (waitlist Worker —
  the ONLY allowed destination).
- Linking: Google Ads account will need YouTube channel link (channel-level
  permission) once the ads account exists.

## Recommended campaign shape (draft — confirm with Arsal at go-time)
- Campaign type: **Video → Drive conversions / or Efficient reach** — for
  waitlist clicks use **"Video action campaign"** (skippable in-stream with
  CTA button) — best fit for a 9s vertical Short... NOTE: Video Action
  Campaigns are landscape-oriented; vertical 9:16 inventory comes via
  **Video reach / bumpers or DemandGen (shorts placements)**. Decide:
  - Option A (simple): Video action campaign, landscape cut of the 9s
    (1:1 or 16:9 letterboxed) — cheap clicks, CTA banner.
  - Option B (Shorts-native): Demand Gen campaign with the 9:16 video →
    Shorts feed placement + CTA — matches the creative natively.
  Recommend B first (creative already fits), fallback A.
- Budget: $3–5/day CAD proposed; global cap still CA$20 → at $5/day that's
  ~3 days if Meta boost also runs — may need stagger or cap raise. ASK.
- Geo: US (Jersey City / NYC bias optional start) — matches waitlist intent.
- Conversion goal: waitlist signup (no pixel yet — use link clicks as
  proxy until the Worker gets a conversion ping).

## Arsal's checklist (billing)
1. ads.google.com → new account (or he may already have one).
2. Billing: add payment method himself.
3. Link: YouTube channel Arxa → linked accounts.
4. Tell me the customer ID (XXX-XXX-XXXX) when done — do NOT share passwords.

## When he says go (agent runbook)
1. Open ads.google.com in debug Edge (port 9222) — same session discipline
   as Meta (his machine, his login; agent drives clicks after login).
2. Create campaign per confirmed shape; set daily budget; upload creative;
   destination = Worker; CTA = "Sign up" / "Learn more" (NOT "Buy").
3. Screenshot before final submit — explicit Arsal go for the money click.
4. Add Google Ads metrics block to analytics cron after launch.