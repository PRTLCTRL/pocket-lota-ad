# Ads Ops Copilot — productization spec v0.1

**Written:** 2026-09-16
**Status:** DRAFT — Arsal's go needed on sequencing + pricing before any build
**Thesis:** The bet was never Lota. It's the operating system built to run Lota: creative → vet → publish → measure → recommend, run by agents on a daily loop. Lota is user #1 and the case study. This doc defines what it takes to run the same loop for a *second* brand, paid.

---

## 1. What already exists (extracted from Lota, reusable)

| Loop stage | Asset | Where |
|---|---|---|
| Creative factory | Shorts pipeline (ffmpeg + fal/Kling i2v), stills seeds | `shorts/`, makelab |
| Brand-lock vetting | Frame extraction (ffmpeg) + vision check per frame, pass/fail locks | ads desk doc §2 + workflow log §3.4 |
| Publishing | Boost route via Business Suite (CDP Edge, no-kill dual-profile); composer wizard scripts | `reel2_publish/wizard/share.py` |
| Measurement | Daily 9:15am cron: Meta metrics (CDP scrape) + waitlist signups (KV via wrangler) | `pocket_lota_analytics.py` |
| Cap discipline | Cap math: daily-only budgets, stagger rule, alert at 90% of cap | workflow log §2 |
| Reporting | iMessage digest + dashboard wayfinding tab | dashboard cron |
| Board discipline | Wayfinder map, weekday frontier routine | issue #2 |

**Key insight:** every stage is already scripted once. Productizing is mostly *de-hardcoding* and *de-Arsal-ing*, not building new features.

## 2. What is hardcoded to one brand (the gaps)

1. **Identity** — Meta session lives in his debug Edge profile; publishing from any other IP trips Meta restrictions. Client brands need their own Business Manager access, not his.
2. **State** — analytics script has his Page/ad IDs and KV namespace baked in; dashboard is single-brand.
3. **Crons** — 9:15am job is bound to this machine + my memory of Lota. Multi-brand needs a config-driven loop, not a copy per brand.
4. **Scrape fragility** — CDP Business Suite scrape breaks on FB layout changes and can't run in cloud. Product-grade version needs Graph API tokens (system-user token per client BM).
5. **Me as runtime** — the loop currently depends on this Hermes session's memory. v0.5+ should move to a stateless worker + config.

## 3. Revenue model (decided reasoning)

Three options were weighed:
- **Pure SaaS first** — rejected for now: no distribution, polish burden, revenue too far out.
- **Pure agency** — rejected as endgame: sells Arsal's hours, stops scaling.
- **Hybrid: service → product** — CHOSEN. Run 2-3 real brands on the machine at $1-2k/mo done-for-you. Every manual step becomes a scripted step. When the loop runs without Arsal in the seat, flip to SaaS with proof, case studies, and a waitlist.

Service fees fund the product build. Client ad accounts also generate cross-brand creative performance data Lota alone can't.

## 4. Version 0.1 — "one real second brand, paid"

Scope (smallest sellable thing):
- **Onboarding checklist** (per brand): brand-locks doc, Page/BM access, budget cap agreement in writing, destination URL, creative seed assets.
- **Brand config file**: `brands/<name>.yaml` — page id, ad account, cap, destination, brand locks, creative pool. Analytics + publishing scripts read it instead of constants.
- **Weekly operating cadence**: creative batch (2-3) → vet vs locks → publish → 7-day measure → recommendations memo. Client gets the memo; we keep the loop.
- **Deliverable**: weekly numbers + creative + next moves. Same shape as his 9:15am digest, client-facing tone.

Explicitly out of v0.1: OAuth onboarding, self-serve signup, billing portal, multi-tenant dashboard, TikTok/YouTube expansion.

## 5. The uncomfortable prerequisite

Nobody buys ad ops from an operator whose own account shows 0 signups. **Sequence: Lota first.**
Current state (Sep 16): CA$30 cap, spend ramping, 0 real signups, queue = CTA swap go + above-fold signup + creative rotation.
- M1: Lota waitlist ≥ 10 real signups → machine proven, screenshots + numbers = the pitch.
- M2: brand-config refactor (de-hardcode analytics + publishing).
- M3: second brand live and paid (find via JC/NYC small-biz network, Ella's circle, existing contacts).
- M4: 3 brands stable or convert to waitlisted SaaS.

## 6. Risks

- **Meta flags** — client accounts must be accessed through their own BM + system user tokens; never log into a client's Meta as him. IP-restriction lesson from Lota applies doubly.
- **CDP scrape is scaffolding** — fine for Lota + 1-2 service clients; replace with Graph API before any SaaS claim.
- **Attention split** — wekend, finza, job apps all compete. This product only works if M1 gets priority until signups move.
- **Don't fake anything** — reviews, pixels, numbers (standing rule from ads desk).

## 7. Pricing sketch (for discussion, not committed)

- Pilot brand: CA$800-1,200/mo or flat 4-week pilot ~CA$500 + ad spend on their card. Pilot price is a sales tool, not the target.
- Target DFY: CA$1,500-2,000/mo per brand.
- SaaS later: $99-199/mo self-serve tier once multi-tenant.