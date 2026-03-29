"""
Privacy Bandit — vendor privacy policy assessment agent.

Flow
----
Phase 1 — Discovery (deterministic Python, no LLM)
  Staged fallback: DDG search → TLD probe → AI reasoning → link scrape.
  See core/tools/discover.py for full stage documentation.
  Successful results are cached in ~/.bandit/domain-cache.json.

Phase 2 — Signal extraction (single LLM call)
  The retrieved policy text is passed to build_extraction_prompt().
  The LLM returns a flat JSON object with signal keys.

Phase 3 — Scoring (deterministic, no LLM)
  score_vendor() processes the signals and returns a fully scored
  AssessmentResult.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from core.agents.base_bandit import BaseBandit
from core.llm.base import BaseLLMProvider
from core.scoring.rubric import (
    RUBRIC,
    AssessmentResult,
    build_extraction_prompt,
    score_vendor,
)
from core.tools.fetch import fetch_url
from core.tools.parse import html_to_text


@dataclass
class FetchedSource:
    """Metadata for a single page retrieved during assessment."""
    url: str
    chars: int
    via: str   # "direct" or "jina"


@dataclass
class PrivacyAssessment:
    """Assessment result plus provenance — which pages were analysed."""
    result: AssessmentResult
    sources: list[FetchedSource] = field(default_factory=list)


class PrivacyBandit(BaseBandit):
    """Assess a vendor's privacy practices against the 8-dimension rubric."""

    _MIN_PARSED_CHARS = 500

    def __init__(
        self,
        provider: BaseLLMProvider,
        on_progress: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(provider)
        self._fetched_pages: dict[str, str] = {}
        self._fetch_meta: list[FetchedSource] = []
        self._on_progress = on_progress

    def _progress(self, msg: str) -> None:
        if self._on_progress:
            self._on_progress(msg)

    # ── Fetch helper ──────────────────────────────────────────────────

    def _fetch(self, url: str) -> str:
        """Fetch, parse, cache, and return clean text for a URL."""
        if url in self._fetched_pages:
            return self._fetched_pages[url]

        raw, source = fetch_url(url)
        text = html_to_text(raw)

        # JS-rendered shell check — retry via Jina if text is sparse
        if len(text) < self._MIN_PARSED_CHARS and source == "direct":
            try:
                from core.tools.fetch import _fetch_jina
                raw2 = _fetch_jina(url)
                text2 = html_to_text(raw2)
                if len(text2) > len(text):
                    text, source = text2, "jina"
            except Exception:
                pass

        self._fetched_pages[url] = text
        self._fetch_meta.append(FetchedSource(url=url, chars=len(text), via=source))
        return text

    # ── Signal reshaping ──────────────────────────────────────────────

    @staticmethod
    def _reshape_signals(raw_json: dict) -> tuple[dict[str, dict[str, bool]], list[str]]:
        """Reshape flat signal dict into per-dimension dicts for score_vendor()."""
        signals: dict = raw_json.get("signals", {})
        art28: dict   = raw_json.get("art28_checklist", {})
        frameworks: dict = raw_json.get("framework_certifications", {})

        per_dim: dict[str, dict[str, bool]] = {}
        for dim_key in RUBRIC:
            prefix = dim_key.lower() + "_"
            per_dim[dim_key] = {
                k: bool(v) for k, v in signals.items() if k.startswith(prefix)
            }

        per_dim.setdefault("D8", {}).update({k: bool(v) for k, v in art28.items()})

        return per_dim, [k for k, v in frameworks.items() if v]

    # ── Main assess method ────────────────────────────────────────────

    @staticmethod
    def _detect_input_type(vendor: str) -> str:
        """Return 'direct URL', 'domain', or 'company name'."""
        if "://" in vendor:
            return "direct URL"
        if "." in vendor and " " not in vendor:
            return "domain"
        return "company name"

    def assess(self, vendor: str) -> PrivacyAssessment:
        """Run a full privacy assessment for a vendor.

        Parameters
        ----------
        vendor:
            Vendor name (e.g. "Acme Corp"), domain (e.g. "acme.com"),
            or full URL (e.g. "https://acme.com/privacy-policy").

        Returns
        -------
        PrivacyAssessment
            Scored assessment with all 8 dimensions plus source provenance.

        Raises
        ------
        RuntimeError
            If no policy content could be retrieved.
        """
        import urllib.parse
        from core.tools.discover import discover_policy_url, probe_dpa_paths

        self._fetched_pages = {}
        self._fetch_meta = []

        vendor = vendor.strip()

        # ── Input type detection ──────────────────────────────────────
        input_type = self._detect_input_type(vendor)
        self._progress(f"Phase 1/3  Input type:  {input_type:<16}({vendor})")

        # ── Phase 1: Discovery ────────────────────────────────────────
        if input_type == "direct URL":
            # Skip all discovery — use the URL exactly as given
            self._progress("Phase 1/3  Direct URL — skipping discovery…")
            policy_url = vendor
        else:
            self._progress(f"Phase 1/3  Discovering privacy policy for {vendor}…")
            policy_url = discover_policy_url(
                vendor,
                provider=self.provider,
                verbose_cb=self._on_progress,
            )

        if not policy_url:
            raise RuntimeError(
                f"Could not locate a privacy policy for {vendor!r}. "
                f"Logged to ~/.bandit/manual-review.json for follow-up."
            )

        self._progress("Phase 1/3  Fetching policy…")
        self._fetch(policy_url)

        # Also try to fetch the DPA from the same domain
        domain = urllib.parse.urlparse(policy_url).netloc.lstrip("www.")
        dpa_url = probe_dpa_paths(domain)
        if dpa_url:
            self._progress(f"Phase 1/3  Found DPA — fetching…")
            self._fetch(dpa_url)

        policy_text = "\n\n---\n\n".join(self._fetched_pages.values())
        if not policy_text.strip():
            raise RuntimeError(
                f"Could not retrieve any content from {policy_url}"
            )

        # ── Phase 2: Signal extraction ────────────────────────────────
        self._progress(
            f"Phase 2/3  Extracting signals from {len(self._fetch_meta)} page(s)…"
        )
        extraction_prompt = build_extraction_prompt(vendor, policy_text)
        raw_json = self.provider.complete_json(
            prompt=extraction_prompt,
            max_tokens=2048,
        )

        # ── Phase 3: Deterministic scoring ───────────────────────────
        self._progress("Phase 3/3  Scoring against rubric…")
        per_dim, fw_list = self._reshape_signals(raw_json)
        result = score_vendor(
            vendor_name=vendor,
            evidence=per_dim,
            extracted_text=policy_text,
            framework_evidence=fw_list,
        )

        return PrivacyAssessment(result=result, sources=list(self._fetch_meta))
