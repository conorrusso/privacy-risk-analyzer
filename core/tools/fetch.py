"""
URL fetching with Jina Reader fallback.

Strategy
--------
1. Direct HTTP fetch with a browser-like User-Agent.
2. On any failure, retry via Jina Reader (r.jina.ai/{url}) which renders
   JavaScript-heavy pages and returns clean text.

Both paths cap reads at _MAX_BYTES to prevent OOM on large pages.
"""
from __future__ import annotations

import urllib.error
import urllib.request

_TIMEOUT = 25  # seconds
_MAX_BYTES = 800_000  # ~800 KB — enough for any privacy policy
_JINA_BASE = "https://r.jina.ai/"

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",  # skip gzip so we can cap bytes
}


def fetch_url(url: str) -> tuple[str, str]:
    """Fetch a URL and return (content, source).

    source is "direct" or "jina".

    Raises
    ------
    urllib.error.URLError
        If both the direct fetch and the Jina fallback fail.
    """
    try:
        return _fetch_direct(url), "direct"
    except Exception:
        return _fetch_jina(url), "jina"


def _fetch_direct(url: str) -> str:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        raw = resp.read(_MAX_BYTES)
        return raw.decode(_detect_charset(resp), errors="replace")


def _fetch_jina(url: str) -> str:
    jina_url = _JINA_BASE + url
    headers = {**_HEADERS, "X-Return-Format": "text", "X-Timeout": "20"}
    req = urllib.request.Request(jina_url, headers=headers)
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        raw = resp.read(_MAX_BYTES)
        return raw.decode(_detect_charset(resp), errors="replace")


def _detect_charset(resp) -> str:
    """Parse charset from Content-Type header, defaulting to utf-8."""
    ct = resp.headers.get("Content-Type", "")
    for part in ct.split(";"):
        part = part.strip()
        if part.lower().startswith("charset="):
            return part.split("=", 1)[1].strip().strip('"')
    return "utf-8"
