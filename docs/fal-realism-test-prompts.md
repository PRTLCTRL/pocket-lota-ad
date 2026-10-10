# fal.ai realism test kit — prompts + targets for "not AI-ey" Pocket Lota shorts

**Written:** 2026-10-10 (Arsal's fal test run)
**Purpose:** test whether current video models can produce product-demo shorts that survive the realism gate — and read as real — before any of it goes near the pipeline. Test-only: nothing here publishes, nothing boosts, no Meta/budget touch. Every output still goes through vetting before staging.

---

## 1. The stack, verified (Oct 10)

- **Video:** the existing films are **Veo-class text/i2v renders via fal.ai**, staged Sep 27 (workflow-log Oct 3: "all films are AI-generated, Veo-class"). The Sep-27 night-crew flow = **stills seed → image-to-video** (spec §1: "ffmpeg + fal/Kling i2v").
- **Stills seeds:** gpt-image-1 (key in ~/.env). Flask-read retry recipe lives in meta-ads-ops: **open flared rim, NO cap, single-material matte spout, pronounced downward arc + short stream**.
- **Editing/cutting:** **ffmpeg 8.1.1** — frame-vet + realism gate in `~/AppData/Local/hermes/scripts/brand_vet_v2.py`, cut assembly in `scripts/ugc_cut.py` (30s/15s cuts, burned-in text, end card).
- **Hermes in-tool image gen: currently unavailable** (no FAL_KEY in session) — generate seed stills on fal directly with the prompts below (FLUX / gpt-image endpoints).

## 2. Why the last batch got called out (the tells to kill)

Oct 3 diagnosis, all confirmed by the gate: dark moody product-hero look · physics-soft water arc (read as "waterfall effect") · repeating textures (caption degenerated "door door door…") · **zero handheld, zero grain** — "clean + frozen" is the AI signature. Gate scores on the 4 films: grain σ 0.25–0.375 (want ≥ 1.0), 26–43% duplicated-frame pairs, steady-camera jitter 0.015px (want ≥ 0.15).

**Realism targets the gate scores (from `brand_vet_v2.py --realism`):**

| Check | PASS needs | Old films |
|---|---|---|
| Grain σ (sensor noise) | ≥ 1.0 | 0.25–0.375 |
| Duplicated-frame pairs | < 25% | 26–43% |
| Jitter residual (handheld) | ≥ 0.15 px | 0.015 |
| Repeating texture (autocorr) | peak < 0.6 | flagged |

## 3. fal model picks for these tests

- **Kling 2.5 Turbo** (`kling-video` v2.5-turbo) — best i2v motion control + supports **negative prompts** (the anti-AI lever).
- **Veo 3** — most photoreal + **native audio** (real water/bathroom SFX kills the "silent render" tell).
- **Hailuo 02** (minimax) — strong physics for the water test, cheapest.
- All: **9:16, 5s, low-medium creativity/cfg** (high creativity = morphing + weird physics).

## 4. The prompts (3 options, brand-lock safe)

**Prompt rules baked in:** "amateur smartphone video" framing, handheld micro-shake, sensor grain, practical window light, imperfect exposure, short fast cuts of motion. **Never:** slow-motion hero arcs (physics-soft + screams render), static tripod, studio dark.

### Option A — the product demo (tests the water-physics tell directly)

**Seed still (run first, FLUX or gpt-image endpoint):**

> Amateur smartphone photo, vertical 9:16, slightly off-center handheld framing: a realistic hand gripping a small matte lemon-yellow plastic squeeze bottle with a short open angled spout and no cap, held over a plain white bathroom counter in a bright ordinary bathroom, spout angled downward out of the bottom of the frame, soft daylight from a small window, warm slightly cluttered bathroom softly blurred behind, visible phone-camera sensor grain, natural imperfect exposure, realistic skin texture, slight motion blur at the fingers, candid everyday snapshot, absolutely not a studio product advertisement

**i2v motion prompt (Kling 2.5 / Veo 3, feed the seed):**

> Handheld smartphone video, slight hand tremor throughout: the fingers squeeze the yellow bottle firmly and a short tight arc of clear water shoots straight down out of the bottom of the frame, fast with tiny natural splashes and stray droplets, water catching the window light and sparkling, realistic gravity and droplet physics, no slow motion, natural handheld micro-shake, visible sensor grain, amateur candid clip

**Negative prompt (Kling/Hailuo):**

> tripod, static camera, studio lighting, dark background, cinematic, slow motion, smooth flawless water stream, CGI, 3D render, product advertisement, glossy, morphing, deformed hands, extra fingers, cap on bottle, flask, bottle tips, repetitive pattern, watermark, text

**t2v-only variant (no seed, Veo 3):** same motion text + "Close-up of a hand holding a small matte lemon-yellow squeeze bottle with an open angled spout over a white bathroom counter…" + ask for **audio**: "natural bathroom ambience, running water spray sound".

### Option B — everyday-carry context (no water at all — the safest realism test)

**t2v (Kling 2.5 / Hailuo 02):**

> Handheld amateur smartphone video, vertical 9:16, natural micro-shake: a hand pulls a small matte lemon-yellow plastic squeeze bottle with an open angled spout out of the front side pocket of a dark everyday backpack on a wooden floor, warm afternoon window light, lived-in room softly blurred behind, realistic skin texture, visible sensor grain, imperfect exposure, casual candid slice-of-life clip, no music

**Negative:** tripod, studio lighting, cinematic, slow motion, CGI, 3D render, product ad, flawless, morphing, repetitive pattern, watermark, text

### Option C — the hand-wash outro (the pre-approved sink closer, brand-vetted framing)

**t2v (any model):**

> Handheld smartphone video, slight tremor: hands lathering soap under a running bathroom tap, warm overhead light, ordinary bright bathroom, water splashing naturally with droplets, realistic skin texture and pores, visible sensor grain, casual candid framing, a small yellow bottle sits on the counter edge facing away from camera, no music, natural faucet sound

**Negative:** tripod, studio lighting, cinematic, slow motion, CGI, 3D render, flawless, morphing, watermark, text, readable label

## 5. Brand locks carried into these tests (so outputs are usable, not just pretty)

Implied-only staging — never a bowl, body, waste, or stall interior · spout points **down**, destination never shown · **no cap** on the bottle (domed cap = thermos/flask read — the #1 stills failure) · single-material matte bottle · yellow squeeze-bottle reads at a glance · sink appears **only** in the hand-wash outro · no readable label.

## 6. Scoring loop (the part that makes this a real test)

1. Drop render outputs in a folder and tell me — I run **brand_vet_v2 locks + realism gate** on each and log the scores (grain/shake/dup/texture vs the table above). 4/4 previous renders FAIL; your tests are the first shot at a synthetic PASS.
2. **Flask-read eyeball:** 30 seconds on each output — does the bottle read as bottle or thermos? (Vision on this box is unreliable; your eyeball is the brand-lock check for tests.)
3. **Honesty ladder stands:** even a gate-PASSING render doesn't get passed off as a real product demo (the Oct-3 rule). Real phone footage stays the trust path for the hero cuts; renders that pass earn b-roll/insert slots or get labeled "concept".

**Staging only — nothing publishes, nothing boosts, no Meta/budget touched.**