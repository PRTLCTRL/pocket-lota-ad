# -*- coding: utf-8 -*-
"""
fal_batch5.py — TikTok-style word-pop captions (Arsal's "yes").

Path: regenerate the VO via fal ElevenLabs requesting word/character
timestamps -> build a word-timing table -> render a 30fps RGBA caption
track (words pop in white, the ACTIVE word in brand yellow, dark scrim,
bottom third) -> single ffmpeg overlay onto the pre-subtitle corporate
mash (b4/corporate-v2-vo.mp4) -> fal-corporate-v3.mp4.

Fallback: if no timestamp metadata is exposed by the fal wrapper, derive
word onsets from the audio itself (short-time energy valleys), mapped
onto the known word sequence.

Spend: 1x ElevenLabs regeneration ~$0.10. Everything else local + free.
"""
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fal_gen as fg

ROOT = fg.ROOT
T = os.path.join(ROOT, "fal-tests")
B = os.path.join(T, "b5")
BASE = os.path.join(T, "b4", "corporate-v2-vo.mp4")  # pre-subtitle mash w/ VO

VO_COPY = ("Between meetings, your break should actually feel like one. "
           "Pocket Lota - sleek, sealed, and it lives in your work bag. "
           "The cleaner solution, wherever your day goes.")
RACHEL = "21m00Tcm4TlvDq8ikWAM"
TTS_MODELS = [
    "fal-ai/elevenlabs/tts/multilingual-v2",
    "fal-ai/elevenlabs/tts/eleven-v3",
]
YELLOW = (255, 214, 64, 255)
WHITE = (255, 255, 255, 255)
FONT = r"C:\Windows\Fonts\ariblk.ttf"


def tts_with_timestamps(out_mp3):
    """Probe ElevenLabs endpoints for timestamp metadata; return (path, meta)."""
    for model in TTS_MODELS:
        for extra in ({"with_timestamps": True}, {}, {"enable_logging": False}):
            args = {"text": VO_COPY, "voice_id": RACHEL}
            args.update(extra)
            try:
                print("  tts submit %s %s" % (model, extra), flush=True)
                r = fg.queue_run(model, args, timeout=180)
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
                meta_keys = sorted(r.keys()) if isinstance(r, dict) else []
                print("  -> %s | response keys: %s" % (out_mp3, meta_keys),
                      flush=True)
                return out_mp3, r
            except Exception as e:
                if fg._rejected(e):
                    print("    rejected (free): %s" % str(e)[:120], flush=True)
                    time.sleep(1)
                    continue
                print("    ERROR: %s" % str(e)[:150], flush=True)
                return None, None
    return None, None


def energy_word_onsets(mp3, n_words):
    """No-metadata fallback: find inter-word valleys via short-time energy."""
    import wave
    import numpy as np
    wav = os.path.join(B, "vo.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", mp3, "-ac", "1",
                    "-ar", "16000", wav], check=True)
    w = wave.open(wav)
    data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(float)
    sr = w.getframerate()
    hop = int(sr * 0.01)
    win = int(sr * 0.025)
    energy = np.array([np.sqrt((data[i:i + win] ** 2).mean())
                       for i in range(0, len(data) - win, hop)])
    smooth = np.convolve(energy, np.ones(5) / 5, "same")
    # find local minima under a threshold, spaced >= 90ms
    onsets = []
    thr = smooth.max() * 0.18
    for i in range(2, len(smooth) - 2):
        if (smooth[i] < thr and smooth[i] <= smooth[i - 1]
                and smooth[i] <= smooth[i + 1]
                and (not onsets or (i - onsets[-1]) * 0.01 > 0.09)):
            onsets.append(i)
    if not onsets:
        return None
    # merge: too many valleys -> keep the deepest n_words-1
    if len(onsets) >= n_words:
        vals = sorted(onsets, key=lambda i: smooth[i])[:n_words - 1]
        onsets = sorted(vals)
    dur = float(len(data)) / sr
    times = [o * 0.01 for o in onsets]
    # word starts = valley times; first word starts at first voiced energy
    first = next((i * 0.01 for i in range(len(smooth))
                  if smooth[i] > smooth.max() * 0.25), 0.05)
    starts = [first] + times
    return starts, dur


def char_ts_to_words(r):
    """ElevenLabs character timestamps -> word (start, end) list."""
    al = None
    if isinstance(r, dict):
        al = r.get("alignment") or r.get("character_timestamps") or \
             r.get("timestamps") or r.get("normalized_character_timestamps")
    if not al:
        return None
    chars = al.get("characters") or []
    starts = al.get("character_start_times_seconds") or \
        al.get("start_times") or []
    ends = al.get("character_end_times_seconds") or al.get("end_times") or []
    if not (chars and starts):
        return None
    words, cur, cs = [], "", None
    for ch, s, e in zip(chars, starts, ends + [None]):
        if ch.strip():
            if cs is None:
                cs = s
            cur += ch
        elif cur:
            words.append((cur, float(cs), float(ends[max(0, len(ends) - 1)])
                          if not e else float(e)))
            cur, cs = "", None
    if cur:
        words.append((cur, float(cs), float(starts[-1])))
    return words


def render_track(words, total_dur, frames_dir, fps=30):
    """RGBA PNG sequence: word-pop captions, active word in yellow."""
    from PIL import Image, ImageDraw, ImageFont
    os.makedirs(frames_dir, exist_ok=True)
    font = ImageFont.truetype(FONT, 62)
    sentences = [[], [], []]
    idx = 0
    for si, sent in enumerate(VO_COPY.split(". ")):
        if not sent.endswith("."):
            sent = sent + "."
        ws = sent.split()
        for w in ws:
            if idx < len(words):
                sentences[si].append(words[idx])
                idx += 1
    n = int(total_dur * fps) + int(0.5 * fps)
    prev_sig = None
    count = 0
    for f in range(n):
        t = f / fps
        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for sent in sentences:
            if not sent or t < sent[0][1] - 0.05 or t > sent[-1][2] + 0.35:
                continue
            shown = [(w, s, e) for (w, s, e) in sent if t >= s - 0.02]
            if not shown:
                continue
            active = shown[-1]
            # wrap shown words to lines (max 940px)
            lines, cur, curw = [], [], 0
            for (w, s, e) in shown:
                ww = d.textbbox((0, 0), w, font=font)[2]
                if cur and curw + ww + 26 > 940:
                    lines.append(cur)
                    cur, curw = [], 0
                cur.append((w, s, e, ww))
                curw += ww + 26
            if cur:
                lines.append(cur)
            lh = 82
            y0 = 1580 - len(lines) * lh
            # scrim
            maxw = max(sum(ww + 26 for *_ , ww in [(x[0], x[1], x[2], x[3]) for x in ln]) - 26 for ln in lines)
            d.rounded_rectangle([540 - maxw // 2 - 40, y0 - 26,
                                 540 + maxw // 2 + 40, y0 + len(lines) * lh + 26],
                                26, fill=(0, 0, 0, 122))
            for li, ln in enumerate(lines):
                total_w = sum(x[3] + 26 for x in ln) - 26
                x = 540 - total_w // 2
                for (w, s, e, ww) in ln:
                    col = YELLOW if (w, s, e) == active and t < e + 0.10 else WHITE
                    d.text((x, y0 + li * lh), w, font=font, fill=col)
                    x += ww + 26
        sig = img.tobytes()[::97]
        if sig != prev_sig:
            img.save(os.path.join(frames_dir, "f_%04d.png" % f))
            prev_sig = sig
            count += 1
    # fill gaps: ffmpeg image2 needs contiguous or it holds last frame only
    # -> copy previous frame forward for missing indices
    last = None
    for f in range(n):
        p = os.path.join(frames_dir, "f_%04d.png" % f)
        if os.path.exists(p):
            last = p
        elif last:
            from PIL import Image as I
            I.open(last).save(p)
    print("caption track: %d unique states -> %d frames" % (count, n))
    return frames_dir


def main():
    if not fg.load_env():
        return 2
    os.makedirs(B, exist_ok=True)
    vo = os.path.join(B, "vo-rachel-ts.mp3")
    got, r = tts_with_timestamps(vo)
    if not got:
        print("TTS failed - abort")
        return 1
    words = char_ts_to_words(r)
    import wave
    wavp = os.path.join(B, "dur.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", vo, "-ac", "1",
                    "-ar", "16000", wavp], check=True)
    w = wave.open(wavp)
    total_dur = w.getnframes() / w.getframerate()
    w.close()
    os.unlink(wavp)
    if words:
        print("word timings from ElevenLabs metadata: %d words" % len(words))
    else:
        print("no timestamp metadata - energy-onset fallback")
        words_raw = VO_COPY.split()
        res = energy_word_onsets(vo, len(words_raw))
        if not res:
            print("onset detection failed - abort")
            return 1
        starts, dur = res
        words = []
        for i, wd in enumerate(words_raw):
            s = starts[i] if i < len(starts) else starts[-1] + 0.3
            e = starts[i + 1] if i + 1 < len(starts) else dur
            words.append((wd, s, e))
    for wd, s, e in words[:5]:
        print("   %.2f-%.2f  %s" % (s, e, wd))
    print("total words: %d, audio %.2fs" % (len(words), total_dur))

    # shift VO offset: the mash mixes VO with adelay=600ms -> shift timings
    SHIFT = 0.6
    words = [(wd, s + SHIFT, e + SHIFT) for (wd, s, e) in words]

    frames_dir = render_track(words, 13.97, os.path.join(B, "frames"))

    final = os.path.join(T, "fal-corporate-v3.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error",
                    "-framerate", "30", "-i",
                    os.path.join(frames_dir, "f_%04d.png"),
                    "-i", BASE, "-filter_complex",
                    "[0:v]format=rgba[cap];[1:v][cap]overlay=0:0[v]",
                    "-map", "[v]", "-map", "1:a", "-t", "13.97",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "copy",
                    "-movflags", "+faststart", final], check=True)
    r2 = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                         "format=duration", "-of", "csv=p=0", final],
                       capture_output=True, text=True)
    print("FINAL -> %s (%ss)" % (final, r2.stdout.strip()))

    # deterministic verify: yellow active word + white prior words mid-line
    import tempfile
    from PIL import Image
    def zone(t, box, cond):
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            jp = f.name
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i",
                        final, "-frames:v", "1", "-q:v", "3", jp], check=True)
        im = Image.open(jp).crop(box)
        os.unlink(jp)
        return sum(1 for p in im.getdata() if cond(*p))
    mid = None
    for wd, s, e in words:
        if e > 2.0:
            mid = (wd, s, e)
            break
    t_check = (mid[1] + mid[2]) / 2 if mid else 2.0
    yel = zone(t_check, (0, 1300, 1080, 1750),
               lambda r, g, b: r > 220 and g > 180 and b < 110)
    wht = zone(t_check, (0, 1300, 1080, 1750),
               lambda r, g, b: r > 235 and g > 235 and b > 235)
    gap = zone(13.5, (0, 1300, 1080, 1750),
               lambda r, g, b: r > 220 and g > 180 and b < 110)
    print("verify @%.2fs: yellow=%d white=%d | @13.5s yellow=%d" %
          (t_check, yel, wht, gap))
    print("WORD-POP CAPTIONS %s" %
          ("OK" if yel > 800 and wht > 1500 and gap < 100 else "CHECK FAILED"))
    return 0


if __name__ == "__main__":
    sys.exit(main())