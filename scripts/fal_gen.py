# -*- coding: utf-8 -*-
"""
fal_gen.py - Pocket Lota fal.ai creative pipeline (agent-driven factory).

stills -> image-to-video -> download -> realism-gate scoring.
Transport: RAW fal Queue API (queue.fal.run REST) - fal_client 1.0.3's own
queue transport was returning "Path / not found" from its gateway rewrite,
so we speak the documented REST directly with the account key from .env.
Resumable: existing outputs are skipped, so re-runs never re-burn credits.
Arg-fallbacks retry ONLY on pre-acceptance 4xx rejections (free); once a job
is accepted it is never auto-resubmitted.

Env: reads FAL_API_KEY from the repo .env.
Staging/test only - nothing publishes without Arsal's go.

Usage:
  python fal_gen.py list
  python fal_gen.py run --stage stills --concepts A
  python fal_gen.py run --stage video  --concepts A,B,C
  python fal_gen.py run --stage all
  python fal_gen.py run --stage score
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS = os.path.join(ROOT, "fal-tests")
STILLS = os.path.join(TESTS, "stills")
VENV_PY = os.path.expanduser(
    "~/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe")
VET = os.path.expanduser("~/AppData/Local/hermes/scripts/brand_vet_v2.py")
QUEUE = "https://queue.fal.run/"
KEY = None

NEG = ("tripod, static camera, studio lighting, dark background, cinematic, "
       "slow motion, smooth flawless water, CGI, 3D render, product "
       "advertisement, glossy, morphing, deformed hands, extra fingers, "
       "cap on bottle, flask, repetitive pattern, watermark, text")

STILL_MODELS = [
    # current fal gallery ids (verified Oct 10); arg fallbacks are free (422)
    ("fal-ai/nano-banana-pro",
     lambda p: [{"prompt": p, "aspect_ratio": "9:16"},
                {"prompt": p, "image_size": "9:16"},
                {"prompt": p, "aspect_ratio": "portrait"},
                {"prompt": p}]),
    ("fal-ai/nano-banana-2",
     lambda p: [{"prompt": p, "aspect_ratio": "9:16"},
                {"prompt": p}]),
    ("fal-ai/flux/schnell",
     lambda p: [{"prompt": p, "image_size": "portrait_16_9"},
                {"prompt": p}]),
]

CONCEPTS = {
    "A": {
        "name": "demo-arc",
        "model": "kling-v3-pro",
        "video_models": [
            # schema verified on the /api page: prompt, start_image_url,
            # duration, negative_prompt, generate_audio, cfg_scale
            ("fal-ai/kling-video/v3/pro/image-to-video",
             lambda m, u: [{"prompt": m, "start_image_url": u, "duration": "5",
                            "negative_prompt": NEG, "generate_audio": True},
                           {"prompt": m, "start_image_url": u, "duration": "5",
                            "negative_prompt": NEG},
                           {"prompt": m, "start_image_url": u,
                            "duration": "5"}]),
        ],
        "still_prompt": (
            "Amateur smartphone photo, vertical portrait framing, slightly "
            "off-center handheld: a realistic hand gripping a small matte "
            "lemon-yellow plastic squeeze bottle with a short open angled "
            "spout and no cap, held over a plain white bathroom counter in a "
            "bright ordinary bathroom, spout angled pointing down out of the "
            "bottom of the frame, soft daylight from a small window, warm "
            "slightly cluttered bathroom softly blurred behind, visible "
            "phone-camera sensor grain, natural imperfect exposure, realistic "
            "skin texture, candid everyday snapshot, not a studio product ad"),
        "motion_prompt": (
            "Handheld smartphone video with slight hand tremor: the fingers "
            "squeeze the yellow bottle firmly and a short tight arc of clear "
            "water shoots straight down out of the bottom of the frame, fast "
            "with tiny natural splashes and stray droplets, water catching "
            "the window light, realistic gravity and droplet physics, no "
            "slow motion, visible sensor grain, amateur candid clip"),
    },
    "B": {
        "name": "edc-pocket",
        "model": "kling-25-turbo",
        "video_models": [
            ("fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
             lambda m, u: [{"prompt": m, "image_url": u, "duration": "5",
                            "negative_prompt": NEG},
                           {"prompt": m, "start_image_url": u,
                            "duration": "5", "negative_prompt": NEG},
                           {"prompt": m, "image_url": u, "duration": "5"},
                           {"prompt": m, "start_image_url": u,
                            "duration": "5"}]),
        ],
        "still_prompt": (
            "Amateur smartphone photo, vertical portrait framing: a hand "
            "pulling a small matte lemon-yellow plastic squeeze bottle with "
            "an open angled spout halfway out of the front side pocket of a "
            "dark everyday backpack resting on a wooden home floor, warm "
            "afternoon window light, lived-in room softly blurred behind, "
            "visible sensor grain, natural skin texture, casual imperfect "
            "handheld framing, slice-of-life snapshot, not a product ad"),
        "motion_prompt": (
            "Handheld smartphone video, natural micro-shake: the hand pulls "
            "the small yellow bottle fully out of the backpack side pocket, "
            "gives it a small satisfied pat, and sets it back in the pocket, "
            "warm window light, realistic fabric and plastic textures, "
            "visible sensor grain, casual candid clip, natural room "
            "ambience and fabric sounds"),
    },
    "C": {
        "name": "size-contrast",
        "model": "ltx-13b",
        "video_models": [
            ("fal-ai/ltx-video-13b-distilled/image-to-video",
             lambda m, u: [{"prompt": m, "image_url": u, "duration": 5,
                            "negative_prompt": NEG},
                           {"prompt": m, "start_image_url": u, "duration": 5,
                            "negative_prompt": NEG},
                           {"prompt": m, "image_url": u, "duration": 5},
                           {"prompt": m, "image_url": u}]),
        ],
        "still_prompt": (
            "Amateur smartphone photo, vertical portrait framing: a classic "
            "well-worn stainless steel lota watering can with a long spout "
            "sitting on a family bathroom shelf among soap and a towel, and "
            "beside it a hand holding a small matte lemon-yellow plastic "
            "squeeze bottle with an open angled spout, the size difference "
            "between the two objects clearly visible, warm home daylight, "
            "visible sensor grain, candid everyday snapshot, not a product ad"),
        "motion_prompt": (
            "Handheld smartphone video, slight tremor: the hand sets the "
            "small yellow bottle down on the shelf right next to the classic "
            "steel lota, holds a beat showing the size difference between "
            "the two, warm home light, realistic textures, visible sensor "
            "grain, casual candid clip"),
    },
    # ---- batch 2 (Oct 10, spend-capped test round, seeds reused = $0 stills)
    "A2": {
        "name": "demo-arc-k25",
        "model": "kling-25-turbo",
        "seed_from": "A",
        "video_models": [
            ("fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
             lambda m, u: [{"prompt": m, "image_url": u, "duration": "5",
                            "negative_prompt": NEG},
                           {"prompt": m, "image_url": u, "duration": "5"}]),
        ],
        "still_prompt": "",  # seed reused from A - never generated
        "motion_prompt": None,  # aliased from CONCEPTS["A"] below
    },
    "C2": {
        "name": "size-contrast-k25",
        "model": "kling-25-turbo",
        "seed_from": "C",
        "video_models": [
            ("fal-ai/kling-video/v2.5-turbo/pro/image-to-video",
             lambda m, u: [{"prompt": m, "image_url": u, "duration": "5",
                            "negative_prompt": NEG},
                           {"prompt": m, "image_url": u, "duration": "5"}]),
        ],
        "still_prompt": "",
        "motion_prompt": None,  # aliased from CONCEPTS["C"] below
    },
    "B2": {
        "name": "edc-pocket-vidu",
        "model": "vidu-q4",
        "seed_from": "B",
        "video_models": [
            # vidu q4: $0.0665/s @720p, native audio; schema per playground
            ("fal-ai/vidu/q4/image-to-video",
             lambda m, u: [{"prompt": m, "image_url": u, "duration": 5},
                           {"prompt": m, "image_url": u},
                           {"prompt": m, "start_image_url": u, "duration": 5},
                           {"prompt": m, "img_url": u, "duration": 5}]),
        ],
        "still_prompt": "",
        "motion_prompt": None,  # aliased from CONCEPTS["B"] below
    },
}

# batch-2 concepts reuse the batch-1 motion prompts verbatim
for _src, _dst in (("A", "A2"), ("C", "C2"), ("B", "B2")):
    CONCEPTS[_dst]["motion_prompt"] = CONCEPTS[_src]["motion_prompt"]


# ------------------------------------------------------------ raw transport --
def _req(method, url, body=None, timeout=180):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={"Authorization": "Key " + KEY,
                 "User-Agent": "pocket-lota-pipeline/1.0",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = ""
        try:
            detail = e.read().decode("utf-8", "replace")[:400]
        except Exception:
            pass
        raise RuntimeError("HTTP %s %s :: %s" % (e.code, url, detail))


def queue_run(model, args, timeout=900):
    """Submit to the fal queue API, poll to completion, return result."""
    sub = _req("POST", QUEUE + model, args)
    status_url = sub.get("status_url")
    response_url = sub.get("response_url")
    if not (status_url and response_url):
        raise RuntimeError("no status/response url: %s" % str(sub)[:200])
    rid = sub.get("request_id", "?")
    print("    accepted request %s" % rid, flush=True)
    t0 = time.time()
    while True:
        if time.time() - t0 > timeout:
            raise RuntimeError("queue timeout after %ds" % timeout)
        st = _req("GET", status_url)
        status = st.get("status", "?")
        if status == "COMPLETED":
            break
        if status in ("IN_QUEUE", "IN_PROGRESS"):
            pos = st.get("queue_position", "")
            print("    %s pos=%s (%.0fs)" % (status, pos, time.time() - t0),
                  flush=True)
            time.sleep(5)
            continue
        raise RuntimeError("job status %s: %s" % (status, str(st)[:200]))
    res = _req("GET", response_url)
    if isinstance(res, dict) and res.get("error"):
        raise RuntimeError("job error: %s" % str(res.get("error"))[:200])
    print("    completed in %.0fs" % (time.time() - t0), flush=True)
    return res


def _rejected(exc):
    """Pre-acceptance 4xx rejection (bad arg / unknown model) = free retry."""
    s = str(exc).lower()
    if "http 5" in s or "http 429" in s:
        return False
    if re.search(r"http 4\d\d", s):
        return True
    return any(t in s for t in ("not found", "invalid", "unrecognized",
                                "does not exist", "422"))


def download(url, path):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=300) as resp, open(path, "wb") as f:
        while True:
            chunk = resp.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    return path


def _first_image_url(result):
    if not isinstance(result, dict):
        return None
    if isinstance(result.get("images"), list) and result["images"]:
        return result["images"][0].get("url")
    if isinstance(result.get("image"), list) and result["image"]:
        return result["image"][0].get("url")
    if isinstance(result.get("image"), dict):
        return result["image"].get("url")
    return result.get("image_url")


def _first_video_url(result):
    if not isinstance(result, dict):
        return None
    v = result.get("video")
    if isinstance(v, dict) and v.get("url"):
        return v["url"]
    if isinstance(v, list) and v and v[0].get("url"):
        return v[0]["url"]
    if result.get("video_url"):
        return result["video_url"]
    vids = result.get("videos")
    if isinstance(vids, list) and vids:
        return vids[0].get("url")
    return None


# ------------------------------------------------------------------- stages --
def gen_still(cid, c):
    out = os.path.join(STILLS, "%s.png" % cid)
    if os.path.exists(out):
        print("still %s exists - skip" % cid)
        return out
    if not c.get("still_prompt"):
        print("still %s: seed_from concept, no still generation" % cid)
        return os.path.join(STILLS, "%s.png" % c.get("seed_from", cid))
    for model, argf in STILL_MODELS:
        for args in argf(c["still_prompt"]):
            try:
                print("  submit still-%s :: %s" % (cid, model), flush=True)
                r = queue_run(model, args, timeout=300)
                url = _first_image_url(r)
                if not url:
                    raise RuntimeError("no image url in result: %s"
                                       % str(r)[:200])
                download(url, out)
                record_seed_url(cid, url)
                print("  -> %s (via %s)" % (out, model), flush=True)
                return out
            except Exception as e:
                msg = str(e)[:160].replace("\n", " ")
                if _rejected(e):
                    print("    rejected (pre-acceptance, free): %s" % msg,
                          flush=True)
                    time.sleep(1)
                    continue
                print("    ERROR: %s" % msg, flush=True)
                return None
    print("  still %s: all model/arg combos rejected" % cid, flush=True)
    return None


def gen_video(cid, c):
    final = os.path.join(TESTS, "%s-%s.mp4" % (cid, c["name"]))
    if os.path.exists(final):
        print("video %s exists - skip" % cid)
        return final
    seed_id = c.get("seed_from", cid)
    still = os.path.join(STILLS, "%s.png" % seed_id)
    if c.get("t2v"):
        seed_url = None
    else:
        if not os.path.exists(still):
            print("video %s: no seed still for %s - run stills stage first"
                  % (cid, seed_id))
            return None
        seed_url = _seed_remote_url(still, seed_id)
        if not seed_url:
            print("video %s: no recorded seed URL for %s" % (cid, seed_id))
            return None
    for model, argf in c["video_models"]:
        for args in argf(c["motion_prompt"], seed_url):
            try:
                print("  submit video-%s :: %s" % (cid, model), flush=True)
                r = queue_run(model, args, timeout=900)
                vurl = _first_video_url(r)
                if not vurl:
                    raise RuntimeError("no video url: %s" % str(r)[:200])
                tmp = os.path.join(TESTS, "_tmp_%s.mp4" % cid)
                download(vurl, tmp)
                os.replace(tmp, final)
                print("  -> %s (via %s)" % (final, model), flush=True)
                return final
            except Exception as e:
                msg = str(e)[:160].replace("\n", " ")
                if _rejected(e):
                    print("    rejected (pre-acceptance, free): %s" % msg,
                          flush=True)
                    time.sleep(1)
                    continue
                print("    ERROR: %s" % msg, flush=True)
                return None
    print("  video %s: all candidates rejected" % cid, flush=True)
    return None


def _seed_remote_url(still_path, cid):
    """fal media URLs are public; reuse the still's OWN url so no upload
    round-trip is needed. Recorded next to the still at download time."""
    meta = os.path.join(STILLS, "%s.url.txt" % cid)
    if os.path.exists(meta):
        return open(meta).read().strip()
    print("  no recorded seed URL for %s - regenerating still is cheaper "
          "than guessing" % cid)
    return None


def record_seed_url(cid, url):
    with open(os.path.join(STILLS, "%s.url.txt" % cid), "w") as f:
        f.write(url)


def score(path):
    """Realism gate + deterministic yellow-bottle pixel check."""
    res = {"file": os.path.basename(path)}
    try:
        r = subprocess.run([VENV_PY, VET, "--realism", path],
                            capture_output=True, text=True, timeout=900)
        out = (r.stdout or "") + (r.stderr or "")
        m = re.search(r"REALISM VERDICT:\s*(\w+)", out)
        res["realism"] = m.group(1) if m else "ERROR"
        res["details"] = [ln.strip() for ln in out.splitlines()
                          if "FLAG" in ln or "-> ok" in ln][:6]
    except Exception as e:
        res["realism"] = "ERROR"
        res["details"] = [str(e)[:120]]
    try:
        from PIL import Image
        yellow = 0
        total = 0
        for t in ("1.0", "2.5", "4.0"):
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
                jp = f.name
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", t, "-i",
                            path, "-frames:v", "1", "-q:v", "3", jp],
                           check=True)
            img = Image.open(jp).convert("RGB").resize((270, 480))
            px = list(img.getdata())
            yellow += sum(1 for r, g, b in px
                          if r > 150 and g > 115 and b < 115 and r > b + 40)
            total += len(px)
            os.unlink(jp)
        res["yellow_pct"] = round(100.0 * yellow / total, 2)
    except Exception:
        res["yellow_pct"] = -1
    return res


def run_score():
    scores = []
    for cid, c in sorted(CONCEPTS.items()):
        p = os.path.join(TESTS, "%s-%s.mp4" % (cid, c["name"]))
        if not os.path.exists(p):
            print("%s: no output yet" % cid)
            continue
        s = score(p)
        s["concept"] = "%s-%s" % (cid, c["name"])
        scores.append(s)
        print("%s realism=%s yellow=%.2f%%" %
              (s["concept"], s["realism"], s["yellow_pct"]))
    with open(os.path.join(TESTS, "scores.json"), "w") as f:
        json.dump(scores, f, indent=2)
    print("scores -> fal-tests/scores.json")


def load_env():
    global KEY
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        with open(p) as f:
            for ln in f:
                m = re.match(r"^FAL_API_KEY\s*=\s*(\S+)", ln)
                if m:
                    KEY = m.group(1)
                    break
    if KEY:
        print("FAL key loaded from repo .env (never printed)")
        return True
    print("ERROR: FAL_API_KEY not found in repo .env")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "run"])
    ap.add_argument("--stage", default="all",
                    choices=["all", "stills", "video", "score"])
    ap.add_argument("--concepts", default="A,B,C")
    a = ap.parse_args()
    if a.cmd == "list":
        for k, c in sorted(CONCEPTS.items()):
            print("%s %s (video models: %s)" % (
                k, c["name"], [m for m, _ in c["video_models"]]))
        return 0
    if not load_env():
        return 2
    ids = [s.strip().upper() for s in a.concepts.split(",") if s.strip()]
    os.makedirs(STILLS, exist_ok=True)
    if a.stage in ("all", "stills"):
        for cid in ids:
            if cid in CONCEPTS:
                print("== still %s (%s) ==" % (cid, CONCEPTS[cid]["name"]))
                gen_still(cid, CONCEPTS[cid])
    if a.stage in ("all", "video"):
        for cid in ids:
            if cid in CONCEPTS:
                print("== video %s (%s) ==" % (cid, CONCEPTS[cid]["name"]))
                gen_video(cid, CONCEPTS[cid])
    if a.stage in ("all", "score"):
        run_score()
    return 0


if __name__ == "__main__":
    sys.exit(main())