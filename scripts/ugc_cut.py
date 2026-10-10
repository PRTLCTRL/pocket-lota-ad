# -*- coding: utf-8 -*-
"""
ugc_cut.py - Pocket Lota UGC assembly line.

Turns one afternoon of raw phone clips into finished Pocket Lota shorts,
implementing the three staged UGC shot lists (Oct 4/5/9) verbatim:
  angle "office"   : board/inbox/hermes/20261004-0108-hermes-office-ugc-shotlist.md
  angle "comfort"  : board/inbox/hermes/20261005-0102-hermes-comfort-health-45plus-ugc-shotlist.md
  angle "cultural" : board/inbox/hermes/20261009-0105-hermes-cultural-lota-ugc-shotlist.md

Per cut: 30s organic (YouTube hero) + 15s mirror (FB reel), both with
burned-in sound-off text beats + the unified generated end card, then the
standing pipeline: brand_vet_v2.py locks -> realism gate -> stage -> Arsal's go.

End card CTA mirrors Advitisor's locked caption ("First batch is free - just
leave your email."). Price is deliberately NOT on the card (waitlist-only
destination; the $19.99 lines in the angle-1/2 lists predate that lock).

Usage:
  python ugc_cut.py <angle> --raw <clips_dir> [--manifest manifest.json]
                    [--out shorts] [--label v1] [--dry-run] [--bts]
  python ugc_cut.py endcard --png out.png          # regenerate just the card art
  python ugc_cut.py demo --raw tmpdir              # synthetic self-test clips + run

Raw clips: name files shot1.mp4 .. shot10.mp4 (shot-1/shot_1 also OK, any
video ext). Or pass --manifest {"shots":{"1":{"file":"IMG_0001.MOV","in":2.5},
"2":{...}},"bts":[{"file":"...","in":0,"out":4,"text":"optional"}]} for phone
names / in-points. Missing OPTIONAL shots are skipped with a warning; missing
required shots abort that cut (never silently re-order the locked film).
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    sys.exit("PIL (pillow) required: pip install pillow")

W, H = 1080, 1920
FPS = 30
FONT_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
FONT_BLACK = r"C:\Windows\Fonts\ariblk.ttf"
FONT_REG = r"C:\Windows\Fonts\segoeui.ttf"
MASCOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "public", "lota-lemon.png")
CARD_DUR = 3.0
VET_PY = os.path.expanduser(
    "~/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe")
VET = os.path.expanduser("~/AppData/Local/hermes/scripts/brand_vet_v2.py")
VET_HINT = (
    "Next pipeline steps (staging only - NOTHING publishes without Arsal's go):\n"
    '  "%s" "%s" <film.mp4> 0.75,3,6,9,11.25   # brand locks\n'
    '  "%s" "%s" --realism <film.mp4>          # realism gate\n'
    "Real phone footage should PASS the realism gate (natural grain/shake).\n"
    "Synthetic/AI renders FAIL by design - never publish a FAIL."
) % (VET_PY, VET, VET_PY, VET)


class Shot(object):
    def __init__(self, dur, text=None, ramp=False, optional=False, subtitle=False):
        self.dur = float(dur)          # guide duration from the shot list
        self.text = text                # burned-in sound-off beat (verbatim)
        self.ramp = ramp                # half-speed ramp (60fps capture note)
        self.optional = optional       # cut works without it per the list
        self.subtitle = subtitle        # it's a subtitle of spoken audio


ENDCARD = Shot(CARD_DUR)

ANGLES = {
    # Angle 1 - office-day agitation (10 clips). Text beats = the list's own
    # VO lines, verbatim ("Nobody plans their day around a bathroom." /
    # "Paper was never the plan.") - zero new copy.
    "office": {
        "shots": {
            1: Shot(5, "Nobody plans their day around a bathroom."),
            2: Shot(3),
            3: Shot(3, optional=True),
            4: Shot(4),
            5: Shot(3),
            6: Shot(4),
            7: Shot(4, "Paper was never the plan.", ramp=True),
            8: Shot(5),
            9: Shot(4),
            10: Shot(5),
        },
        "organic": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, "card"],
        "boost15": [1, 4, 5, 7, 8, 10, "card"],
    },
    # Angle 2 - comfort/health 45+ (9 clips; 6b alt replaces 6 when present).
    "comfort": {
        "shots": {
            1: Shot(4.5, "Packing for another work trip."),
            2: Shot(3),
            3: Shot(3.5, "The part nobody talks about.", optional=True),
            4: Shot(4, "Hotel bathroom, night 2."),
            5: Shot(3, ramp=True),   # "let the bottle breathe" - no text per list
            6: Shot(4, "The one thing I never leave behind."),
            "6b": Shot(5, "Every kit I pack has one of these now. Don't travel without it.", subtitle=True),
            7: Shot(4),
            8: Shot(4, "Pocket Lota - the first batch is free."),
        },
        "organic": [1, 2, 3, 4, 5, 6, 7, 8, "card"],
        "boost15": [1, 4, 5, 6, 7, 8, "card"],
    },
    # Angle 3 - cultural lota (9 clips; shot 9 IS the end card).
    "cultural": {
        "shots": {
            1: Shot(4.5, "Every desi house has one."),
            2: Shot(5, "Every desi household has one. My nani's was steel. Mine fits in my backpack.", subtitle=True),
            3: Shot(4, "Nani's. And mine."),
            4: Shot(4.5, '"What\'s wrong with the regular one?"', optional=True, subtitle=True),
            5: Shot(3, "The pocket part."),
            6: Shot(4, "Some things don't change."),
            7: Shot(4),
            8: Shot(4, "Now there's room for both."),
            9: ENDCARD,
        },
        "organic": [1, 2, 3, 4, 5, 6, 7, 8, 9],
        "boost15": [1, 3, 5, 6, 7, 9],
    },
}

CUT_TARGETS = {"organic": 30.0, "boost15": 15.0}


# --------------------------------------------------------------------- art --
def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _wrap(draw, text, font, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def make_endcard_png(path):
    """Unified end card (1080x1920): cream bg, lemon mascot, wordmark,
    tagline, locked-caption CTA, waitlist URL. No price (waitlist lock)."""
    img = Image.new("RGB", (W, H), (255, 247, 233))
    d = ImageDraw.Draw(img)
    if os.path.exists(MASCOT):
        m = Image.open(MASCOT).convert("RGBA")
        m.thumbnail((520, 520), Image.LANCZOS)
        img.paste(m, ((W - m.width) // 2, 420 - m.height // 2), m)
    else:
        print("WARN: mascot %s missing - card goes text-only" % MASCOT)
    ink = (35, 35, 35)
    warm = (140, 106, 20)
    for txt, font, y, col in (
        ("Pocket Lota", _font(FONT_BLACK, 118), 760, ink),
        ("the lota, pocket-sized.", _font(FONT_BOLD, 58), 930, warm),
        ("First batch is free -", _font(FONT_BOLD, 52), 1120, ink),
        ("just leave your email.", _font(FONT_BOLD, 52), 1186, ink),
        ("pocket-lota-ad.prtl.workers.dev", _font(FONT_REG, 40), 1330, (90, 90, 90)),
    ):
        bb = d.textbbox((0, 0), txt, font=font)
        d.text(((W - bb[2]) // 2, y), txt, font=font, fill=col)
    d.rounded_rectangle([80, 1420, W - 80, 1428], 4, fill=warm)
    img.save(path)
    return path


def make_text_png(text, path):
    """Full-frame transparent overlay: white text, rounded dark scrim,
    lower third - readable sound-off, never covering the action."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = _font(FONT_BOLD, 62)
    lines = _wrap(d, text, font, W - 260)
    lh = 84
    block_h = len(lines) * lh
    pad_x, pad_y = 46, 30
    y0 = 1390 - block_h - pad_y          # text block bottom ~72% height
    wmax = max(d.textbbox((0, 0), ln, font=font)[2] for ln in lines)
    d.rounded_rectangle([W // 2 - wmax // 2 - pad_x, y0,
                         W // 2 + wmax // 2 + pad_x, y0 + block_h + 2 * pad_y],
                        26, fill=(0, 0, 0, 118))
    for i, ln in enumerate(lines):
        bb = d.textbbox((0, 0), ln, font=font)
        d.text(((W - bb[2]) // 2, y0 + pad_y + i * lh), ln, font=font,
               fill=(255, 255, 255, 255))
    img.save(path)
    return path


# ------------------------------------------------------------------ ffmpeg --
def ffprobe(path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "a:0",
           "-show_entries", "stream=codec_type", "-of", "csv=p=0", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return "audio" in (r.stdout or "")


def clip_duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", path],
                       capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def build_shot(src, out, dur, text_png=None, in_pt=0.0):
    """trim -> (ramp) -> 9:16 scale/crop -> fps30 -> contrast-only grade
    -> text overlay (alpha fades) -> uniform intermediate."""
    ramp = src.endswith("::RAMP")
    if ramp:
        src = src[:-len("::RAMP")]
    use = dur / 2.0 if ramp else dur
    vf = ("trim=start=%s:duration=%s,setpts=PTS-STARTPTS" % (in_pt, use))
    if ramp:
        vf += ",setpts=2*PTS"
    vf += (",scale=%d:%d:force_original_aspect_ratio=increase,"
           "crop=%d:%d,setsar=1,fps=%d,eq=contrast=1.05" % (W, H, W, H, FPS))
    has_audio = ffprobe(src)
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src]
    idx_png = idx_sil = None
    n = 1
    if text_png:
        cmd += ["-loop", "1", "-t", str(dur), "-i", text_png]
        idx_png = 1
        n = 2
    if not has_audio:
        cmd += ["-f", "lavfi", "-t", str(dur), "-i",
                "anullsrc=r=44100:cl=stereo"]
        idx_sil = n
    fc = ["[0:v]%s[v0]" % vf]
    if has_audio:
        af = "atrim=start=%s:duration=%s,asetpts=PTS-STARTPTS" % (in_pt, use)
        if ramp:
            af += ",atempo=0.5"
        fc.append("[0:a]%s[a0]" % af)
        amap = "[a0]"
    else:
        amap = "[%d:a]" % idx_sil
    if text_png:
        fade_out = max(0.0, dur - 0.35)
        fc.append("[%d:v]format=rgba,fade=t=in:st=0:d=0.25:alpha=1,"
                  "fade=t=out:st=%s:d=0.30:alpha=1[t0]" % (idx_png, fade_out))
        fc.append("[v0][t0]overlay=0:0[v]")
        vmap = "[v]"
    else:
        vmap = "[v0]"
    cmd += ["-filter_complex", ";".join(fc), "-map", vmap, "-map", amap,
            "-t", str(dur), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k",
            "-ar", "44100", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    return out


def build_card(card_png, out, dur=CARD_DUR):
    cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-t", str(dur),
           "-i", card_png, "-f", "lavfi", "-t", str(dur), "-i",
           "anullsrc=r=44100:cl=stereo", "-filter_complex",
           "[0:v]scale=%d:%d,setsar=1,fps=%d,fade=t=in:st=0:d=0.3[v]" % (W, H, FPS),
           "-map", "[v]", "-map", "1:a", "-t", str(dur),
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k",
           "-ar", "44100", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    return out


def concat(parts, out):
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        lst = f.name
        for p in parts:
            f.write("file '%s'\n" % p.replace("\\", "/").replace("'", "'\\''"))
    try:
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat",
                        "-safe", "0", "-i", lst, "-c:v", "libx264",
                        "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
                        "-movflags", "+faststart", out], check=True)
    finally:
        os.unlink(lst)
    return out


# ------------------------------------------------------------------- plans --
def find_clips(raw_dir, manifest):
    """Return {shot_key: (path, in_pt)} - manifest wins, else shotN.* match."""
    files = {}
    if manifest and "shots" in manifest:
        for k, v in manifest["shots"].items():
            p = os.path.join(raw_dir, v["file"])
            if not os.path.exists(p):
                sys.exit("manifest clip missing: %s" % p)
            files[k if k in ("6b",) else int(k)] = (p, float(v.get("in", 0)))
    if files:
        return files
    rx = re.compile(r"^shot[-_]?(\d{1,2})\.(mp4|mov|mkv|m4v|avi|webm)$", re.I)
    for fn in os.listdir(raw_dir):
        m = rx.match(fn)
        if m:
            files[int(m.group(1))] = (os.path.join(raw_dir, fn), 0.0)
    return files


def resolve_order(angle, order, clips):
    """Handle comfort 6b alt (replaces 6 when present) + drop optional misses."""
    resolved, dropped = [], []
    for s in order:
        if s == "card" or s == 9 and angle == "cultural":
            resolved.append("card")
            continue
        if s == 6 and "6b" in clips and "6b" in ANGLES[angle]["shots"]:
            resolved.append("6b")
            continue
        if s in clips:
            resolved.append(s)
        elif getattr(ANGLES[angle]["shots"][s], "optional", False):
            dropped.append(s)
        else:
            sys.exit("ABORT: required shot %r for angle %r not in clips dir "
                     "(shot file or --manifest entry missing). The locked "
                     "cut is never silently re-ordered." % (s, angle))
    return resolved, dropped


def build_plan(angle, cut, clips):
    """Beat sheet with guide durations scaled to hit the nominal cut length."""
    resolved, dropped = resolve_order(angle, ANGLES[angle][cut], clips)
    guides = [(s, CARD_DUR) if s == "card"
              else (s, ANGLES[angle]["shots"][s].dur) for s in resolved]
    total = sum(d for _, d in guides)
    target = CUT_TARGETS[cut]
    scale = 1.0 if total <= 0 else min(1.15, target / total)
    plan, t = [], 0.0
    for s, d in guides:
        dur = CARD_DUR if s == "card" else max(1.2, round(d * scale, 2))
        plan.append((s, dur))
        t += dur
    return plan, dropped, scale


def run_angle(angle, clips, out_dir, label, dry=False, tmp=None):
    results = {}
    card_png = make_endcard_png(os.path.join(tmp, "endcard.png"))
    for cut in ("organic", "boost15"):
        plan, dropped, scale = build_plan(angle, cut, clips)
        name = "ugc-%s-%s-%s-1080x1920.mp4" % (angle, label, cut)
        out = os.path.join(out_dir, name)
        print("\n== %s %s (guide scale %.2f; dropped optional: %s) ==" %
              (angle, cut, scale, dropped or "none"))
        for s, d in plan:
            tag = "END CARD" if s == "card" else "shot %s" % s
            sh = ANGLES[angle]["shots"].get(s, ENDCARD) if s != "card" else ENDCARD
            extra = []
            if getattr(sh, "text", None):
                extra.append('text "%s"' % sh.text)
            if getattr(sh, "ramp", False):
                extra.append("half-speed ramp")
            print("  %-9s %5.2fs  %s" % (tag, d, "; ".join(extra)))
        if dry:
            results[name] = None
            continue
        parts = []
        for i, (s, d) in enumerate(plan):
            piece = os.path.join(tmp, "%s_%s_%02d.mp4" % (angle, cut, i))
            if s == "card":
                build_card(card_png, piece)
                parts.append(piece)
                continue
            sh = ANGLES[angle]["shots"][s]
            src, in_pt = clips[s]
            avail = clip_duration(src) - in_pt
            if avail + 0.01 < (d / 2 if sh.ramp else d):
                sys.exit("clip %s too short for %.2fs beat (ramp=%s)" %
                         (src, d, sh.ramp))
            tpng = make_text_png(sh.text, os.path.join(tmp, "t_%s_%d.png" % (angle, i))) \
                if getattr(sh, "text", None) else None
            tag = src + ("::RAMP" if sh.ramp else "")
            parts.append(build_shot(tag, piece, d, tpng, in_pt))
        concat(parts, out)
        got = clip_duration(out)
        results[name] = (out, got)
        print("  -> %s (%.1fs)" % (out, got))
    return results


def run_bts(clips_manifest, raw_dir, out_dir, label, dry=False, tmp=None):
    entries = (clips_manifest or {}).get("bts") or []
    if not entries:
        print("bts: no 'bts' entries in manifest - nothing to build")
        return {}
    parts = []
    for i, e in enumerate(entries):
        src = os.path.join(raw_dir, e["file"])
        if not os.path.exists(src):
            sys.exit("bts clip missing: %s" % src)
        d = float(e.get("out", 0)) - float(e.get("in", 0))
        if d <= 0:
            d = min(3.0, clip_duration(src))
        piece = os.path.join(tmp, "bts_%02d.mp4" % i)
        tpng = make_text_png(e["text"], os.path.join(tmp, "bts_t_%02d.png" % i)) \
            if e.get("text") else None
        parts.append(build_shot(src, piece, d, tpng, float(e.get("in", 0))))
    out = os.path.join(out_dir, "ugc-bts-%s-1080x1920.mp4" % label)
    concat(parts, out)
    print("BTS -> %s (%.1fs)" % (out, clip_duration(out)))
    return {os.path.basename(out): (out, clip_duration(out))}


def demo(dirpath):
    """Synthetic self-test: fake phone clips -> full build -> verify."""
    os.makedirs(dirpath, exist_ok=True)
    for i in range(1, 11):
        p = os.path.join(dirpath, "shot%02d.mp4" % i)
        if not os.path.exists(p):
            subprocess.run(["ffmpeg", "-y", "-v", "error",
                           "-f", "lavfi", "-t", "6",
                           "-i", "testsrc2=size=1080x1920:rate=30",
                           "-f", "lavfi", "-t", "6",
                           "-i", "sine=frequency=%d:sample_rate=44100" % (200 + i),
                           "-t", "6", "-c:v", "libx264", "-preset", "veryfast",
                           "-pix_fmt", "yuv420p", "-c:a", "aac", p], check=True)
    ok = True
    for angle in ("cultural", "office", "comfort"):
        clips = find_clips(dirpath, None)
        with tempfile.TemporaryDirectory() as td:
            res = run_angle(angle, clips, dirpath, "demo", tmp=td)
            for name, v in res.items():
                if not v:
                    ok = False
                    continue
                out, dur = v
                want = CUT_TARGETS["organic" if "organic" in name else "boost15"]
                if abs(dur - want) > 3.5:
                    print("FAIL: %s duration %.1fs vs nominal %.0fs" % (name, dur, want))
                    ok = False
    print("\ndemo: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Pocket Lota UGC assembly line")
    ap.add_argument("angle", choices=sorted(ANGLES) + ["endcard", "demo"])
    ap.add_argument("--raw", help="directory of raw clips")
    ap.add_argument("--manifest", help="JSON: shots {key:{file,in}}, bts [...]")
    ap.add_argument("--out", default=None, help="output dir (default shorts/)")
    ap.add_argument("--label", default="v1")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--bts", action="store_true", help="build bloopers cut too")
    ap.add_argument("--png", default=None, help="endcard mode: output PNG path")
    a = ap.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if a.angle == "endcard":
        p = a.png or os.path.join(root, "public", "ugc-endcard.png")
        make_endcard_png(p)
        print("end card -> %s" % p)
        return 0
    if a.angle == "demo":
        return demo(a.raw or os.path.join(tempfile.gettempdir(), "ugc_demo_raw"))

    if not a.raw or not os.path.isdir(a.raw):
        sys.exit("give --raw <clips_dir>")
    manifest = json.load(open(a.manifest)) if a.manifest else None
    clips = find_clips(a.raw, manifest)
    if not clips:
        sys.exit("no clips matched in %s (name them shot1..shotN or pass --manifest)" % a.raw)
    out_dir = a.out or os.path.join(root, "shorts")
    os.makedirs(out_dir, exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        res = run_angle(a.angle, clips, out_dir, a.label, a.dry_run, tmp=td)
        if a.bts and manifest:
            res.update(run_bts(manifest, a.raw, out_dir, a.label, a.dry_run, tmp=td))
    print("\n" + VET_HINT)
    return 0


if __name__ == "__main__":
    sys.exit(main())