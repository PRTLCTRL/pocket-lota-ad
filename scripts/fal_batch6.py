# -*- coding: utf-8 -*-
"""
fal_batch6.py — v4: the implied-washroom corporate story (T1+T2, copy C).

Storyboard (~17.5s):
  1. tote-grab  (t2i seed + K2.5) — she lifts the tote beside the laptop
  2. occupied   (t2i seed + K2.5) — corridor, indicator flips, door closed
  3. tile-pour  (edit seed w/ black-cap ref + Kling v3 Pro ELEMENTS,
     generate_audio ON) — steep top-down lap-POV: hand + black-cap product,
     pour arc down out of frame, tiles only (T1)
  4. hand-wash  (edit seed w/ black-cap ref + K2.5) — sink outro
  5. end card   (ugc_cut make_endcard) — $0
VO: ElevenLabs Rachel, copy C, timestamps parsed for frame-exact word-pop.

Spend est: 2x t2i (~$0.2 each... see live) + 2x edit seeds (~$0.2 each)
+ 1x v3pro audio+elements (~$0.84) + 2x K2.5 ($0.35 ea) + 1x TTS (~$0.10)
~= $2.6. Single pass; arg fallbacks free; resumable.
"""
import base64
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fal_gen as fg
from fal_batch3 import data_uri
import fal_batch5 as b5
import ugc_cut as uc

ROOT = fg.ROOT
T = os.path.join(ROOT, "fal-tests")
B = os.path.join(T, "b6")
BLACKCAP = os.path.join(T, "design-ref", "lota-detail-blackcap.png")
POUR = os.path.join(ROOT, "lota-pour.png")

T2I = "fal-ai/nano-banana-pro"
EDIT = "fal-ai/nano-banana-pro/edit"
V3PRO = "fal-ai/kling-video/v3/pro/image-to-video"
K25 = "fal-ai/kling-video/v2.5-turbo/pro/image-to-video"
TTS = "fal-ai/elevenlabs/tts/multilingual-v2"
RACHEL = "21m00Tcm4TlvDq8ikWAM"
NEG = fg.NEG

COPY_C = ("Calendar says 2:45. You say finally. Door. Lock. Exhale. "
          "Clean, composed, back by 2:47. Pocket Lota.")

SCENES = [
    {
        "id": "grab",
        "seed_kind": "t2i",
        "seed_prompt": (
            "Amateur smartphone photo, vertical 9:16: a woman's hand with a "
            "neat manicure gripping the strap of a structured work tote "
            "bag, lifting it from an office desk beside an open laptop and "
            "a coffee cup, warm late-afternoon window light, office softly "
            "blurred, visible sensor grain, candid, not a product ad"),
        "model": K25,
        "motion": (
            "Handheld smartphone video, natural micro-shake: the hand "
            "lifts the tote bag off the desk and slings the strap over "
            "her shoulder, laptop glow, warm window light, casual candid "
            "clip, no music"),
        "dur": "5",
    },
    {
        "id": "door",
        "seed_kind": "t2i",
        "seed_prompt": (
            "Amateur smartphone photo, vertical 9:16: a modern office "
            "bathroom corridor, one stall door with a small metal "
            "OCCUPIED slide indicator currently showing green, warm "
            "ceiling light, clean minimal tiles, no people, realistic, "
            "visible sensor grain"),
        "model": K25,
        "motion": (
            "Handheld smartphone video, subtle sway: the small metal "
            "indicator on the door slides from green to red with a soft "
            "click, hold on the closed door, warm steady light, ambient "
            "hush, no music"),
        "dur": "5",
    },
    {
        "id": "pour",
        "seed_kind": "edit",
        "seed_prompt": (
            "Keep this exact product design completely unchanged - same "
            "sleek modern bottle with its MATTE BLACK CAP - in this scene "
            "the black cap is removed and rests at the very edge of frame, "
            "and the open bottle is held by a woman's hand with a neat "
            "manicure. Camera looks STEEPLY DOWNWARD from just above her "
            "lap: hand + bottle near the top of frame, a short tight arc "
            "of clear water shooting DOWN toward the bottom edge of "
            "frame and out of view, small light-gray tile floor filling "
            "the lower frame, a strip of dark trouser fabric visible at "
            "one edge, warm soft light, realistic smartphone photo, "
            "visible sensor grain, no toilet or fixtures anywhere"),
        "model": V3PRO,
        "motion": (
            "Steep top-down handheld shot: the fingers squeeze the "
            "bottle, a tight arc of clear water shoots straight down out "
            "of the bottom of the frame with natural droplets, water "
            "catching warm light, subtle hand tremor, realistic physics, "
            "natural water sound and quiet bathroom ambience, no slow "
            "motion, no music"),
        "dur": "5",
        "elements": True,
    },
    {
        "id": "wash",
        "seed_kind": "edit",
        "seed_prompt": (
            "Keep this exact product design completely unchanged - same "
            "sleek modern bottle with its MATTE BLACK CAP: the capped "
            "bottle stands on the edge of a bathroom sink counter facing "
            "away, label not readable, while a woman's hands with neat "
            "manicure lather soap under running warm water, soft warm "
            "light, mirror softly blurred behind, realistic smartphone "
            "photo, visible sensor grain, no toilet anywhere"),
        "model": K25,
        "motion": (
            "Handheld smartphone video, natural micro-shake: hands lather "
            "soap under running water and rinse, realistic water motion, "
            "the black-capped bottle steady on the counter edge, warm "
            "light, casual candid clip, no music"),
        "dur": "5",
    },
]

BEATS = [("grab", 3.6), ("door", 4.2), ("pour", 5.0), ("wash", 4.2)]
XF = 0.5
CARD_DUR = 2.5


def t2i_or_edit(sc, out_png):
    if os.path.exists(out_png):
        print("seed %s exists - skip" % sc["id"])
        return open(out_png.replace(".png", ".url.txt")).read().strip()
    if sc["seed_kind"] == "t2i":
        attempts = [
            {"prompt": sc["seed_prompt"], "aspect_ratio": "9:16"},
            {"prompt": sc["seed_prompt"]},
        ]
        model = T2I
    else:
        refs = [data_uri(BLACKCAP), data_uri(POUR)]
        attempts = [
            {"prompt": sc["seed_prompt"], "image_urls": refs},
            {"prompt": sc["seed_prompt"], "image_url": refs[0]},
        ]
        model = EDIT
    for i, args in enumerate(attempts):
        try:
            print("  seed %s (%s attempt %d)" % (sc["id"], sc["seed_kind"], i + 1),
                  flush=True)
            r = fg.queue_run(model, args, timeout=300)
            url = (r.get("images") or [{}])[0].get("url") or r.get("image_url")
            if not url:
                raise RuntimeError("no image: %s" % str(r)[:200])
            fg.download(url, out_png)
            open(out_png.replace(".png", ".url.txt"), "w").write(url)
            print("  -> %s" % out_png, flush=True)
            return url
        except Exception as e:
            if fg._rejected(e):
                print("    rejected (free): %s" % str(e)[:110], flush=True)
                time.sleep(1)
                continue
            print("    ERROR: %s" % str(e)[:150], flush=True)
            return None
    return None


def render_scene(sc, seed_url, out_mp4):
    if os.path.exists(out_mp4):
        print("video %s exists - skip" % sc["id"])
        return out_mp4
    m = sc["motion"]
    if sc["model"] == V3PRO:
        du_cap = data_uri(BLACKCAP)
        argsets = [
            {"prompt": m, "start_image_url": seed_url, "duration": "5",
             "generate_audio": True,
             "elements": [{"frontal_image_url": du_cap,
                           "reference_image_urls": [data_uri(POUR)]}]},
            {"prompt": m, "start_image_url": seed_url, "duration": "5",
             "generate_audio": True},
            {"prompt": m, "start_image_url": seed_url, "duration": "5"},
        ]
    else:
        argsets = [
            {"prompt": m, "image_url": seed_url, "duration": "5",
             "negative_prompt": NEG},
            {"prompt": m, "image_url": seed_url, "duration": "5"},
        ]
    for args in argsets:
        try:
            print("  i2v %s :: %s" % (sc["id"], sc["model"].split("/")[-3:]),
                  flush=True)
            r = fg.queue_run(sc["model"], args, timeout=900)
            vurl = fg._first_video_url(r)
            if not vurl:
                raise RuntimeError("no video: %s" % str(r)[:200])
            fg.download(vurl, out_mp4)
            print("  -> %s" % out_mp4, flush=True)
            return out_mp4
        except Exception as e:
            if fg._rejected(e):
                print("    rejected (free): %s" % str(e)[:110], flush=True)
                time.sleep(1)
                continue
            print("    ERROR: %s" % str(e)[:150], flush=True)
            return None
    return None


def tts_copy_c(out_mp3):
    import json
    if os.path.exists(out_mp3):
        print("vo exists - skip")
        if os.path.exists(out_mp3 + ".json"):
            return out_mp3, json.load(open(out_mp3 + ".json"))
        return out_mp3, None
    for extra in ({}, {"with_timestamps": True}):
        args = {"text": COPY_C, "voice_id": RACHEL}
        args.update(extra)
        try:
            print("  tts (copy C, Rachel)", flush=True)
            r = fg.queue_run(TTS, args, timeout=180)
            import json as _j
            a = r.get("audio")
            aurl = a.get("url") if isinstance(a, dict) else a
            aurl = aurl or r.get("audio_url")
            if not aurl:
                raise RuntimeError("no audio: %s" % str(r)[:200])
            fg.download(aurl, out_mp3)
            with open(out_mp3 + ".json", "w") as f:
                _j.dump(r, f)
            print("  -> %s (keys: %s)" % (out_mp3, sorted(r.keys())), flush=True)
            return out_mp3, r
        except Exception as e:
            if fg._rejected(e):
                print("    rejected (free): %s" % str(e)[:110], flush=True)
                time.sleep(1)
                continue
            print("    ERROR: %s" % str(e)[:150], flush=True)
            return None, None
    return None, None


def parse_ts(r):
    """Generic parser for fal's ElevenLabs `timestamps` field."""
    import json
    if not isinstance(r, dict):
        return None
    ts = r.get("timestamps")
    if not ts:
        return None
    print("  timestamps field type: %s" % type(ts).__name__)
    if isinstance(ts, dict):
        print("  timestamps keys: %s" % sorted(ts.keys()))
        chars = ts.get("characters")
        cs = ts.get("character_start_times_seconds") or ts.get("start_times")
        ce = ts.get("character_end_times_seconds") or ts.get("end_times")
        if chars and cs:
            words, cur, start = [], "", None
            for ch, s, e in zip(chars, cs, ce + [None]):
                if ch.strip():
                    if start is None:
                        start = s
                    cur += ch
                elif cur:
                    words.append((cur, float(start), float(e)))
                    cur, start = "", None
            if cur:
                words.append((cur, float(start), float(cs[-1] + 0.2)))
            return words
    if isinstance(ts, list) and ts and isinstance(ts[0], dict):
        print("  first item keys: %s" % sorted(ts[0].keys()))
        words = []
        for it in ts:
            w = it.get("word") or it.get("text")
            s = it.get("start") or it.get("from_s") or it.get("start_time")
            e = it.get("end") or it.get("to_s") or it.get("end_time")
            if w and s is not None:
                words.append((w, float(s), float(e or s + 0.2)))
        return words or None
    return None


def render_track_local(words, total_dur, frames_dir, fps=30):
    """Word-pop caption track, sentences grouped from the ACTUAL word list
    (word ending in . ! ? closes a block) — not the old copy."""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(frames_dir, exist_ok=True)
    font = ImageFont.truetype(b5.FONT, 62)
    blocks, cur = [], []
    for item in words:
        cur.append(item)
        if item[0].endswith((".", "!", "?")):
            blocks.append(cur)
            cur = []
    if cur:
        blocks.append(cur)
    print("caption blocks: %d" % len(blocks))
    n = int(total_dur * fps) + int(0.5 * fps)
    prev_sig = None
    count = 0
    for f in range(n):
        t = f / fps
        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for blk in blocks:
            if t < blk[0][1] - 0.05 or t > blk[-1][2] + 0.35:
                continue
            shown = [(w, s, e) for (w, s, e) in blk if t >= s - 0.02]
            if not shown:
                continue
            active = shown[-1]
            lines, cur_l, curw = [], [], 0
            for (w, s, e) in shown:
                ww = d.textbbox((0, 0), w, font=font)[2]
                if cur_l and curw + ww + 26 > 940:
                    lines.append(cur_l)
                    cur_l, curw = [], 0
                cur_l.append((w, s, e, ww))
                curw += ww + 26
            if cur_l:
                lines.append(cur_l)
            lh = 82
            y0 = 1580 - len(lines) * lh
            maxw = max(sum(x[3] + 26 for x in ln) - 26 for ln in lines)
            d.rounded_rectangle([540 - maxw // 2 - 40, y0 - 26,
                                 540 + maxw // 2 + 40,
                                 y0 + len(lines) * lh + 26], 26,
                                fill=(0, 0, 0, 122))
            for li, ln in enumerate(lines):
                total_w = sum(x[3] + 26 for x in ln) - 26
                x = 540 - total_w // 2
                for (w, s, e, ww) in ln:
                    col = b5.YELLOW if (w, s, e) == active and t < e + 0.10 \
                        else b5.WHITE
                    d.text((x, y0 + li * lh), w, font=font, fill=col)
                    x += ww + 26
        sig = img.tobytes()[::97]
        if sig != prev_sig:
            img.save(os.path.join(frames_dir, "f_%04d.png" % f))
            prev_sig = sig
            count += 1
    last = None
    for f in range(n):
        p = os.path.join(frames_dir, "f_%04d.png" % f)
        if os.path.exists(p):
            last = p
        elif last:
            from PIL import Image as I
            I.open(last).save(p)
    print("caption track: %d states -> %d frames" % (count, n))
    return frames_dir


def main():
    import json
    import tempfile
    import wave
    import numpy as np
    if not fg.load_env():
        return 2
    os.makedirs(B, exist_ok=True)

    du_blackcap = data_uri(BLACKCAP)
    print("black-cap ref loaded (%d KB)" % (len(du_blackcap) // 1024))

    # 1. seeds
    for sc in SCENES:
        u = t2i_or_edit(sc, os.path.join(B, "seed-%s.png" % sc["id"]))
        sc["url"] = u

    # 2. renders
    for sc in SCENES:
        if not sc.get("url"):
            print("scene %s: no seed - skip render" % sc["id"])
            continue
        if sc.get("elements"):
            sc["motion"] = sc["motion"]  # plain (no #1 - kept simple)
        sc["mp4"] = render_scene(sc, sc["url"],
                                 os.path.join(B, "scene-%s.mp4" % sc["id"]))

    # 3. VO with timestamps
    vo, vo_r = tts_copy_c(os.path.join(B, "vo-c-rachel.mp3"))
    words = parse_ts(vo_r) if vo_r else None
    if not words and vo:
        res = b5.energy_word_onsets(vo, len(COPY_C.split()))
        if res:
            starts, dur = res
            raw = COPY_C.split()
            words = []
            for i, w in enumerate(raw):
                s = starts[i] if i < len(starts) else starts[-1]
                e = starts[i + 1] if i + 1 < len(starts) else dur
                words.append((w, s, e))
    print("word timings: %s" % ("metadata" if words else "MISSING"))
    if words:
        for w, s, e in words[:3]:
            print("   %.2f-%.2f %s" % (s, e, w))

    # 4. assemble
    if not all(sc.get("mp4") for sc in SCENES) or not vo:
        print("assembly skipped (missing scenes/VO)")
        return 1
    scene_by_id = {s["id"]: s for s in SCENES}
    norms = []
    for sid, dur in BEATS:
        src = scene_by_id[sid]["mp4"]
        n = os.path.join(B, "n_%s.mp4" % sid)
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0",
                            "-show_entries", "stream=codec_type", "-of",
                            "csv=p=0", src], capture_output=True, text=True)
        has_a = "audio" in (r.stdout or "")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", src]
        if not has_a:
            cmd += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
        cmd += ["-filter_complex",
                "[0:v]scale=1080:1920:force_original_aspect_ratio="
                "increase,crop=1080:1920,setsar=1,fps=30[v]",
                "-map", "[v]", "-map", "0:a" if has_a else "1:a",
                "-t", str(dur), "-c:v", "libx264", "-preset", "medium",
                "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac",
                "-b:a", "160k", "-ar", "44100", "-ac", "2", n]
        subprocess.run(cmd, check=True)
        norms.append((n, dur))
    card_png = uc.make_endcard_png(os.path.join(B, "endcard.png"))
    card = os.path.join(B, "card.mp4")
    uc.build_card(card_png, card, dur=CARD_DUR)

    total = sum(d for _, d in norms) + CARD_DUR - XF * 4
    print("film length: %.1fs" % total)
    fc = ""
    offs = []
    t = 0.0
    inputs = []
    for n, d in norms:
        inputs += ["-i", n]
    inputs += ["-i", card, "-i", vo]
    # video chain
    off = norms[0][1] - XF
    fc += "[0:v][1:v]xfade=transition=fade:duration=%.2f:offset=%.2f[v01];" % (XF, off)
    off2 = off + norms[1][1] - XF
    fc += "[v01][2:v]xfade=transition=fade:duration=%.2f:offset=%.2f[v12];" % (XF, off2)
    off3 = off2 + norms[2][1] - XF
    fc += "[v12][3:v]xfade=transition=smoothleft:duration=%.2f:offset=%.2f[v34];" % (XF, off3)
    off4 = off3 + norms[3][1] - XF
    fc += "[v34][4:v]xfade=transition=fadeblack:duration=%.2f:offset=%.2f[v];" % (XF, off4)
    # audio: all scene audios + VO
    fc += ("[0:a][1:a]acrossfade=d=%.2f[a01];[a01][2:a]acrossfade=d=%.2f[a02];"
           "[a02][3:a]acrossfade=d=%.2f[a03];[a03][4:a]acrossfade=d=%.2f[amix];"
           % (XF, XF, XF, XF))
    fc += "[5:a]adelay=1200|1200,volume=2.0[vo];"
    fc += ("[amix][vo]amix=inputs=2:duration=first:dropout_transition=0,"
           "alimiter=limit=0.95[a]")
    mash_vo = os.path.join(B, "v4-vo.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + inputs +
                   ["-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-t", "%.2f" % total, mash_vo], check=True)
    print("vo mash -> %s" % mash_vo)

    # 5. word-pop captions
    if words:
        SHIFT = 1.2
        words = [(w, s + SHIFT, e + SHIFT) for (w, s, e) in words]
        frames_dir = render_track_local(words, total, os.path.join(B, "frames"))
        final = os.path.join(T, "fal-corporate-v4.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error",
                        "-framerate", "30", "-i",
                        os.path.join(frames_dir, "f_%04d.png"),
                        "-i", mash_vo, "-filter_complex",
                        "[0:v]format=rgba[cap];[1:v][cap]overlay=0:0[v]",
                        "-map", "[v]", "-map", "1:a", "-t", "%.2f" % total,
                        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                        "-pix_fmt", "yuv420p", "-c:a", "copy",
                        "-movflags", "+faststart", final], check=True)
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration", "-of", "csv=p=0", final],
                           capture_output=True, text=True)
        print("FINAL -> %s (%ss)" % (final, r.stdout.strip()))
        s = fg.score(final)
        print("gate: %s | yellow %.2f%%" % (s["realism"], s["yellow_pct"]))
        return 0
    print("no word timings - v4-vo only (no captions)")
    return 1


if __name__ == "__main__":
    sys.exit(main())