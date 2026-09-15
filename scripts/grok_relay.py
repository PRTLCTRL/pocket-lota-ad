#!/usr/bin/env python
"""grok_relay.py — xAI Grok relay for the agent-board (pocket-lota-ad/board/).

Polls board/inbox/grok/ for task messages, sends content to xAI chat API,
writes replies into board/inbox/hermes/, archives the task.

Token: reads XAI_API_KEY from finza/.env (NEVER prints it).
Run: python scripts/grok_relay.py [--once] [--poll 30]
"""
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOARD = REPO / "board"
INBOX_GROK = BOARD / "inbox" / "grok"
INBOX_HERMES = BOARD / "inbox" / "hermes"
ARCHIVE = BOARD / "archive"
API_URL = "https://api.x.ai/v1/chat/completions"
MODEL = os.environ.get("GROK_MODEL", "grok-4-fast")


def load_key():
    """Read XAI_API_KEY from finza/.env without printing it."""
    env = Path(r"C:\Users\Arsal\Projects\finza\.env")
    for line in env.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("XAI_API_KEY="):
            key = line.split("=", 1)[1].strip().strip('"').strip("'")
            if key:
                return key
    return None


def parse_frontmatter(text):
    """Extract simple key: value frontmatter between --- lines."""
    meta = {}
    body = text
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = m.group(2)
    return meta, body.strip()


def grok_call(api_key, system, user_text):
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user_text},
        ],
        "temperature": 0.8,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    return data["choices"][0]["message"]["content"]


def process_message(path, api_key):
    raw = path.read_text(encoding="utf-8", errors="replace")
    meta, body = parse_frontmatter(raw)
    frm = meta.get("from", "unknown")
    to = meta.get("to", "grok")
    topic = meta.get("topic", "general")
    mtype = meta.get("type", "task")

    if to not in ("grok", "all"):
        print(f"skip {path.name}: not addressed to grok (to={to})")
        return False

    system = (
        "You are Grok, collaborating on the Pocket Lota ad pipeline with Hermes "
        "(an operational agent) and Arsal (the human conduit). You receive tasks "
        "and questions via the board. Be creative but concrete; every deliverable "
        "must be directly usable (copy-paste ready). If a task is unclear, state "
        "your assumptions and deliver the best interpretation anyway. If a task "
        "seems harmful or off-mission, refuse and explain."
    )
    user = f"[message type: {mtype} | topic: {topic} | from: {frm}]\n\n{body}"

    print(f"processing {path.name} -> xAI ({MODEL})")
    reply = grok_call(api_key, system, user)

    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    fname = f"{stamp}-grok-{topic}.md"
    reply_text = (
        f"---\nfrom: grok\nto: {frm}\ntopic: {topic}\n"
        f"type: reply\ncreated: {datetime.now().astimezone().isoformat(timespec='seconds')}\n"
        f"in_reply_to: {path.name}\n---\n\n{reply}\n"
    )
    (INBOX_HERMES / fname).write_text(reply_text, encoding="utf-8")

    # archive the task
    (BOARD / "archive").mkdir(exist_ok=True)
    path.rename(BOARD / "archive" / path.name)
    print(f"reply written: {fname}")
    return True


def main():
    once = "--once" in sys.argv
    poll = 30
    if "--poll" in sys.argv:
        poll = int(sys.argv[sys.argv.index("--poll") + 1])

    api_key = load_key()
    if not api_key:
        print("XAI_API_KEY not found in finza/.env — add it to go live.")
        sys.exit(1)

    while True:
        INBOX_GROK.mkdir(parents=True, exist_ok=True)
        msgs = sorted(INBOX_GROK.glob("*.md"))
        if not msgs:
            if once:
                print("no messages")
                break
            time.sleep(poll)
            continue
        for p in msgs:
            try:
                process_message(p, api_key)
            except Exception as e:
                print(f"error on {p.name}: {e}")
        if once:
            break


if __name__ == "__main__":
    main()