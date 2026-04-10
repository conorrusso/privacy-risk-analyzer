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
from core.agents.legal_bandit import LegalBandit
from core.llm.base import BaseLLMProvider
from core.reports.legal_report import generate_legal_brief
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
    def _translate_dpa_signals(signals: dict) -> dict:
        """Map granular d8_art28_* DPA extraction signals to aggregate D8 rubric signal names.

        The DPA extraction prompt returns per-provision booleans (d8_art28_*).
        The D8 rubric checks aggregate signals (d8_all_art28_provisions, etc.).
        Without this translation, DPA signals never reach D8 scoring.
        """
        translated: dict = {}

        # 8 core Art.28(3)(a)–(h) provisions
        art28_core = [
            signals.get("d8_art28_controller_obligations"),  # 3a documented instructions
            signals.get("d8_art28_confidentiality"),         # 3b confidentiality
            signals.get("d8_art28_security_measures"),       # 3c security measures
            signals.get("d8_art28_sub_processor_approval"),  # 3d sub-processing
            signals.get("d8_art28_assistance_dsars"),        # 3e DSAR assistance
            signals.get("d8_art28_audit_rights"),            # 3f audit/inspection
            signals.get("d8_art28_deletion_return"),         # 3g deletion/return
            signals.get("d8_art28_assistance_breach"),       # 3h breach assistance
        ]
        present_count = sum(1 for p in art28_core if p)

        if present_count >= 8:
            translated["d8_all_art28_provisions"] = True
            translated["d8_most_art28_provisions"] = True
        elif present_count >= 5:
            translated["d8_most_art28_provisions"] = True

        # Processing annex exists — subject matter + data types + data subjects defined
        if (signals.get("d8_art28_subject_matter") and
                signals.get("d8_art28_data_types") and
                signals.get("d8_art28_data_subjects")):
            translated["d8_processing_annex_exists"] = True

        # Detailed annex — also includes duration and nature/purpose
        if (translated.get("d8_processing_annex_exists") and
                signals.get("d8_art28_duration") and
                signals.get("d8_art28_nature_purpose")):
            translated["d8_processing_annex_detailed"] = True

        # TOMs in annex — security measures described with specificity
        if signals.get("d8_art28_security_measures_specific"):
            translated["d8_toms_in_annex"] = True

        # Measurable SLAs — breach SLA hours AND deletion timeframe both numeric
        breach_sla = signals.get("d5_breach_notification_sla_hours")
        deletion_days = signals.get("d7_deletion_timeframe_days")
        if (breach_sla and isinstance(breach_sla, (int, float)) and int(breach_sla) > 0
                and deletion_days and isinstance(deletion_days, (int, float))
                and int(deletion_days) > 0):
            translated["d8_measurable_slas"] = True

        # International transfers specified — mechanism named + SCC module number stated
        if signals.get("d4_transfer_mechanism_stated") and signals.get("d4_scc_module_specified"):
            translated["d8_international_transfers_specified"] = True

        return translated

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

    def assess(
        self,
        vendor: str,
        docs_folder: str = None,
        integration_context: str | None = None,
    ) -> PrivacyAssessment:
        """Run a full privacy assessment for a vendor.

        Parameters
        ----------
        vendor:
            Vendor name (e.g. "Acme Corp"), domain (e.g. "acme.com"),
            or full URL (e.g. "https://acme.com/privacy-policy").
        docs_folder:
            Optional path to a local folder containing vendor documents
            (DPA, MSA, SOC 2, etc.) for deeper scoring.

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

        import re as _re
        vendor = vendor.strip()[:200]
        vendor = _re.sub(r"[^\w\s\-\.\(\)/:]", "", vendor).strip()
        if not vendor:
            raise ValueError("Vendor name is empty after sanitisation.")

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

        # ── Document ingestion (optional) ────────────────────────────
        documents_assessed: list[str] = []
        ready_docs: list = []
        all_doc_signals: dict = {}
        signal_sources: dict = {}

        if docs_folder:
            from core.documents.ingestor import DocumentIngestor
            from core.documents.classifier import DocumentType
            from core.documents.doc_prompts import get_extraction_prompt

            self._progress("Phase 1/3  Ingesting vendor documents…")
            ingestor = DocumentIngestor(llm_provider=self.provider)
            try:
                manifest = ingestor.ingest_folder(docs_folder)
                ingestor.show_manifest(manifest)

                ready_docs = [
                    d for d in manifest.documents
                    if d.extraction_ok and d.doc_type != DocumentType.UNKNOWN
                ]
                documents_assessed = [d.file_name for d in ready_docs]

                # If a Privacy Policy PDF is in Drive docs, use its text
                # instead of the JS-rendered web fetch — more reliable
                _policy_doc = next(
                    (d for d in ready_docs
                     if d.doc_type == DocumentType.PRIVACY_POLICY
                     and len(d.text) > 2000),
                    None
                )
                if _policy_doc:
                    policy_text = _policy_doc.text
                    self._progress(
                        f"Phase 1/3  Using Drive PDF for policy signals: "
                        f"{_policy_doc.file_name}"
                    )

                for doc in ready_docs:
                    self._progress(
                        f"Phase 2/3  Extracting signals from {doc.file_name}…"
                    )
                    doc_prompt = get_extraction_prompt(
                        doc.doc_type, vendor, doc.text
                    )
                    try:
                        doc_signals = self.provider.complete_json(
                            prompt=doc_prompt,
                            max_tokens=2048,
                        )
                        # Accumulate truthy doc signals only.
                        # Never store False/null — documents add evidence,
                        # they never remove it.
                        for key, value in doc_signals.items():
                            if value and not all_doc_signals.get(key):
                                all_doc_signals[key] = value
                                signal_sources[key] = doc.file_name
                    except Exception:
                        pass
            except Exception:
                pass

        # ── Phase 2: Signal extraction ────────────────────────────────
        self._progress(
            f"Phase 2/3  Extracting signals from {len(self._fetch_meta)} page(s)…"
        )
        extraction_prompt = build_extraction_prompt(vendor, policy_text)
        if integration_context:
            extraction_prompt = extraction_prompt + "\n\n" + integration_context
        raw_json = self.provider.complete_json(
            prompt=extraction_prompt,
            max_tokens=2048,
        )

        # Merge document signals into raw_json signals block.
        # Doc signals fill gaps — they never overwrite a True policy signal
        # with False/null, and never add a False signal for a new key.
        if all_doc_signals:
            policy_signals = raw_json.get("signals", {})
            for key, value in all_doc_signals.items():
                if value and not policy_signals.get(key):
                    policy_signals[key] = value
                    signal_sources.setdefault(key, "document")
            raw_json["signals"] = policy_signals

            # Merge art28_checklist if DPA signals present
            art28_keys = {
                k: v for k, v in all_doc_signals.items()
                if k.startswith("d8_art28_")
            }
            if art28_keys:
                existing_art28 = raw_json.get("art28_checklist", {})
                for key, value in art28_keys.items():
                    art28_key = key[len("d8_art28_"):]
                    if art28_key not in existing_art28 or (
                        value and not existing_art28.get(art28_key)
                    ):
                        existing_art28[art28_key] = value
                raw_json["art28_checklist"] = existing_art28

            # Translate granular DPA provision signals → aggregate D8 rubric signal names
            # (d8_art28_* → d8_all_art28_provisions, d8_processing_annex_exists, etc.)
            d8_translated = self._translate_dpa_signals(all_doc_signals)
            if d8_translated:
                _sigs = raw_json.setdefault("signals", {})
                for k, v in d8_translated.items():
                    if k not in _sigs or (v and not _sigs.get(k)):
                        _sigs[k] = v

            # Translate d8_art28_assistance_dsars → D3 signal so DPA
            # DSAR assistance commitment registers in D3 scoring
            if all_doc_signals.get("d8_art28_assistance_dsars"):
                _sigs = raw_json.setdefault("signals", {})
                _sigs.setdefault("d3_dsar_procedure_documented", True)
                _sigs.setdefault("d3_some_rights_listed", True)

            # Build framework_certifications from successfully extracted
            # certification documents. The policy extraction prompt only
            # sees the web page — it cannot detect certs from PDFs.
            _doc_types = {d.doc_type for d in ready_docs if d.extraction_ok}
            _fw_certs = raw_json.setdefault("framework_certifications", {})

            if DocumentType.SOC2_TYPE2 in _doc_types:
                if all_doc_signals.get("privacy_tsc_included"):
                    _fw_certs.setdefault("soc2_type2_privacy_tsc", True)
                else:
                    _fw_certs.setdefault("soc2_type2_security_only", True)

            if DocumentType.ISO27001 in _doc_types:
                _fw_certs.setdefault("iso_27001_only", True)
                # ISO 27701 extension detected inside the ISO 27001 cert
                if all_doc_signals.get("iso27701_extension"):
                    _fw_certs.setdefault("iso_27701_certified", True)

            if DocumentType.ISO27701 in _doc_types:
                _fw_certs.setdefault("iso_27701_certified", True)

        # ── Evidence confidence ───────────────────────────────────────
        evidence_confidence = self._calculate_evidence_confidence(
            fetch_ok=bool(policy_text.strip()),
            extracted_text=policy_text,
        )

        # ── Vendor function profiling ─────────────────────────────────
        vendor_functions = None
        try:
            from core.profiles.auto_detect import detector
            from core.profiles.vendor_cache import profile_cache
            import datetime as _dt

            domain_for_detect = domain if "domain" in dir() else None
            cached_profile = profile_cache.get(vendor)
            if cached_profile:
                from core.profiles.vendor_functions import VendorFunction
                vendor_functions = [VendorFunction(f) for f in cached_profile.functions]
            else:
                detect_result = detector.detect(vendor, domain=domain_for_detect)
                vendor_functions = detect_result.functions
                # Cache the detection result
                from core.profiles.vendor_cache import VendorProfile
                vp = VendorProfile(
                    vendor_name=vendor,
                    vendor_slug=detect_result.vendor_slug,
                    functions=[f.value for f in detect_result.functions],
                    detection_method=detect_result.method,
                    last_updated=_dt.date.today().isoformat(),
                )
                profile_cache.save(vendor, vp)
        except Exception:
            vendor_functions = None

        # ── Phase 3: Deterministic scoring ───────────────────────────
        self._progress("Phase 3/3  Scoring against rubric…")
        per_dim, fw_list = self._reshape_signals(raw_json)

        from core.config import BanditConfig, get_profile_label, load_config
        config = load_config()
        bandit_cfg = BanditConfig(config)
        profile_weights = bandit_cfg.get_weights(vendor_functions=vendor_functions)
        auto_escalate_triggers = bandit_cfg.get_auto_escalate_triggers()

        # Apply intake weight modifiers if vendor profile has intake data
        _vp = None
        try:
            from core.profiles.vendor_cache import profile_cache as _pc
            _vp = _pc.get(vendor)
            if _vp and _vp.intake_completed:
                from core.profiles.intake import apply_intake_weight_modifiers
                org_profile = bandit_cfg.get_profile()
                profile_weights = apply_intake_weight_modifiers(
                    profile_weights, _vp, org_profile
                )
        except Exception:
            pass

        dpa_found = any(
            d.doc_type == DocumentType.DPA and d.extraction_ok and d.char_count > 5000
            for d in ready_docs
        )
        scored_doc_types = {
            d.doc_type for d in ready_docs if d.extraction_ok
        }
        assessment_scope = (
            "policy_and_documents"
            if scored_doc_types
            else "public_policy_only"
        )

        result = score_vendor(
            vendor_name=vendor,
            evidence=per_dim,
            extracted_text=policy_text,
            framework_evidence=fw_list,
            profile_weights=profile_weights,
            auto_escalate_triggers=auto_escalate_triggers,
            assessment_scope=assessment_scope,
            dpa_available=dpa_found,
        )

        if config:
            result.active_profile = get_profile_label(config)

        result.documents_assessed = documents_assessed
        result.signal_sources = signal_sources

        # Attach replaceability from vendor profile
        try:
            from core.profiles.intake import normalise_sole_source
            _sole = getattr(_vp, "sole_source", None) if _vp else None
            result.sole_source = normalise_sole_source(_sole)
            # Escalate if HIGH risk and not replaceable
            if (result.risk_tier == "HIGH"
                    and result.sole_source == "not_replaceable"):
                result.escalation_required = True
                result.escalation_reasons.append(
                    "Vendor is HIGH risk with no viable "
                    "alternative — limited ability to "
                    "enforce contract improvements or switch"
                )
        except Exception:
            result.sole_source = None

        # ── Phase 4: Legal Bandit (contract gap analysis) ─────────────
        legal_result = None
        if ready_docs:
            self._progress("Phase 3/4  Legal Bandit — contract gap analysis…")
            legal_bandit = LegalBandit(self.provider)

            # Build flat policy_scores dict for Legal Bandit
            policy_scores = {
                dim: dr.capped_score
                for dim, dr in result.dimensions.items()
            }

            # Build flat policy_signals for conflict detection
            flat_signals: dict = {}
            for dim_signals in per_dim.values():
                flat_signals.update(dim_signals)

            try:
                legal_result = legal_bandit.assess(
                    vendor_name=vendor,
                    documents=ready_docs,
                    policy_signals=flat_signals,
                    policy_scores=policy_scores,
                )
            except Exception as _lb_err:
                import logging as _log
                _log.getLogger("bandit").warning(
                    f"Legal Bandit failed for {vendor}: {_lb_err}"
                    " — main assessment still saved."
                )
                self._progress(
                    f"⚠ Legal Bandit failed ({type(_lb_err).__name__})"
                    " — GRC report saved. Re-run bandit legal"
                    f' "{vendor}" --drive to retry the contract'
                    " analysis separately."
                )

        if legal_result:
            # Update dimension scores from contract assessment
            for dim_score in legal_result.dimension_scores:
                if dim_score.score_changed and dim_score.dimension in result.dimensions:
                    result.dimensions[dim_score.dimension].capped_score = (
                        dim_score.final_score
                    )

            # Recalculate weighted average with updated scores
            from core.scoring.rubric import RUBRIC, classify_risk
            _included = [
                k for k, dr in result.dimensions.items()
                if not dr.is_excluded
            ]
            if _included:
                total_weight = sum(
                    result.dimensions[k].weight for k in _included
                )
                weighted_sum = sum(
                    result.dimensions[k].capped_score
                    * result.dimensions[k].weight
                    for k in _included
                )
                result.weighted_average = (
                    round(weighted_sum / total_weight, 1)
                    if total_weight else result.weighted_average
                )
                result.risk_tier = classify_risk(result.weighted_average)

            # Merge escalation from Legal Bandit
            if legal_result.escalation_required:
                result.escalation_required = True
                result.escalation_reasons.extend(
                    legal_result.escalation_reasons
                )

            # Store legal result on assessment result
            result.legal_bandit_result = legal_result
        elif ready_docs:
            self._progress(
                "Phase 3/4  Legal Bandit — no DPA or MSA found, skipped."
            )

        return PrivacyAssessment(result=result, sources=list(self._fetch_meta))

    # ── Evidence confidence ───────────────────────────────────────────

    @staticmethod
    def _calculate_evidence_confidence(
        fetch_ok: bool,
        extracted_text: str,
    ) -> float:
        """Return a 0.0–1.0 confidence score for the evidence quality.

        Based on:
        - Whether a page was successfully fetched
        - Total text length (proxy for policy completeness)
        - Presence of key privacy policy indicators
        """
        if not fetch_ok or not extracted_text.strip():
            return 0.0

        text_len = len(extracted_text)
        score = 0.0

        # Length component (0.0–0.5)
        if text_len >= 10_000:
            score += 0.5
        elif text_len >= 3_000:
            score += 0.3
        elif text_len >= 500:
            score += 0.1

        # Content indicators (0.0–0.5)
        text_lower = extracted_text.lower()
        indicators = [
            "privacy policy",
            "personal data",
            "data controller",
            "third part",
            "retain",
            "delete",
            "rights",
            "contact",
        ]
        hits = sum(1 for ind in indicators if ind in text_lower)
        score += min(0.5, hits * 0.065)

        return round(min(1.0, score), 2)
