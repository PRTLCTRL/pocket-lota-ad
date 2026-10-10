# -*- coding: utf-8 -*-
"""
fal_batch3.py — corporate-women round: real-design consistency + office story.

Per Arsal's Oct 10 review (batch-3 go):
  1. Seeds via nano-banana-pro/edit with the REAL product design as reference
     (lota-detail.jpg padded to 9:16) — design consistency, woman's hand,
     corporate office desk scenes.
  2. i2v on Kling 2.5 Turbo (dim/warm per batch-2 grain finding).
  3. Realistic female VO (ElevenLabs multilingual-v2, voice Rachel) —
     same copy he loved, verbatim.
  4. Corporate-story mash: office-desk -> demo-arc (existing) -> sealed-in-bag.

Spend (single pass, arg-fallbacks free): 2x nano-banana-pro/edit (~$0.2 ea)
+ 2x Kling 2.5 i2v ($0.35 ea) + 1x ElevenLabs (~$0.10) ~= $1.2 of the ~$1.5
batch-3 envelope. Resumable: existing outputs skipped.
"""
import base64
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fal_gen as fg  # queue_run, download, load_env, _req, KEY handling

ROOT = fg.ROOT
T = os.path.join(ROOT, "fal-tests")
DESIGN = os.path.join(ROOT, "lota-detail.jpg")
A_DEMO = os.path.join(T, "A-demo-arc.mp4")

VO_COPY = ("Between meetings, your break should actually feel like one. "
           "Pocket Lota - sleek, sealed, and it lives in your work bag. "
           "The cleaner solution, wherever your day goes.")
RACHEL = "21m00Tcm4TlvDq8ikWAM"  # ElevenLabs premade female (warm, professional)

EDIT_MODEL = "fal-ai/nano-banana-pro/edit"
I2V_MODEL = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"
TTS_MODEL = "fal-ai/elevenlabs/tts/multilingual-v2"

NEG = fg.NEG


def pad_916(src, out):
    """Pad the product shot to a 1080x1920 canvas for the edit model."""
    from PIL import Image
    img = Image.open(src).convert("RGB")
    canvas = Image.new("RGB", (1080, 1920), (245, 245, 242))
    img.thumbnail((1000, 1000), Image.LANCZOS)
    canvas.paste(img, ((1080 - img.width) // 2, (1920 - img.height) // 2))
    canvas.save(out)
    return out


def data_uri(path):
    ext = "png" if path.lower().endswith(".png") else "jpeg"
    with open(path, "rb") as f:
        return "data:image/%s;base64,%s" % (ext, base64.b64encode(f.read()).decode())


def edit_seed(name, prompt, ref_du, out_png):
    if os.path.exists(out_png):
        print("seed %s exists - skip" % name)
        return open(out_png.replace(".png", ".url.txt")).read().strip()
    attempts = [
        {"prompt": prompt, "image_urls": [ref_du]},
        {"prompt": prompt, "image_url": ref_du},
        {"prompt": prompt, "images": [ref_du]},
        {"prompt": prompt, "image_urls": [ref_du], "aspect_ratio": "9:16"},
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


def i2v(name, motion, seed_url, out_mp4):
    if os.path.exists(out_mp4):
        print("video %s exists - skip" % name)
        return out_mp4
    for args in ({"prompt": motion, "image_url": seed_url, "duration": "5",
                  "negative_prompt": NEG},
                 {"prompt": motion, "image_url": seed_url, "duration": "5"}):
        try:
            print("  i2v submit %s" % name, flush=True)
            r = fg.queue_run(I2V_MODEL, args, timeout=900)
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


def realistic_vo(out_mp3):
    if os.path.exists(out_mp3):
        print("vo exists - skip")
        return out_mp3
    for args in ({"text": VO_COPY, "voice_id": RACHEL},
                 {"text": VO_COPY, "voice_id": RACHEL,
                  "model_settings": {"stability": 0.5, "similarity_boost": 0.75}},
                 {"text": VO_COPY}):
        try:
            print("  tts submit (elevenlabs multilingual-v2)", flush=True)
            r = fg.queue_run(TTS_MODEL, args, timeout=180)
            # elevenlabs on fal: {"audio": {"url": ...}} typically
            aurl = None
            if isinstance(r, dict):
                a = r.get("audio")
                if isinstance(a, dict):
                    aurl = a.get("url")
                elif isinstance(a, str):
                    aurl = a
                aurl = aurl or r.get("audio_url")
            if not aurl:
                raise RuntimeError("no audio url: %s" % str(r)[:200])
            fg.download(aurl, out_mp3)
            print("  -> %s" % out_mp3, flush=True)
            return out_mp3
        except Exception as e:
            if fg._rejected(e):
                print("    rejected (free): %s" % str(e)[:120], flush=True)
                time.sleep(1)
                continue
            print("    ERROR: %s" % str(e)[:150], flush=True)
            return None
    return None


def f0_check(path, label):
    wav = os.path.join(tempfile.gettempdir(), "vo_check.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ac", "1",
                    "-ar", "16000", wav], check=True)
    w = wave.open(wav)
    data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
    sr = w.getframerate()
    seg = data[int(sr * 0.3):int(sr * 0.3) + sr * 5]
    frame, hop = int(sr * 0.04), int(sr * 0.02)
    f0s = []
    for i in range(0, len(seg) - frame, hop):
        s = seg[i:i + frame]
        if np.sqrt((s ** 2).mean()) < 200:
            continue
        s = s - s.mean()
        corr = np.correlate(s, s, "full")[frame - 1:]
        corr /= (corr[0] + 1e-9)
        lo, hi = int(sr / 300), int(sr / 70)
        if hi >= len(corr):
            continue
        lag = lo + int(np.argmax(corr[lo:hi]))
        if corr[lag] > 0.5:
            f0s.append(sr / lag)
    med = float(np.median(f0s)) if f0s else 0.0
    print("%s: median F0 %.0f Hz -> %s" %
          (label, med, "FEMALE" if med >= 160 else "MALE" if med > 0 else "?"))
    return med


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
    import numpy as np  # noqa (kept for f0_check)
    globals()["np"] = np
    if not fg.load_env():
        return 2
    os.makedirs(os.path.join(T, "b3"), exist_ok=True)
    B = os.path.join(T, "b3")

    # 0. design reference -> 9:16 padded canvas -> data URI
    ref = pad_916(DESIGN, os.path.join(B, "design-ref-916.png"))
    du = data_uri(ref)
    print("design ref padded: %s (%d bytes as data uri)" % (ref, len(du)))

    # 1. corporate office seeds (real design, woman's hand)
    s1 = edit_seed("desk-break",
                   "Keep this exact product design completely unchanged - "
                   "same sleek modern bottle, same cap and tube, same colors "
                   "and proportions. Show it being lifted out of a "
                   "professional woman's tote bag onto a corporate office "
                   "desk by a woman's hand with a neat manicure, laptop and "
                   "coffee cup softly blurred behind, warm late-afternoon "
                   "window light, realistic candid smartphone photo, "
                   "vertical composition, visible sensor grain, not a "
                   "product ad",
                   du, os.path.join(B, "seed-desk.png"))
    s2 = edit_seed("sealed-bag",
                   "Keep this exact product design completely unchanged - "
                   "same sleek modern bottle, same cap and tube, same colors "
                   "and proportions. Show a woman's hand with neat manicure "
                   "sliding it into the side pocket of a structured work "
                   "tote bag on an office desk, zipper about to close over "
                   "it, warm window light, realistic candid smartphone "
                   "photo, vertical composition, visible sensor grain",
                   du, os.path.join(B, "seed-bag.png"))

    # 2. i2v both scenes (Kling 2.5, warm office motion)
    v1 = i2v("desk-break",
             "Handheld smartphone video, natural micro-shake: the woman's "
             "hand lifts the sleek bottle out of the tote bag onto the desk, "
             "sets it beside her coffee, warm window light, realistic "
             "textures, visible sensor grain, casual candid clip",
             s1, os.path.join(B, "scene-desk.mp4")) if s1 else None
    v2 = i2v("sealed-bag",
             "Handheld smartphone video, natural micro-shake: the woman's "
             "hand slides the sleek bottle into the tote's side pocket and "
             "zips it closed, a small confident pat on the pocket, warm "
             "window light, realistic textures, visible sensor grain, "
             "casual candid clip",
             s2, os.path.join(B, "scene-bag.mp4")) if s2 else None

    # 3. realistic female VO (same copy, verbatim)
    vo = realistic_vo(os.path.join(B, "vo-female-real.mp3"))

    # 4. corporate-story mash: desk -> demo-arc -> sealed-bag + VO
    if v1 and v2 and vo and os.path.exists(A_DEMO):
        n1 = norm_clip(v1, os.path.join(B, "n1.mp4"))
        n2 = norm_clip(A_DEMO, os.path.join(B, "n2.mp4"))
        n3 = norm_clip(v2, os.path.join(B, "n3.mp4"))
        d, xf = 5.04, 0.6
        fc = ("[0:v][1:v]xfade=transition=fade:duration=%s:offset=%.2f[v01];"
              "[v01][2:v]xfade=transition=smoothleft:duration=%s:offset=%.2f[v];"
              "[0:a][1:a]acrossfade=d=%s[a01];[a01][2:a]acrossfade=d=%s[amix];"
              "[3:a]adelay=600|600,volume=2.0[vo];"
              "[amix][vo]amix=inputs=2:duration=first:dropout_transition=0,"
              "alimiter=limit=0.95[a]"
              % (xf, d - xf, xf, 2 * d - 2 * xf, xf, xf))
        out = os.path.join(T, "fal-corporate-v1.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", n1, "-i", n2,
                        "-i", n3, "-i", vo, "-filter_complex", fc,
                        "-map", "[v]", "-map", "[a]", "-c:v", "libx264",
                        "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                        out], check=True)
        print("CORPORATE MASH -> %s" % out)
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", out],
                           capture_output=True, text=True)
        print("duration: %ss" % r.stdout.strip())
        f0_check(vo, "elevenlabs VO")
    else:
        print("mash skipped: v1=%s v2=%s vo=%s" % (bool(v1), bool(v2), bool(vo)))
    return 0


if __name__ == "__main__":
    sys.exit(main())