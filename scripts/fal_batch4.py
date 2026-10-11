# -*- coding: utf-8 -*-
"""
fal_batch4.py — consistency + scale + subtitles round (Arsal's batch-4 asks).

His asks (Oct 10 review of corporate v1):
  1. PRODUCT CONSISTENCY across scenes (public comment: "AI, product doesn't
     look consistent") -> every seed now references BOTH product views
     (lota-detail.jpg + lota-pour.png) + hard "do not redesign" language;
     desk scene additionally tests Kling v3 Pro ELEMENTS (the consistency
     feature) with the product as reference element.
  2. TRUE SCALE -> the product is the size of a single AirPods Max earcup,
     smaller than her palm — written into every prompt (earlier renders
     were oversized bottles). Plus a dedicated size-proof scene.
  3. SUBTITLES burned in (sound-off first rule) over the VO lines.

Spend (single pass, arg fallbacks free): 3x nano-banana-pro/edit (~$0.2)
+ 1x Kling v3 Pro i2v (~$0.56, audio off) + 2x Kling 2.5 Turbo (~$0.35 ea)
~= $1.9. VO reused from batch 3 (ElevenLabs Rachel) - $0.
"""
import base64
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fal_gen as fg
from fal_batch3 import pad_916, data_uri  # reuse helpers

ROOT = fg.ROOT
T = os.path.join(ROOT, "fal-tests")
B = os.path.join(T, "b4")
DETAIL = os.path.join(ROOT, "lota-detail.jpg")
POUR = os.path.join(ROOT, "lota-pour.png")
VO = os.path.join(T, "b3", "vo-female-real.mp3")  # ElevenLabs Rachel, reused

EDIT_MODEL = "fal-ai/nano-banana-pro/edit"
V3PRO = "fal-ai/kling-video/v3/pro/image-to-video"
K25 = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"
NEG = fg.NEG

SCALE = ("The product is TINY - the size of a single AirPods Max earcup, "
         "clearly smaller than her palm, dwarfed by the coffee cup. ")
LOCK = ("Keep this exact product design completely unchanged and "
        "identical in every detail across the image - same sleek modern "
        "bottle, same cap, same nozzle tube, same colors, proportions and "
        "finish. Do not redesign, restyle or reinterpret any part of it. ")

SCENES = {
    "desk": {
        "model": "v3pro-elements",
        "seed_prompt": (
            LOCK + SCALE +
            "Realistic candid smartphone photo, vertical composition: a "
            "woman's hand with a neat manicure lifting the tiny product out "
            "of a structured work tote bag onto a corporate office desk "
            "next to a laptop and a coffee cup, warm late-afternoon window "
            "light, office softly blurred behind, visible sensor grain, "
            "not a product ad"),
        "motion_prompt": (
            "Handheld smartphone video, natural micro-shake: the woman's "
            "hand lifts the tiny product (#1) out of the tote bag and sets "
            "it on the desk beside the coffee cup where it looks tiny, "
            "warm window light, realistic textures, visible sensor grain, "
            "casual candid clip"),
        "motion_prompt_plain": (
            "Handheld smartphone video, natural micro-shake: the woman's "
            "hand lifts the tiny product out of the tote bag and sets it "
            "on the desk beside the coffee cup where it looks tiny, warm "
            "window light, realistic textures, visible sensor grain, "
            "casual candid clip"),
        "video": "v3pro",
    },
    "size": {
        "model": "k25",
        "seed_prompt": (
            LOCK + SCALE +
            "Realistic candid smartphone photo, vertical composition: the "
            "tiny product sitting on an office desk directly next to a "
            "large coffee cup and a sunglasses case for scale, a woman's "
            "hand entering frame about to pick it up, warm afternoon "
            "window light, visible sensor grain, not a product ad"),
        "motion_prompt": (
            "Handheld smartphone video, natural micro-shake: the woman's "
            "hand picks up the tiny product from the desk, holding it "
            "palm-open so it is clearly the size of an AirPods Max earcup "
            "next to the coffee cup, warm window light, realistic "
            "textures, visible sensor grain, casual candid clip"),
        "video": "k25",
    },
    "bag": {
        "model": "k25",
        "seed_prompt": (
            LOCK + SCALE +
            "Realistic candid smartphone photo, vertical composition: a "
            "woman's hand with a neat manicure sliding the tiny product "
            "into the small side pocket of a structured work tote bag on "
            "an office desk, zipper about to close over it, warm window "
            "light, office softly blurred, visible sensor grain, not a "
            "product ad"),
        "motion_prompt": (
            "Handheld smartphone video, natural micro-shake: the woman's "
            "hand slides the tiny product into the tote's side pocket and "
            "zips it closed, a small confident pat on the pocket, warm "
            "window light, realistic textures, visible sensor grain, "
            "casual candid clip"),
        "video": "k25",
    },
}

SUBS = [
    ("Between meetings, your break should actually feel like one.", 0.6, 4.2),
    ("Pocket Lota \u2014 sleek, sealed, and it lives in your work bag.",
     4.6, 8.8),
    ("The cleaner solution, wherever your day goes.", 9.2, 13.2),
]


def edit_seed(name, prompt, refs, out_png):
    if os.path.exists(out_png):
        print("seed %s exists - skip" % name)
        return open(out_png.replace(".png", ".url.txt")).read().strip()
    attempts = [
        {"prompt": prompt, "image_urls": refs},
        {"prompt": prompt, "image_urls": refs, "aspect_ratio": "9:16"},
        {"prompt": prompt, "image_url": refs[0]},
    ]
    for i, args in enumerate(attempts):
        try:
            print("  edit submit %s (attempt %d)" % (name, i + 1), flush=True)
            r = fg.queue_run(EDIT_MODEL, args, timeout=300)
            url = (r.get("images") or [{}])[0].get("url") or r.get("image_url")
            if not url:
                raise RuntimeError("no image url: %s" % str(r)[:200])
            fg.download(url, out_png)
            open(out_png.replace(".png", ".url.txt"), "w").write(url)
            print("  -> %s" % out_png, flush=True)
            return url
        except Exception as e:
            if fg._rejected(e):
                print("    rejected (free): %s" % str(e)[:120], flush=True)
                time.sleep(1)
                continue
            print("    ERROR: %s" % str(e)[:150], flush=True)
            return None
    return None


def i2v(name, model, argsets, out_mp4):
    if os.path.exists(out_mp4):
        print("video %s exists - skip" % name)
        return out_mp4
    for args in argsets:
        try:
            print("  i2v submit %s :: %s" % (name, model), flush=True)
            r = fg.queue_run(model, args, timeout=900)
            vurl = fg._first_video_url(r)
            if not vurl:
                raise RuntimeError("no video url: %s" % str(r)[:200])
            fg.download(vurl, out_mp4)
            print("  -> %s" % out_mp4, flush=True)
            return out_mp4
        except Exception as e:
            if fg._rejected(e):
                print("    rejected (free): %s" % str(e)[:120], flush=True)
                time.sleep(1)
                continue
            print("    ERROR: %s" % str(e)[:150], flush=True)
            return None
    return None


def sub_png(text, path):
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1080, 1920
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 56)
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textbbox((0, 0), trial, font=font)[2] <= W - 220 or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    lh = 78
    pad_x, pad_y = 42, 26
    y0 = 1560 - len(lines) * lh - pad_y
    wmax = max(d.textbbox((0, 0), ln, font=font)[2] for ln in lines)
    d.rounded_rectangle([W // 2 - wmax // 2 - pad_x, y0,
                         W // 2 + wmax // 2 + pad_x,
                         y0 + len(lines) * lh + 2 * pad_y], 24,
                        fill=(0, 0, 0, 122))
    for i, ln in enumerate(lines):
        bb = d.textbbox((0, 0), ln, font=font)
        d.text(((W - bb[2]) // 2, y0 + pad_y + i * lh), ln, font=font,
               fill=(255, 255, 255, 255))
    img.save(path)
    return path


def norm_clip(src, out, dur=5.04):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                        "-show_entries", "stream=codec_type", "-of", "csv=p=0",
                        src], capture_output=True, text=True)
    has_a = "audio" in (r.stdout or "")
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src]
    if not has_a:
        cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
    cmd += ["-filter_complex",
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,setsar=1,fps=30[v]",
            "-map", "[v]", "-map", "0:a" if has_a else "1:a",
            "-t", str(dur), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
            "-ar", "44100", "-ac", "2", out]
    subprocess.run(cmd, check=True)
    return out


def main():
    if not fg.load_env():
        return 2
    os.makedirs(B, exist_ok=True)
    # product refs as data URIs (detail + pour - the two clean design views)
    du_detail = data_uri(pad_916(DETAIL, os.path.join(B, "ref-detail.png")))
    du_pour = data_uri(POUR)
    refs = [du_detail, du_pour]
    print("product refs loaded (detail+pour, %d KB total)" %
          ((len(du_detail) + len(du_pour)) // 1024))

    # 1. seeds (all reference BOTH product views + scale anchor)
    seeds = {}
    for k, sc in SCENES.items():
        seeds[k] = edit_seed(k, sc["seed_prompt"], refs,
                             os.path.join(B, "seed-%s.png" % k))

    # 2. i2v — desk tests Kling v3 Elements first; others on K2.5
    vids = {}
    for k, sc in SCENES.items():
        u = seeds.get(k)
        if not u:
            print("scene %s: no seed - skip" % k)
            continue
        if sc["video"] == "v3pro":
            argsets = [
                {"prompt": sc["motion_prompt"], "start_image_url": u,
                 "duration": "5", "generate_audio": False,
                 "elements": [{"frontal_image_url": du_detail,
                               "reference_image_urls": [du_pour]}]},
                {"prompt": sc["motion_prompt_plain"], "start_image_url": u,
                 "duration": "5", "generate_audio": False},
                {"prompt": sc["motion_prompt_plain"], "start_image_url": u,
                 "duration": "5"},
            ]
            vids[k] = i2v(k, V3PRO, argsets, os.path.join(B, "scene-%s.mp4" % k))
        else:
            argsets = [
                {"prompt": sc["motion_prompt"], "image_url": u,
                 "duration": "5", "negative_prompt": NEG},
                {"prompt": sc["motion_prompt"], "image_url": u,
                 "duration": "5"},
            ]
            vids[k] = i2v(k, K25, argsets, os.path.join(B, "scene-%s.mp4" % k))

    # 3. mash + VO
    if not all(vids.get(k) for k in ("desk", "size", "bag")) or not os.path.exists(VO):
        print("mash skipped (missing scenes or VO)")
        return 1
    n1 = norm_clip(vids["desk"], os.path.join(B, "n1.mp4"))
    n2 = norm_clip(vids["size"], os.path.join(B, "n2.mp4"))
    n3 = norm_clip(vids["bag"], os.path.join(B, "n3.mp4"))
    d, xf = 5.04, 0.6
    fc = ("[0:v][1:v]xfade=transition=fade:duration=%s:offset=%.2f[v01];"
          "[v01][2:v]xfade=transition=smoothleft:duration=%s:offset=%.2f[v];"
          "[0:a][1:a]acrossfade=d=%s[a01];[a01][2:a]acrossfade=d=%s[amix];"
          "[3:a]adelay=600|600,volume=2.0[vo];"
          "[amix][vo]amix=inputs=2:duration=first:dropout_transition=0,"
          "alimiter=limit=0.95[a]"
          % (xf, d - xf, xf, 2 * d - 2 * xf, xf, xf))
    mash_vo = os.path.join(B, "corporate-v2-vo.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", n1, "-i", n2,
                    "-i", n3, "-i", VO, "-filter_complex", fc,
                    "-map", "[v]", "-map", "[a]", "-c:v", "libx264",
                    "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", mash_vo], check=True)
    print("vo mash -> %s" % mash_vo)

    # 4. burn subtitles (3 windows, PIL overlays)
    subs = [sub_png(t, os.path.join(B, "sub_%d.png" % i))
            for i, (t, _, _) in enumerate(SUBS)]
    inputs = ["-i", mash_vo]
    for s in subs:
        inputs += ["-loop", "1", "-i", s]
    fc = ""
    for i, (_, st, en) in enumerate(SUBS):
        fc += ("[%d:v]format=rgba,fade=t=in:st=%.2f:d=0.25:alpha=1,"
               "fade=t=out:st=%.2f:d=0.25:alpha=1[s%d];" % (i + 1, st, en - 0.25, i))
    last = "0:v"
    for i in range(len(SUBS)):
        out_lbl = "[vout]" if i == len(SUBS) - 1 else "[vt%d]" % i
        fc += ("[%s][s%d]overlay=0:0:enable='between(t,%.2f,%.2f)'%s;"
               % (last, i, SUBS[i][1], SUBS[i][2], out_lbl))
        last = out_lbl[1:-1] if i < len(SUBS) - 1 else "vout"
    fc = fc[:-1]
    final = os.path.join(T, "fal-corporate-v2.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + inputs +
                   ["-filter_complex", fc, "-map", "[vout]", "-map", "0:a",
                    "-t", "13.97",  # looped PNG inputs are infinite - cap!
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "copy",
                    "-movflags", "+faststart", final], check=True)
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "format=duration", "-of", "csv=p=0", final],
                       capture_output=True, text=True)
    print("FINAL -> %s (%ss)" % (final, r.stdout.strip()))

    # verify subtitles burned: white pixels in the sub band at t=2 vs t=4.4
    import tempfile
    from PIL import Image
    def band_white(t):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            jp = f.name
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i",
                        final, "-frames:v", "1", "-q:v", "3", jp], check=True)
        im = Image.open(jp).convert("RGB").crop((0, 1350, 1080, 1750))
        os.unlink(jp)
        return sum(1 for p in im.getdata()
                   if p[0] > 235 and p[1] > 235 and p[2] > 235)
    w1, w2 = band_white(2.0), band_white(4.4)
    print("subtitle check: white px at t=2.0: %d (sub window) | t=4.4: %d (gap)"
          % (w1, w2))
    print("SUBTITLES %s" % ("BURNED OK" if w1 > 3000 > w2 else "CHECK FAILED"))
    return 0


if __name__ == "__main__":
    sys.exit(main())