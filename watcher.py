#!/usr/bin/env python3
"""Watch the ZWiK Łódź failures page for a outage notice
and ping a Telegram chat when it appears (once per new occurrence)."""

import json
import os
import re
import sys
import urllib.request
import ssl


def _load_dotenv() -> None:
    """Load KEY=VAL lines from .env file into env, if it exists."""
    try:
        with open(".env", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())
    except FileNotFoundError:
        pass


_load_dotenv()

LISTING_URL = "https://zwik.lodz.pl/pl/artykuly/302/awarie"
BASE = "https://zwik.lodz.pl"
STATE_FILE = "last_seen.txt"

NEEDLE = re.compile(os.environ.get("NEEDLE_PATTERN", r"{location}"), re.IGNORECASE)

# Finds the newest daily "komunikat" article link on the failures listing.
ARTICLE_HREF = re.compile(r'/pl/artykul/302/\d+/komunikat[^"\']*')

HEADERS = {"User-Agent": "Mozilla/5.0 (zwik-watcher; +github-actions)"}
TG_API = "https://api.telegram.org/bot{token}/sendMessage"

def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError:
        # Retry with unverified context (macOS Python cert issue).
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            return resp.read().decode("utf-8", errors="replace")


def latest_announcement_url() -> str:
    html = fetch(LISTING_URL)
    m = ARTICLE_HREF.search(html)
    if not m:
        # Fall back to scanning the listing page itself.
        return LISTING_URL
    return BASE + m.group(0)


def read_state() -> str:
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


def write_state(value: str) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        f.write(value)


def notify(text: str) -> None:
    token = os.environ["TELEGRAM_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    payload = json.dumps(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        TG_API.format(token=token),
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
    except urllib.error.URLError:

        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
            resp.read()


def main() -> int:
    if "--test" in sys.argv[1:]:
        notify(
            "✅ ZWiK watcher test message. If you can read this, your "
            "Telegram token and chat ID are wired up correctly."
        )
        print("test message sent")
        return 0

    url = latest_announcement_url()
    page = fetch(url)
    hit = bool(NEEDLE.search(page))

    previous = read_state()
    current = url if hit else ""

    if hit and current != previous:
        notify(
            "\U0001f6b0 Water failure alert! Your residence appears in the latest "
            f"outage notice.\n\n{url}"
        )
        write_state(current)
        print(f"MATCH -> notified for {url}")
    elif hit:
        print(f"MATCH but already notified for {url}")
    else:
        write_state("")
        print("no match")

    return 0


if __name__ == "__main__":
    sys.exit(main())
