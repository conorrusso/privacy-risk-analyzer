"""
Staged privacy policy URL discovery.

Stages (run in order until one succeeds):
  0  Name normalisation — free, instant
  1  DuckDuckGo web search — primary (~95% success, ~0 cost)
  2  Multi-TLD HEAD probe — free, ~2-4 s of HTTP
  3  AI domain reasoning — rare fallback (~200 tokens)
  4  Homepage link scrape — last resort
  5  Manual review flag — logs to ~/.bandit/manual-review.json

Cache: ~/.bandit/domain-cache.json  (30-day TTL)
"""
from __future__ import annotations

import datetime
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

# ─────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────

_CACHE_PATH  = pathlib.Path.home() / ".bandit" / "domain-cache.json"
_REVIEW_PATH = pathlib.Path.home() / ".bandit" / "manual-review.json"
_CACHE_TTL   = 30  # days

_TLDS = [".com", ".ai", ".io", ".co", ".app", ".dev", ".org", ".net", ".tech", ".inc"]

_PRIVACY_PATHS = [
    "/privacy-policy",
    "/privacy",
    "/legal/privacy",
    "/legal/privacy-policy",
    "/trust/privacy",
    "/policies/privacy",
    "/policy/privacy",
    "/en/privacy",
    "/en/legal/privacy",
    "/company/privacy",
    "/about/privacy",
    "/legal",
]

_DPA_PATHS = [
    "/dpa",
    "/data-processing-agreement",
    "/data-processing-addendum",
    "/legal/dpa",
    "/legal/data-processing-agreement",
    "/gdpr/dpa",
    "/trust/dpa",
    "/gdpr",
]

_AGGREGATORS = frozenset({
    "iubenda.com",
    "termly.io",
    "privacypolicies.com",
    "cookiebot.com",
    "getterms.io",
    "termageddon.com",
    "privacypolicyonline.com",
    "websitepolicies.com",
    "freeprivacypolicy.com",
})

_LEGAL_SUFFIXES = frozenset({
    "inc", "corp", "llc", "ltd", "ag", "gmbh", "bv", "sas", "sa",
    "plc", "nv", "pty", "pte",
})
_DESCRIPTORS = frozenset({
    "ai", "technologies", "technology", "systems", "solutions",
    "software", "platform", "labs", "group", "global", "digital",
    "cloud", "data", "analytics",
})

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "identity",
}


# ─────────────────────────────────────────────────────────────────────
# Stage 0 — Name normalisation
# ─────────────────────────────────────────────────────────────────────

def _normalise(vendor: str) -> tuple[str, list[str]]:
    """
    Return (primary_slug, candidate_slugs) for a vendor string.

    "Anecdotes AI Inc"  → ("anecdotes", ["anecdotes"])
    "HubSpot"           → ("hubspot",   ["hubspot", "hub"])
    "acme.com"          → ("acme",      ["acme"])
    """
    v = vendor.strip()

    # Strip URL components
    v = re.sub(r"^https?://", "", v)
    v = v.split("/")[0].split("?")[0]
    v = re.sub(r"^www\.", "", v, flags=re.IGNORECASE)

    # Already a bare domain — use base name only
    if "." in v and " " not in v:
        base = re.sub(r"[^a-z0-9]", "", v.split(".")[0].lower())
        return base, [base]

    raw_words = re.sub(r"[^a-zA-Z0-9 ]", " ", v).split()
    filtered  = [w for w in raw_words if w.lower() not in _LEGAL_SUFFIXES | _DESCRIPTORS]
    if not filtered:
        filtered = raw_words

    first   = re.sub(r"[^a-z0-9]", "", filtered[0].lower()) if filtered else ""
    primary = re.sub(r"[^a-z0-9]", "", "".join(filtered).lower())

    # CamelCase split: "HubSpot" → first part "hub"
    camel_parts = re.sub(r"([A-Z][a-z]+)", r" \1", re.sub(r"([A-Z]+)", r" \1", v)).split()
    camel_first = re.sub(r"[^a-z0-9]", "", camel_parts[0].lower()) if camel_parts else ""

    candidates: list[str] = []
    for c in [first, primary, camel_first]:
        if c and c not in candidates and len(c) >= 2:
            candidates.append(c)

    if not candidates:
        candidates = [re.sub(r"[^a-z0-9]", "", v.lower()[:20])]

    return candidates[0], candidates


# ─────────────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────────────

def _load_cache() -> dict:
    if not _CACHE_PATH.exists():
        return {}
    try:
        return json.loads(_CACHE_PATH.read_text())
    except Exception:
        return {}


def _save_cache(cache: dict) -> None:
    _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _CACHE_PATH.write_text(json.dumps(cache, indent=2))


def _check_cache(slug: str) -> dict | None:
    entry = _load_cache().get(slug)
    if not entry:
        return None
    try:
        cached_at = datetime.datetime.fromisoformat(entry["cached_at"])
        if (datetime.datetime.now() - cached_at).days <= _CACHE_TTL:
            return entry
    except Exception:
        pass
    return None


def _write_cache(slug: str, domain: str, policy_url: str, stage: str) -> None:
    cache = _load_cache()
    cache[slug] = {
        "domain": domain,
        "policy_url": policy_url,
        "resolved_via": stage,
        "cached_at": datetime.datetime.now().isoformat(),
    }
    _save_cache(cache)


# ─────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────

def _is_aggregator(url: str) -> bool:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
        return any(agg in host for agg in _AGGREGATORS)
    except Exception:
        return False


def head_request(url: str, timeout: int = 6) -> int | None:
    """Return the final HTTP status code for a HEAD request, or None on error."""
    req = urllib.request.Request(url, method="HEAD", headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status
    except urllib.error.HTTPError as exc:
        return exc.code
    except Exception:
        return None


def _tiny_get(url: str, max_bytes: int = 4096, timeout: int = 6) -> str | None:
    """Return the first max_bytes of a URL as text, or None on failure."""
    req = urllib.request.Request(url, headers=_HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read(max_bytes).decode("utf-8", errors="replace")
    except Exception:
        return None


def _verify_url(url: str, timeout: int = 6) -> bool:
    status = head_request(url, timeout=timeout)
    return status is not None and status < 400


def _probe_privacy_paths(domain: str) -> str | None:
    """Try each known privacy path on domain; return first live URL."""
    for path in _PRIVACY_PATHS:
        url = f"https://{domain}{path}"
        if _verify_url(url, timeout=5):
            return url
    return None


def probe_dpa_paths(domain: str) -> str | None:
    """Try each known DPA path on domain; return first live URL."""
    for path in _DPA_PATHS:
        url = f"https://{domain}{path}"
        if _verify_url(url, timeout=5):
            return url
    return None


# ─────────────────────────────────────────────────────────────────────
# Stage 1 — DuckDuckGo web search
# ─────────────────────────────────────────────────────────────────────

def _ddg_search(query: str, n: int = 12) -> list[str]:
    """Return up to n result URLs from a DuckDuckGo HTML search."""
    encoded = urllib.parse.quote(query)
    url = f"https://html.duckduckgo.com/html/?q={encoded}"
    req = urllib.request.Request(url, headers={**_HEADERS, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read(500_000).decode("utf-8", errors="replace")
    except Exception:
        return []

    # Primary: DDG encodes result URLs as uddg= params in redirect hrefs
    urls: list[str] = []
    for raw in re.findall(r"uddg=([^&\">\s]+)", html):
        decoded = urllib.parse.unquote(raw)
        if decoded.startswith("http"):
            urls.append(decoded)
        if len(urls) >= n:
            break

    # Fallback: extract result__url display text e.g. "company.com/privacy-policy"
    if not urls:
        for display in re.findall(r'class="result__url"[^>]*>\s*([^\s<]+)', html)[:n]:
            d = display.strip()
            urls.append(d if d.startswith("http") else f"https://{d}")

    return urls


def _score_search_result(url: str, slug: str) -> int:
    """Score a search URL. Returns -100 for disqualified, higher = better."""
    if _is_aggregator(url):
        return -100
    url_lower = url.lower()
    if "privacy" not in url_lower:
        return -1
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
        path = urllib.parse.urlparse(url).path.lower()
    except Exception:
        return 0
    score = 0
    if slug in host:
        score += 20
    for pp in ("/privacy-policy", "/legal/privacy", "/policies/privacy"):
        if path.startswith(pp):
            score += 5
            break
    if "/privacy" in path:
        score += 3
    return score


def _stage1_search(vendor: str, slug: str) -> str | None:
    for query in (f'"{vendor}" privacy policy', f"{vendor} privacy policy"):
        results = _ddg_search(query)
        scored = sorted(
            ((r, _score_search_result(r, slug)) for r in results),
            key=lambda x: x[1],
            reverse=True,
        )
        for url, score in scored:
            if score > 0 and _verify_url(url):
                return url
    return None


# ─────────────────────────────────────────────────────────────────────
# Stage 2 — Multi-TLD probe
# ─────────────────────────────────────────────────────────────────────

def _stage2_tld_probe(
    candidates: list[str],
    tried_domains: list[str],
) -> tuple[str, str] | None:
    """
    Probe slug+TLD combos with HEAD, verify ownership with a tiny GET,
    then probe standard privacy paths.

    Returns (domain, policy_url) or None.
    Appends any verified live domains to tried_domains for Stage 4.
    """
    for slug in candidates:
        for tld in _TLDS:
            domain = f"{slug}{tld}"
            # Quick liveness check
            status = head_request(f"https://{domain}", timeout=4)
            if status is None or status >= 400:
                continue

            # Verify ownership: slug must appear in the homepage content
            content = _tiny_get(f"https://{domain}", max_bytes=4096, timeout=5)
            if content is None or slug not in content.lower():
                continue

            if domain not in tried_domains:
                tried_domains.append(domain)

            policy_url = _probe_privacy_paths(domain)
            if policy_url:
                return domain, policy_url

            # Valid domain, no standard path — record for Stage 4 and
            # keep looking (different TLD might be the real company site)

    return None


# ─────────────────────────────────────────────────────────────────────
# Stage 3 — AI domain reasoning
# ─────────────────────────────────────────────────────────────────────

def _stage3_ai_reason(
    vendor: str,
    tried_domains: list[str],
    provider,
) -> str | None:
    """Ask the LLM to infer the correct domain. Returns a bare domain or None."""
    if provider is None:
        return None

    tried_str = ", ".join(tried_domains) if tried_domains else "(none tried)"
    prompt = (
        f"The company '{vendor}' has a website. "
        f"I tried these domains and none returned a valid privacy policy: {tried_str}\n\n"
        f"What is the most likely domain for this company? "
        f"Tech/AI companies often use .ai or .io, developer tools use .dev, "
        f"newer startups use .co. If this is a well-known company, reason about "
        f"what you know about their actual domain.\n\n"
        f'Respond with a JSON object, e.g.: {{"domain": "anecdotes.ai"}}'
    )
    try:
        result = provider.complete_json(prompt=prompt, max_tokens=64)
        domain = str(result.get("domain", "")).strip().lower()
        if domain and re.match(r"^[a-z0-9][a-z0-9.-]+\.[a-z]{2,}$", domain):
            return domain
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────
# Stage 4 — Homepage link scrape
# ─────────────────────────────────────────────────────────────────────

def _stage4_homepage_scrape(domain: str) -> str | None:
    """Fetch the homepage via Jina and extract any privacy-containing link."""
    try:
        from core.tools.fetch import _fetch_jina
        raw = _fetch_jina(f"https://{domain}")
    except Exception:
        return None

    found: list[str] = []

    # Full URLs with "privacy" in them
    found.extend(re.findall(
        r"https?://[^\s\"'<>]+privacy[^\s\"'<>]*",
        raw,
        re.IGNORECASE,
    ))

    # Relative hrefs
    for rel in re.findall(r'href="(/[^"]*privacy[^"]*)"', raw, re.IGNORECASE):
        found.append(f"https://{domain}{rel}")

    seen: set[str] = set()
    for url in found:
        if url in seen or _is_aggregator(url):
            continue
        seen.add(url)
        if _verify_url(url, timeout=5):
            return url

    return None


# ─────────────────────────────────────────────────────────────────────
# Stage 5 — Manual review flag
# ─────────────────────────────────────────────────────────────────────

def _stage5_flag(vendor: str, tried_domains: list[str]) -> None:
    entries: list[dict] = []
    if _REVIEW_PATH.exists():
        try:
            entries = json.loads(_REVIEW_PATH.read_text())
        except Exception:
            pass
    entries.append({
        "vendor": vendor,
        "tried_domains": tried_domains,
        "timestamp": datetime.datetime.now().isoformat(),
        "reason": "all_stages_failed",
    })
    _REVIEW_PATH.parent.mkdir(parents=True, exist_ok=True)
    _REVIEW_PATH.write_text(json.dumps(entries, indent=2))


# ─────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────

def discover_policy_url(
    vendor: str,
    provider=None,
    verbose_cb: Callable[[str], None] | None = None,
) -> str | None:
    """
    Discover the vendor's privacy policy URL using staged fallback.

    Returns a URL string, or None if all stages fail.
    Successful results are cached in ~/.bandit/domain-cache.json.
    """

    def vp(stage: str, sym: str, msg: str) -> None:
        if verbose_cb:
            verbose_cb(f"  {stage:<26}{sym}  {msg}")

    vendor = vendor.strip()

    # ── Fast path A: caller gave a direct URL ─────────────────────────
    if re.match(r"^https?://", vendor):
        parsed_path = urllib.parse.urlparse(vendor).path.rstrip("/")
        if parsed_path and _verify_url(vendor):
            # Specific page URL — use it directly
            vp("Input URL", "✓", vendor)
            return vendor
        # Bare site root — probe known privacy paths on that domain
        domain = urllib.parse.urlparse(vendor).netloc.lstrip("www.")
        url = _probe_privacy_paths(domain)
        if url:
            vp("Input domain probe", "✓", url)
            return url

    # ── Fast path B: caller gave a bare domain ────────────────────────
    if "." in vendor and " " not in vendor:
        domain = re.sub(r"^www\.", "", vendor, flags=re.IGNORECASE)
        url = _probe_privacy_paths(domain)
        if url:
            vp("Domain path probe", "✓", url)
            return url

    # ── Stage 0: normalise ────────────────────────────────────────────
    slug, candidates = _normalise(vendor)
    tried_domains: list[str] = []

    # ── Cache check ───────────────────────────────────────────────────
    cached = _check_cache(slug)
    if cached:
        vp("Cache", "✓", f"[{cached['resolved_via']}]  {cached['policy_url']}")
        return cached["policy_url"]

    # ── Stage 1: DuckDuckGo search ────────────────────────────────────
    vp("Stage 1 (search)", "…", f'"{vendor} privacy policy"')
    url = _stage1_search(vendor, slug)
    if url:
        vp("Stage 1 (search)", "✓", url)
        domain = urllib.parse.urlparse(url).netloc.lstrip("www.")
        _write_cache(slug, domain, url, "stage1_search")
        return url
    vp("Stage 1 (search)", "✗", "no verified result")

    # ── Stage 2: TLD probe ────────────────────────────────────────────
    vp("Stage 2 (TLD probe)", "…", f"candidates: {', '.join(candidates)}")
    result = _stage2_tld_probe(candidates, tried_domains)
    if result:
        domain, url = result
        vp("Stage 2 (TLD probe)", "✓", url)
        _write_cache(slug, domain, url, "stage2_tld_probe")
        return url
    tried_str = ", ".join(tried_domains) or "none"
    vp("Stage 2 (TLD probe)", "✗", f"tried: {tried_str}")

    # ── Stage 3: AI domain reasoning ──────────────────────────────────
    if provider is not None:
        vp("Stage 3 (AI reason)", "…", "asking LLM to infer domain")
        domain = _stage3_ai_reason(vendor, tried_domains, provider)
        if domain:
            vp("Stage 3 (AI reason)", "✓", f"domain: {domain}")
            if domain not in tried_domains:
                tried_domains.append(domain)
            url = _probe_privacy_paths(domain)
            if url:
                vp("Stage 3 (path probe)", "✓", url)
                _write_cache(slug, domain, url, "stage3_ai_reason")
                return url
        vp("Stage 3 (AI reason)", "✗", "no valid domain inferred")

    # ── Stage 4: Homepage link scrape ─────────────────────────────────
    for domain in tried_domains:
        vp("Stage 4 (link scrape)", "…", domain)
        url = _stage4_homepage_scrape(domain)
        if url:
            vp("Stage 4 (link scrape)", "✓", url)
            _write_cache(slug, domain, url, "stage4_homepage_scrape")
            return url
    vp("Stage 4 (link scrape)", "✗", "no privacy link found on any known domain")

    # ── Stage 5: Manual review ────────────────────────────────────────
    _stage5_flag(vendor, tried_domains)
    vp("Stage 5 (failed)", "⚠", f"logged to {_REVIEW_PATH}")
    return None
