"""
Bandit Rubric — Deterministic Privacy Risk Scoring Engine
==========================================================

Version : 1.0.0
Updated : 2026-03-27
License : MIT

Architecture
------------
1. An AI provider (any LLM) extracts structured *evidence* from vendor
   documents (privacy policy, DPA, public disclosures).
2. This module scores that evidence deterministically — the AI never
   assigns scores; Bandit does.

Evidence contract
-----------------
The AI must return a dict per dimension keyed by signal slugs
(see ``RUBRIC[dim]["levels"][n]["required_signals"]``).  Each signal
is ``True`` (present), ``False`` (absent), or a *string* when the
rubric needs to inspect literal policy language for red-flag matching.

Scoring algorithm
-----------------
For each dimension the engine walks levels 5 → 1 and awards the
*highest* level whose required signals are **all** satisfied.  Red-flag
phrases found in extracted text impose a *hard ceiling* on the score
(see ``red_flag_ceilings``).  D8 (DPA Completeness) can further cap
D2, D5, and D7 via the dependency ceiling rule.

Risk tier
---------
HIGH   : weighted_average < 2.5
MEDIUM : 2.5 ≤ weighted_average ≤ 3.5
LOW    : weighted_average > 3.5
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

__version__ = "1.0.0"

# ─────────────────────────────────────────────────────────────────────
# Risk-tier thresholds
# ─────────────────────────────────────────────────────────────────────
RISK_TIERS = {
    "HIGH": lambda avg: avg < 2.5,
    "MEDIUM": lambda avg: 2.5 <= avg <= 3.5,
    "LOW": lambda avg: avg > 3.5,
}


def classify_risk(weighted_average: float) -> str:
    """Return HIGH / MEDIUM / LOW for a weighted average score."""
    if weighted_average < 2.5:
        return "HIGH"
    if weighted_average <= 3.5:
        return "MEDIUM"
    return "LOW"


# ─────────────────────────────────────────────────────────────────────
# Red-flag phrase registry
# ─────────────────────────────────────────────────────────────────────
# Each entry: (compiled regex, affected dimensions, ceiling score,
#              short label for reports)

_RED_FLAGS: list[tuple[re.Pattern, list[str], int, str]] = []


def _rf(pattern: str, dims: list[str], ceiling: int, label: str):
    """Register a red-flag pattern."""
    _RED_FLAGS.append((re.compile(pattern, re.IGNORECASE), dims, ceiling, label))


# ── D1 Data Minimization ────────────────────────────────────────────
_rf(
    r"we may collect data as needed",
    ["D1"], 2,
    "Vague open-ended collection language",
)
_rf(
    r"improving our products and services",
    ["D1", "D6"], 2,
    "Undefined improvement purpose (CRITEO / Netflix precedent)",
)
_rf(
    r"data may be retained for legitimate business purposes",
    ["D1", "D7"], 2,
    "Unbounded retention (Amazon France €32M precedent)",
)

# ── D2 Sub-processor Management ─────────────────────────────────────
_rf(
    r"reasonable efforts to notify",
    ["D2"], 2,
    "Below Art. 28(2) standard for sub-processor notification",
)
_rf(
    r"we share data with third parties",
    ["D2"], 2,
    "Unspecified third-party sharing (Netflix €4.75M / WhatsApp €225M)",
)

# ── D5 Breach Notification ──────────────────────────────────────────
_rf(
    r"notify.{0,40}(as required by law|in accordance with applicable)",
    ["D5"], 2,
    "No specific breach notification commitment",
)
_rf(
    r"within a reasonable period",
    ["D5"], 2,
    "Undefined breach notification timeline",
)

# ── D6 AI/ML Usage ──────────────────────────────────────────────────
_rf(
    r"we may use.{0,30}data.{0,30}improve.{0,30}(products|services|models)",
    ["D6"], 2,
    "AI training bundled under generic improvement (CRITEO €40M / OpenAI €15M)",
)
_rf(
    r"by using our service.{0,20}you consent to.{0,20}(ai|training|model)",
    ["D6"], 2,
    "Bundled consent for AI training (GDPR Art. 7 / FTC guidance)",
)
_rf(
    r"industry.standard ai practices",
    ["D6"], 2,
    "No specificity on AI practices",
)
_rf(
    r"we reserve the right to update.{0,40}(ai|new uses)",
    ["D6"], 1,
    "Retroactive AI policy change (FTC Feb 2024 guidance / Everalbum)",
)
_rf(
    r"data.{0,20}(anonymized|anonymised) form.{0,30}machine learning",
    ["D6"], 3,
    "Anonymization claim without methodology (re-identification risk)",
)

# ── D7 Retention & Deletion ─────────────────────────────────────────
_rf(
    r"(retained|stored).{0,30}as (required|permitted) by (applicable |)law",
    ["D7"], 2,
    "Undefined legal retention (Netflix €4.75M precedent)",
)
_rf(
    r"retained indefinitely",
    ["D7"], 1,
    "Indefinite retention",
)
_rf(
    r"commercially reasonable efforts to delete",
    ["D7"], 2,
    "Non-committal deletion language",
)

# ── D8 DPA Completeness ─────────────────────────────────────────────
_rf(
    r"processor shall process.{0,40}in accordance with.{0,20}instructions",
    ["D8"], 3,
    "Verbatim Art. 28 restatement — EDPB says never sufficient",
)
_rf(
    r"(appropriate|reasonable|industry.standard) (security |)measures",
    ["D8"], 3,
    "Generic security clause (no enforceable standard)",
)
_rf(
    r"privacy shield",
    ["D4", "D8"], 2,
    "Outdated transfer mechanism (invalidated July 2020)",
)

# ── Cross-cutting ───────────────────────────────────────────────────
_rf(
    r"without undue delay(?!.{0,60}(hour|hr|day|business day))",
    ["D5", "D8"], 3,
    "No operational SLA beyond GDPR verbatim",
)


def scan_red_flags(
    extracted_text: str,
) -> list[dict[str, Any]]:
    """Return all red-flag matches found in raw extracted text.

    Each match dict: ``{"label", "dims", "ceiling", "match"}``
    """
    hits = []
    for pattern, dims, ceiling, label in _RED_FLAGS:
        m = pattern.search(extracted_text)
        if m:
            hits.append(
                {
                    "label": label,
                    "dims": dims,
                    "ceiling": ceiling,
                    "match": m.group(0)[:120],
                }
            )
    return hits


def red_flag_ceilings(
    hits: list[dict[str, Any]],
) -> dict[str, int]:
    """Collapse red-flag hits into per-dimension ceiling scores.

    Returns e.g. ``{"D1": 2, "D6": 1}`` — only dims with ceilings.
    """
    ceilings: dict[str, int] = {}
    for h in hits:
        for dim in h["dims"]:
            if dim not in ceilings:
                ceilings[dim] = h["ceiling"]
            else:
                ceilings[dim] = min(ceilings[dim], h["ceiling"])
    return ceilings


# ─────────────────────────────────────────────────────────────────────
# Rubric definition — 8 dimensions
# ─────────────────────────────────────────────────────────────────────
# Signal keys are stable identifiers referenced in the extraction
# prompt.  ``True`` = required present; ``False`` would mean required
# absent (not used currently).

RUBRIC: dict[str, dict[str, Any]] = {
    # ────────────────────────────────────────────────────────────────
    # D1 — DATA MINIMIZATION
    # ────────────────────────────────────────────────────────────────
    "D1": {
        "name": "Data Minimization",
        "weight": 1.0,
        "regulatory_basis": [
            "GDPR Art. 5(1)(c)",
            "CCPA/CPRA — CPPA Enforcement Advisory (Apr 2024)",
            "CJEU Schrems v Meta C-446/21 (Oct 2024)",
        ],
        "framework_refs": [
            "ISO 27701 Annex A — Privacy by design (minimization)",
            "SOC 2 Privacy TSC P3.1 — Collection Limitation",
            "NIST PF CT.DP-P4",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d1_categories_linked_to_purposes",
                    "d1_specific_retention_per_category",
                    "d1_automated_minimization_controls",
                    "d1_privacy_by_design_documented",
                    "d1_periodic_review_cycle",
                ],
                "description": (
                    "Automated enforcement of minimization policies. "
                    "Data inventory links categories to purposes with "
                    "periodic review. Privacy-by-design documentation."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d1_categories_linked_to_purposes",
                    "d1_specific_retention_per_category",
                    "d1_periodic_review_cycle",
                ],
                "description": (
                    "Documented data inventory linking categories to "
                    "purposes with periodic review and category-specific "
                    "retention."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d1_purposes_stated",
                    "d1_categories_listed",
                ],
                "description": (
                    "Collection purposes stated and data categories "
                    "listed, but no documented linkage or review cycle."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d1_purposes_stated",
                ],
                "description": (
                    "Purposes mentioned but vague. Language like 'we "
                    "may collect data as needed' or open-ended purposes "
                    "without category specificity."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No data minimization disclosure. No stated purposes "
                    "or categories. Language contradicts minimization."
                ),
            },
        },
        "enforcement_precedents": [
            "CNIL v Amazon France Logistique — €32M (Dec 2023)",
            "German DPA v notebooksbilliger.de — €10.4M",
        ],
    },
    # ────────────────────────────────────────────────────────────────
    # D2 — SUB-PROCESSOR MANAGEMENT
    # ────────────────────────────────────────────────────────────────
    "D2": {
        "name": "Sub-processor Management",
        "weight": 1.0,
        "regulatory_basis": [
            "GDPR Art. 28(2) and (4)",
            "CCPA/CPRA — notification + contractual flow-down",
            "EDPB Guidelines 7/2020",
        ],
        "framework_refs": [
            "ISO 27701 Annex B — Sub-processor authorization",
            "SOC 2 CC9.2 — Vendor Risk Management",
            "NIST PF ID.IM-P7",
            "CSA CCM STA domain",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d2_published_list_with_locations",
                    "d2_change_notification_period",
                    "d2_objection_right_with_termination",
                    "d2_audit_rights_extend_to_subs",
                    "d2_proof_of_compliance_on_request",
                    "d2_full_liability_retained",
                    "d2_contractual_flowdown",
                ],
                "description": (
                    "Published sub-processor list with locations and "
                    "roles, 30-day notice, objection + termination right, "
                    "audit rights extending to subs, proof-of-compliance "
                    "on request (CRITEO standard), full liability per "
                    "Art. 28(4)."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d2_published_list_with_locations",
                    "d2_change_notification_period",
                    "d2_objection_right_with_termination",
                    "d2_contractual_flowdown",
                ],
                "description": (
                    "Published list with locations, defined notification "
                    "period, objection right with contractual "
                    "consequences, flow-down to sub-processors."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d2_sub_list_exists",
                    "d2_general_authorization_with_notification",
                    "d2_contractual_flowdown",
                ],
                "description": (
                    "Sub-processor list exists (possibly URL-based), "
                    "general authorization with notification of changes, "
                    "standard contractual flow-down."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d2_sub_list_exists",
                ],
                "description": (
                    "Sub-processor list exists but no notification "
                    "mechanism, no objection right, no flow-down clause."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No sub-processor list. No notification mechanism. "
                    "DPA silent on sub-processing."
                ),
            },
        },
        "enforcement_precedents": [
            "CNIL v Criteo — €40M (Jun 2023): audit + proof-of-compliance standard",
        ],
    },
    # ────────────────────────────────────────────────────────────────
    # D3 — DATA SUBJECT RIGHTS
    # ────────────────────────────────────────────────────────────────
    "D3": {
        "name": "Data Subject Rights",
        "weight": 1.0,
        "regulatory_basis": [
            "GDPR Chapter III (Arts. 12–23)",
            "GDPR Art. 28(3)(e)",
            "CCPA/CPRA — access, deletion, correction, opt-out of sale",
        ],
        "framework_refs": [
            "ISO 27701 Annex A — Obligations to PII principals",
            "SOC 2 Privacy TSC P5 (Access), P5.2 (Correction)",
            "NIST PF CT.DM-P1 through P4",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d3_all_gdpr_rights_listed",
                    "d3_ccpa_rights_listed",
                    "d3_contact_details_provided",
                    "d3_response_timeline_stated",
                    "d3_measurable_sla",
                    "d3_automated_dsar_workflow",
                    "d3_identity_verification_process",
                ],
                "description": (
                    "All 7 GDPR rights + CCPA rights explicitly listed. "
                    "Measurable SLA targets (ISO 27701 style, e.g. "
                    "'95% of DSARs within 20 days'). Automated DSAR "
                    "workflow. Identity verification process documented."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d3_all_gdpr_rights_listed",
                    "d3_contact_details_provided",
                    "d3_response_timeline_stated",
                    "d3_dsar_procedure_documented",
                ],
                "description": (
                    "All GDPR Chapter III rights listed with contact "
                    "details, defined response timeline, and documented "
                    "DSAR procedure."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d3_some_rights_listed",
                    "d3_contact_details_provided",
                ],
                "description": (
                    "Some data subject rights listed (access, deletion) "
                    "with contact information, but incomplete coverage "
                    "and no defined timeline."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d3_some_rights_listed",
                ],
                "description": (
                    "Rights mentioned generically without contact "
                    "details or response timelines."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No mention of data subject rights. No contact "
                    "information for privacy requests."
                ),
            },
        },
        "enforcement_precedents": [
            "DPC v Meta — €390M (Jan 2023): transparency on purposes/legal basis",
            "DPC v TikTok — €345M (Sep 2023): children's data, privacy by design",
        ],
    },
    # ────────────────────────────────────────────────────────────────
    # D4 — CROSS-BORDER TRANSFER MECHANISMS
    # ────────────────────────────────────────────────────────────────
    "D4": {
        "name": "Cross-Border Transfer Mechanisms",
        "weight": 1.0,
        "regulatory_basis": [
            "GDPR Chapter V (Arts. 44–50)",
            "CJEU Schrems II (C-311/18)",
            "EU-US Data Privacy Framework (Jul 2023)",
            "EDPB Recommendations 01/2020 on supplementary measures",
        ],
        "framework_refs": [
            "ISO 27701 Annex A — PII sharing/transfer",
            "ISO 27018 — cloud data location disclosure",
            "SOC 2 CC9.2 + Privacy P6",
            "CSA CAIQ DSI-02, DSI-05",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d4_transfer_mechanism_identified",
                    "d4_sccs_module_specified",
                    "d4_tia_documented",
                    "d4_supplementary_measures",
                    "d4_sub_processor_locations_specified",
                    "d4_monitoring_adequacy_changes",
                    "d4_notification_of_mechanism_changes",
                ],
                "description": (
                    "Transfer mechanisms specified with SCC module, "
                    "documented TIA, supplementary measures, sub-"
                    "processor location specificity, monitoring of "
                    "adequacy decision changes."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d4_transfer_mechanism_identified",
                    "d4_sccs_module_specified",
                    "d4_tia_documented",
                    "d4_sub_processor_locations_specified",
                ],
                "description": (
                    "Transfer mechanism identified with SCC module, "
                    "TIA documented per Schrems II, sub-processor "
                    "locations disclosed."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d4_transfer_mechanism_identified",
                ],
                "description": (
                    "Transfer mechanism identified (SCCs, DPF, or "
                    "adequacy) but without module specification, TIA, "
                    "or sub-processor location detail."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d4_transfers_acknowledged",
                ],
                "description": (
                    "Cross-border transfers acknowledged but mechanism "
                    "is vague ('data stays in region') or outdated "
                    "(Privacy Shield)."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No mention of cross-border transfers. No transfer "
                    "mechanism identified."
                ),
            },
        },
        "enforcement_precedents": [
            "DPC v Meta — €1.2B (May 2023): Art. 46(1) infringement, SCCs insufficient",
        ],
    },
    # ────────────────────────────────────────────────────────────────
    # D5 — BREACH NOTIFICATION
    # ────────────────────────────────────────────────────────────────
    "D5": {
        "name": "Breach Notification",
        "weight": 1.0,
        "regulatory_basis": [
            "GDPR Art. 33 (SA notification, 72 hrs)",
            "GDPR Art. 33(2) (processor → controller: without undue delay)",
            "GDPR Art. 34 (individual notification, high risk)",
            "CA Civil Code §1798.82",
        ],
        "framework_refs": [
            "ISO 27701 Clause 6.13 — Incident Management",
            "SOC 2 CC7.3, CC7.4, P6.1",
            "NIST PF Protect-P (PR.PO-P)",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d5_specific_sla_hours",
                    "d5_art33_3_content_commitment",
                    "d5_covers_suspected_incidents",
                    "d5_evidence_preservation",
                    "d5_phased_reporting",
                    "d5_awareness_trigger_defined",
                    "d5_sub_processor_breach_cascade",
                ],
                "description": (
                    "Specific SLA (≤24 hrs), commits to all Art. 33(3) "
                    "content, covers confirmed + suspected incidents, "
                    "evidence preservation, phased reporting per "
                    "Art. 33(4), 'awareness' trigger defined, sub-"
                    "processor breach cascade addressed."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d5_specific_sla_hours",
                    "d5_art33_3_content_commitment",
                    "d5_named_response_lead",
                ],
                "description": (
                    "Specific SLA (24–48 hrs), commits to providing "
                    "Art. 33(3) content elements (nature, numbers, "
                    "consequences, measures), named response lead "
                    "(ISO 27701)."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d5_notification_obligation_stated",
                ],
                "description": (
                    "'Without undue delay' notification mirrors GDPR "
                    "Art. 33(2) verbatim. No specific SLA. Mentions "
                    "notification but doesn't commit to Art. 33(3) "
                    "content."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d5_breach_mentioned",
                ],
                "description": (
                    "Breach notification mentioned but with vague "
                    "language: 'as required by law', 'within a "
                    "reasonable period', or 'promptly'."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No breach notification clause. No commitment to "
                    "assist with controller's Art. 33 obligations."
                ),
            },
        },
        "enforcement_precedents": [
            "DPC v Meta — €251M (Dec 2024): incomplete Art. 33 notifications",
        ],
    },
    # ────────────────────────────────────────────────────────────────
    # D6 — AI/ML DATA USAGE
    # ────────────────────────────────────────────────────────────────
    "D6": {
        "name": "AI/ML Data Usage",
        "weight": 1.5,
        "regulatory_basis": [
            "EU AI Act (Regulation 2024/1689) Arts. 10, 50, 53",
            "GDPR Arts. 5(1)(a), 6, 12, 13, 22",
            "FTC Act Section 5 — algorithmic disgorgement precedent",
            "CCPA/CPRA ADMT Regulations (Jul 2025)",
            "Colorado AI Act SB 24-205 (effective Jun 2026)",
        ],
        "framework_refs": [
            "ISO 27701:2025 — AI-related privacy controls",
            "NIST AI RMF 1.0",
            "NIST PF 1.1 — AI privacy risk subcategories",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d6_ai_disclosed_as_separate_purpose",
                    "d6_legal_basis_identified",
                    "d6_data_categories_specified",
                    "d6_opt_in_for_training",
                    "d6_customer_data_segregation",
                    "d6_data_provenance_documentation",
                    "d6_training_data_retention_schedule",
                    "d6_algorithmic_disgorgement_readiness",
                    "d6_ai_act_art53_compliance",
                    "d6_bias_mitigation_documented",
                    "d6_update_cadence_stated",
                ],
                "description": (
                    "Explicit separate disclosure of AI/ML training as "
                    "distinct purpose with legal basis. Opt-in (not "
                    "just opt-out). Customer data segregation. Data "
                    "provenance documentation. Disgorgement readiness. "
                    "AI Act Art. 53 compliance. Bias mitigation. "
                    "Update cadence ≥ every 6 months."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d6_ai_disclosed_as_separate_purpose",
                    "d6_legal_basis_identified",
                    "d6_data_categories_specified",
                    "d6_opt_out_prominent",
                    "d6_customer_data_segregation",
                    "d6_training_data_retention_schedule",
                    "d6_dpa_ai_restriction_clause",
                ],
                "description": (
                    "AI training clearly disclosed as distinct purpose "
                    "with legal basis. Data categories specified. "
                    "Prominent opt-out. Customer data segregation. "
                    "DPA contains explicit AI restriction clause."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d6_ai_disclosed_as_separate_purpose",
                    "d6_opt_out_exists",
                ],
                "description": (
                    "AI/ML training disclosed as distinct purpose. "
                    "Opt-out mechanism available. But no specifics on "
                    "categories, models, or provenance."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d6_ai_mentioned",
                ],
                "description": (
                    "AI/ML mentioned but bundled with other purposes, "
                    "not separately identified. Opt-out buried or "
                    "burdensome. No data category specifics."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No mention of AI/ML data usage. Or: vague 'improve "
                    "products and services' without AI disclosure. Or: "
                    "retroactive policy change for AI training."
                ),
            },
        },
        "enforcement_precedents": [
            "Garante v OpenAI — €15M (Dec 2024): no lawful basis for training",
            "CNIL v Criteo — €40M (Jun 2023): AI training = separate purpose",
            "FTC v Everalbum (2021): algorithmic disgorgement order",
            "FTC v Weight Watchers (2022): model deletion + data deletion",
            "FTC v Rite Aid (2024): deployer liability for AI accuracy",
        ],
    },
    # ────────────────────────────────────────────────────────────────
    # D7 — RETENTION AND DELETION
    # ────────────────────────────────────────────────────────────────
    "D7": {
        "name": "Retention & Deletion",
        "weight": 1.0,
        "regulatory_basis": [
            "GDPR Art. 5(1)(e) — storage limitation",
            "GDPR Art. 17 — right to erasure",
            "GDPR Art. 28(3)(g) — deletion/return at termination",
            "CCPA/CPRA — right to know retention periods",
        ],
        "framework_refs": [
            "ISO 27701 Annex A — Storage limitation controls",
            "SOC 2 Privacy TSC P4 — Use, Retention, Disposal",
            "NIST PF CT.DM-P5",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d7_category_specific_retention",
                    "d7_deletion_timeframe_specified",
                    "d7_deletion_certification",
                    "d7_backup_copies_addressed",
                    "d7_derived_data_addressed",
                    "d7_ai_training_data_retention_separate",
                    "d7_sub_processor_deletion_obligations",
                    "d7_periodic_review_cycle",
                ],
                "description": (
                    "Category-specific retention schedules linked to "
                    "purposes. Deletion within defined timeframe with "
                    "certification. Backup copies, derived/aggregated "
                    "data, AI training data, and sub-processor deletion "
                    "all addressed. Periodic review cycle."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d7_category_specific_retention",
                    "d7_deletion_timeframe_specified",
                    "d7_deletion_certification",
                    "d7_backup_copies_addressed",
                ],
                "description": (
                    "Category-specific retention schedules. Defined "
                    "deletion timeframe (e.g. 30 days). Certification "
                    "of deletion on request. Backup copies explicitly "
                    "addressed."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d7_general_retention_stated",
                    "d7_deletion_at_termination",
                ],
                "description": (
                    "General retention period stated. Deletion at "
                    "contract end per Art. 28(3)(g). But no category-"
                    "specific schedules and no confirmation mechanism."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d7_retention_mentioned",
                ],
                "description": (
                    "Retention topic addressed but with vague language: "
                    "'as required by law', 'commercially reasonable "
                    "efforts'. No specific periods."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No retention schedule. No deletion mechanism. "
                    "'Retained indefinitely' or silence on the topic."
                ),
            },
        },
        "enforcement_precedents": [
            "Dutch DPA v Netflix — €4.75M (Dec 2024): vague retention language",
            "CNIL v Amazon France — €32M (Dec 2023): excessive retention",
        ],
    },
    # ────────────────────────────────────────────────────────────────
    # D8 — DPA COMPLETENESS
    # ────────────────────────────────────────────────────────────────
    "D8": {
        "name": "DPA Completeness",
        "weight": 1.5,
        "regulatory_basis": [
            "GDPR Art. 28(3)(a)–(h)",
            "EDPB Guidelines 7/2020",
            "EC 2021 SCCs (Modules 2 & 3)",
            "EC Art. 28 SCCs template",
            "CCPA/CPRA service provider agreement requirements",
        ],
        "framework_refs": [
            "ISO 27701 Annex B (processor controls) + Annex D (GDPR mapping)",
            "SOC 2 CC9.2 + Privacy criteria",
            "NIST PF GV.PO-P (Governance)",
        ],
        "levels": {
            5: {
                "label": "Gold standard",
                "required_signals": [
                    "d8_all_art28_provisions",
                    "d8_tailored_not_template",
                    "d8_processing_annex_detailed",
                    "d8_toms_in_annex",
                    "d8_measurable_slas",
                    "d8_ai_restriction_clause",
                    "d8_ccpa_provisions",
                    "d8_international_transfers_specified",
                    "d8_independent_verification",
                    "d8_version_controlled",
                    "d8_regular_compliance_reports",
                ],
                "description": (
                    "All Art. 28(3)(a)–(h) provisions, demonstrably "
                    "tailored. Detailed processing annex. TOMs annex "
                    "with change approval. Measurable SLAs. AI/ML "
                    "restriction clause. CCPA provisions. Transfer "
                    "mechanisms. Independent verification (SOC 2 Type "
                    "II + Privacy TSC or ISO 27701). Version-controlled."
                ),
            },
            4: {
                "label": "Strong",
                "required_signals": [
                    "d8_all_art28_provisions",
                    "d8_processing_annex_detailed",
                    "d8_toms_in_annex",
                    "d8_measurable_slas",
                    "d8_ccpa_provisions",
                    "d8_international_transfers_specified",
                    "d8_independent_verification",
                ],
                "description": (
                    "All Art. 28 provisions with specificity beyond "
                    "verbatim. Detailed processing annex. TOMs annex. "
                    "Measurable SLAs. CCPA provisions. Transfer "
                    "mechanisms specified. Independent verification."
                ),
            },
            3: {
                "label": "Minimum compliant",
                "required_signals": [
                    "d8_all_art28_provisions",
                    "d8_processing_annex_exists",
                ],
                "description": (
                    "All 8 Art. 28(3) provisions present with some "
                    "specificity beyond verbatim restatement. Processing "
                    "description annex exists. Recognizably a template."
                ),
            },
            2: {
                "label": "Deficient",
                "required_signals": [
                    "d8_most_art28_provisions",
                ],
                "description": (
                    "DPA exists and addresses most Art. 28 provisions, "
                    "but only by restating regulation verbatim. Missing "
                    "specificity and at least one area (breach SLA, "
                    "deletion timeframe, audit process)."
                ),
            },
            1: {
                "label": "Absent",
                "required_signals": [],
                "description": (
                    "No DPA exists. Or DPA missing 3+ of the 8 "
                    "mandatory provisions. Or references outdated "
                    "framework. Or contains provisions conflicting "
                    "with GDPR."
                ),
            },
        },
        "enforcement_precedents": [
            "CNIL v Dedalus Biologie — €1.5M (Apr 2022): processor liable for missing DPA",
            "Hessian DPA (Jan 2019): fine for missing DPA",
        ],
        # D8 Art. 28(3) sub-provisions for structural completeness check
        "art28_checklist": [
            "art28_3a_documented_instructions",
            "art28_3b_confidentiality",
            "art28_3c_security_measures",
            "art28_3d_sub_processing",
            "art28_3e_dsar_assistance",
            "art28_3f_arts32_36_assistance",
            "art28_3g_deletion_return",
            "art28_3h_audit_rights",
        ],
    },
}

# ─────────────────────────────────────────────────────────────────────
# Assessment scope — what each dimension requires to be fully scored
# ─────────────────────────────────────────────────────────────────────
# "both"     — public policy reveals useful signal; DPA supplements
# "dpa_only" — cannot be meaningfully scored from public policy alone

_ASSESSABLE_FROM: dict[str, str] = {
    "D1": "both",      # policy covers minimization; DPA supplements
    "D2": "both",      # policy lists sub-processors; DPA has contractual obligations
    "D3": "both",      # policy states rights; DPA details the assistance mechanism
    "D4": "both",      # policy mentions transfer mechanisms; DPA specifies modules/TIA
    "D5": "both",      # policy mentions breach notification; DPA has the SLA
    "D6": "both",      # policy discloses AI use and opt-out
    "D7": "both",      # policy states retention periods; DPA specifies termination process
    "D8": "dpa_only",  # DPA completeness cannot be assessed from public policy alone
}

# Dims that are "both" but where the DPA adds significant signal beyond policy
_PARTIALLY_FROM_POLICY: frozenset[str] = frozenset({"D2", "D4", "D5"})

# Inject assessable_from into each RUBRIC dimension for external access
for _dk, _af in _ASSESSABLE_FROM.items():
    RUBRIC[_dk]["assessable_from"] = _af

# ─────────────────────────────────────────────────────────────────────
# D8 dependency ceiling — D8 quality caps D2, D5, D7
# ─────────────────────────────────────────────────────────────────────
# Rationale: a privacy policy promising 24-hr breach notification
# but sitting on a DPA that says "without undue delay" creates an
# enforceability gap.  The DPA is what the controller can rely on.

D8_DEPENDENCY_CEILING: dict[int, dict[str, int]] = {
    1: {"D2": 2, "D5": 2, "D7": 2},
    2: {"D2": 3, "D5": 3, "D7": 3},
    3: {"D2": 4, "D5": 4, "D7": 4},
    # D8 ≥ 4 removes the ceiling
}

# ─────────────────────────────────────────────────────────────────────
# Framework evidence modifiers
# ─────────────────────────────────────────────────────────────────────
# Additive to base score derived from policy/DPA language, capped at 5.

FRAMEWORK_MODIFIERS: dict[str, dict[str, float]] = {
    "soc2_type2_privacy_tsc": {
        "D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0,
        "D5": 1.0, "D6": 1.0, "D7": 1.0, "D8": 1.0,
    },
    "iso_27701_certified": {
        "D1": 1.0, "D2": 1.0, "D3": 1.0, "D4": 1.0,
        "D5": 1.0, "D6": 1.0, "D7": 1.0, "D8": 1.0,
    },
    "soc2_type2_security_only": {
        "D5": 0.5, "D8": 0.5,
    },
    "iso_27001_only": {
        "D5": 0.5,
    },
    "csa_star_certified": {
        "D4": 0.5,
    },
}


# ─────────────────────────────────────────────────────────────────────
# Scoring engine
# ─────────────────────────────────────────────────────────────────────

@dataclass
class DimensionResult:
    """Score result for a single dimension."""

    dimension: str
    name: str
    raw_score: int
    capped_score: int
    level_label: str
    weight: float
    cap_reasons: list[str] = field(default_factory=list)
    matched_signals: list[str] = field(default_factory=list)
    missing_for_next: list[str] = field(default_factory=list)
    # Scope flags — set when assessment_scope limits what can be assessed
    is_excluded: bool = False           # True → excluded from weighted average
    partially_assessed: bool = False    # True → DPA would provide additional signal
    absent_type: str | None = None      # e.g. "requires_dpa"


@dataclass
class AssessmentResult:
    """Full assessment result."""

    version: str
    vendor: str
    dimensions: dict[str, DimensionResult]
    weighted_average: float
    risk_tier: str
    red_flags: list[dict[str, Any]]
    framework_evidence: list[str]
    escalation_required: bool = False
    escalation_reasons: list[str] = field(default_factory=list)
    active_profile: str | None = None
    assessment_scope: str = "public_policy_only"
    documents_assessed: list[str] = field(default_factory=list)
    signal_sources: dict = field(default_factory=dict)


def _score_dimension(
    dim_key: str,
    evidence: dict[str, bool],
) -> tuple[int, str, list[str], list[str]]:
    """Walk levels 5→1, return (score, label, matched, missing_for_next).

    ``evidence`` maps signal slugs to True/False.
    """
    dim = RUBRIC[dim_key]
    for level in (5, 4, 3, 2):
        required = dim["levels"][level]["required_signals"]
        if all(evidence.get(s, False) for s in required):
            matched = [s for s in required if evidence.get(s, False)]
            # What would be needed for the *next* level?
            if level < 5:
                next_req = dim["levels"][level + 1]["required_signals"]
                missing = [s for s in next_req if not evidence.get(s, False)]
            else:
                missing = []
            return level, dim["levels"][level]["label"], matched, missing

    # Level 1 — fallback (no signals required)
    if 2 in dim["levels"]:
        next_req = dim["levels"][2]["required_signals"]
        missing = [s for s in next_req if not evidence.get(s, False)]
    else:
        missing = []
    return 1, dim["levels"][1]["label"], [], missing


def score_vendor(
    vendor_name: str,
    evidence: dict[str, dict[str, bool]],
    extracted_text: str = "",
    framework_evidence: list[str] | None = None,
    profile_weights: dict[str, float] | None = None,
    auto_escalate_triggers: list[dict] | None = None,
    assessment_scope: str = "public_policy_only",
    dpa_available: bool = True,
) -> AssessmentResult:
    """Run the full deterministic scoring pipeline.

    Parameters
    ----------
    vendor_name:
        Display name of the vendor.
    evidence:
        ``{"D1": {"d1_purposes_stated": True, ...}, "D2": {...}, ...}``
    extracted_text:
        Raw policy/DPA text for red-flag scanning.
    framework_evidence:
        List of framework keys from ``FRAMEWORK_MODIFIERS``, e.g.
        ``["soc2_type2_privacy_tsc"]``.
    profile_weights:
        Per-dimension weight overrides from a loaded profile.  Replaces
        the rubric defaults for the weighted-average calculation and is
        stored on each ``DimensionResult``.
    auto_escalate_triggers:
        List of trigger dicts from config ``auto_escalate`` list.
        Checked after scoring; sets ``escalation_required`` and
        ``escalation_reasons`` on the returned result.
    """
    framework_evidence = framework_evidence or []

    # 1. Red-flag scan
    rf_hits = scan_red_flags(extracted_text) if extracted_text else []
    rf_ceilings = red_flag_ceilings(rf_hits)

    # 2. Score each dimension (raw)
    raw_scores: dict[str, tuple[int, str, list[str], list[str]]] = {}
    for dim_key in RUBRIC:
        dim_ev = evidence.get(dim_key, {})
        raw_scores[dim_key] = _score_dimension(dim_key, dim_ev)

    # 3. Apply framework modifiers to raw scores (capped at 5)
    modified_raw: dict[str, int] = {}
    for dim_key in RUBRIC:
        base = raw_scores[dim_key][0]
        modifier = 0.0
        for fw in framework_evidence:
            modifier += FRAMEWORK_MODIFIERS.get(fw, {}).get(dim_key, 0.0)
        modified_raw[dim_key] = min(5, int(base + modifier))

    # 4. Apply red-flag ceilings
    after_rf: dict[str, int] = {}
    cap_reasons: dict[str, list[str]] = {k: [] for k in RUBRIC}
    for dim_key in RUBRIC:
        score = modified_raw[dim_key]
        if dim_key in rf_ceilings and score > rf_ceilings[dim_key]:
            cap_reasons[dim_key].append(
                f"Red-flag ceiling → {rf_ceilings[dim_key]}"
            )
            score = rf_ceilings[dim_key]
        after_rf[dim_key] = score

    # 5. Apply D8 dependency ceiling on D2, D5, D7
    d8_score = after_rf["D8"]
    if d8_score in D8_DEPENDENCY_CEILING:
        ceilings = D8_DEPENDENCY_CEILING[d8_score]
        for dep_dim, dep_ceil in ceilings.items():
            if after_rf[dep_dim] > dep_ceil:
                cap_reasons[dep_dim].append(
                    f"D8 dependency ceiling (D8={d8_score}) → {dep_ceil}"
                )
                after_rf[dep_dim] = dep_ceil

    # 6. Build dimension results
    dim_results: dict[str, DimensionResult] = {}
    for dim_key in RUBRIC:
        raw_score, label, matched, missing = raw_scores[dim_key]
        capped = after_rf[dim_key]
        # Re-derive label if capping changed the effective level
        if capped != raw_score:
            label = RUBRIC[dim_key]["levels"][capped]["label"]
        # Profile weight — override rubric default if provided
        rubric_weight = RUBRIC[dim_key]["weight"]
        applied_weight = rubric_weight
        dim_cap_reasons = list(cap_reasons[dim_key])
        if profile_weights:
            pw = profile_weights.get(dim_key)
            if pw is not None:
                applied_weight = pw
                if abs(pw - rubric_weight) > 0.001:
                    dim_cap_reasons.append(f"{dim_key} weight ×{pw:.1f} — profile")
        dim_results[dim_key] = DimensionResult(
            dimension=dim_key,
            name=RUBRIC[dim_key]["name"],
            raw_score=raw_score,
            capped_score=capped,
            level_label=label,
            weight=applied_weight,
            cap_reasons=dim_cap_reasons,
            matched_signals=matched,
            missing_for_next=missing,
        )

    # 6b. Apply assessment scope rules
    if assessment_scope == "public_policy_only":
        for dim_key in RUBRIC:
            if _ASSESSABLE_FROM.get(dim_key) == "dpa_only":
                dim_results[dim_key].is_excluded = True
                dim_results[dim_key].absent_type = "requires_dpa"
            elif dim_key in _PARTIALLY_FROM_POLICY:
                dim_results[dim_key].partially_assessed = True
    elif not dpa_available:
        # Documents present but no DPA — D8 still cannot be scored
        for dim_key in RUBRIC:
            if _ASSESSABLE_FROM.get(dim_key) == "dpa_only":
                dim_results[dim_key].is_excluded = True
                dim_results[dim_key].absent_type = "requires_dpa"

    # 7. Weighted average — exclude is_excluded dimensions
    _included = [k for k in RUBRIC if not dim_results[k].is_excluded]
    if profile_weights:
        total_weight = sum(profile_weights.get(k, RUBRIC[k]["weight"]) for k in _included)
        weighted_sum = sum(
            dim_results[k].capped_score * profile_weights.get(k, RUBRIC[k]["weight"]) for k in _included
        )
    else:
        total_weight = sum(RUBRIC[k]["weight"] for k in _included)
        weighted_sum = sum(
            dim_results[k].capped_score * RUBRIC[k]["weight"] for k in _included
        )
    weighted_avg = round(weighted_sum / total_weight, 1)
    risk = classify_risk(weighted_avg)

    # 8. Auto-escalation check
    escalation_required = False
    escalation_reasons: list[str] = []
    for trigger in (auto_escalate_triggers or []):
        t_type = trigger.get("type")
        if t_type == "tier":
            if risk == trigger.get("tier"):
                escalation_reasons.append(trigger.get("label", f"Risk tier is {risk}"))
        elif t_type == "score_below":
            dim = trigger.get("dimension")
            threshold = int(trigger.get("threshold", 2))
            if dim and dim in dim_results and dim_results[dim].capped_score < threshold:
                escalation_reasons.append(trigger.get("label", f"{dim} score below {threshold}"))
        elif t_type == "red_flag":
            flag_label = (trigger.get("flag_label") or "").lower()
            for rf in rf_hits:
                if flag_label in rf["label"].lower():
                    escalation_reasons.append(trigger.get("label", rf["label"]))
                    break
        elif t_type == "weighted_average_below":
            threshold = float(trigger.get("threshold", 2.5))
            if weighted_avg < threshold:
                escalation_reasons.append(trigger.get("label", f"Weighted average {weighted_avg} < {threshold}"))
    if escalation_reasons:
        escalation_required = True

    return AssessmentResult(
        version=__version__,
        vendor=vendor_name,
        dimensions=dim_results,
        weighted_average=weighted_avg,
        risk_tier=risk,
        red_flags=rf_hits,
        framework_evidence=framework_evidence,
        escalation_required=escalation_required,
        escalation_reasons=escalation_reasons,
        assessment_scope=assessment_scope,
    )


def result_to_dict(result: AssessmentResult) -> dict[str, Any]:
    """Serialize an AssessmentResult to a JSON-safe dict."""
    return {
        "rubric_version": result.version,
        "vendor": result.vendor,
        "assessment_scope": result.assessment_scope,
        "weighted_average": result.weighted_average,
        "risk_tier": result.risk_tier,
        "escalation_required": result.escalation_required,
        "escalation_reasons": result.escalation_reasons,
        "active_profile": result.active_profile,
        "framework_evidence": result.framework_evidence,
        "red_flags": result.red_flags,
        "dimensions": {
            k: {
                "name": v.name,
                "raw_score": v.raw_score,
                "capped_score": v.capped_score,
                "level_label": v.level_label,
                "weight": v.weight,
                "cap_reasons": v.cap_reasons,
                "matched_signals": v.matched_signals,
                "missing_for_next": v.missing_for_next,
                "is_excluded": v.is_excluded,
                "partially_assessed": v.partially_assessed,
                "absent_type": v.absent_type,
            }
            for k, v in result.dimensions.items()
        },
    }


# ─────────────────────────────────────────────────────────────────────
# Extraction prompt generator
# ─────────────────────────────────────────────────────────────────────
# Produces the prompt sent to the AI provider to extract evidence.
# The AI returns structured signals; Bandit scores them.

def build_extraction_prompt(vendor_name: str, policy_text: str) -> str:
    """Build the evidence-extraction prompt for any LLM provider.

    The LLM must return JSON with the signal keys defined in the
    rubric. Bandit then scores the signals — the LLM never assigns
    scores.
    """
    # Collect all signal keys across all dimensions
    all_signals: dict[str, list[str]] = {}
    for dim_key, dim in RUBRIC.items():
        signals = set()
        for level_data in dim["levels"].values():
            signals.update(level_data["required_signals"])
        all_signals[dim_key] = sorted(signals)

    # Also collect Art. 28 checklist for D8
    art28_keys = RUBRIC["D8"].get("art28_checklist", [])

    signal_block = ""
    for dim_key in sorted(all_signals.keys()):
        dim_name = RUBRIC[dim_key]["name"]
        signal_block += f"\n  // {dim_key} — {dim_name}\n"
        for sig in all_signals[dim_key]:
            signal_block += f'  "{sig}": true | false,\n'

    art28_block = ""
    for key in art28_keys:
        art28_block += f'  "{key}": true | false,\n'

    return f"""You are a privacy compliance evidence extractor. Read the
privacy policy and/or DPA text below for **{vendor_name}** and determine
whether each evidence signal is present (true) or absent (false).

IMPORTANT: You are extracting factual evidence only. Do NOT assign scores
or make qualitative judgments. The scoring engine handles that.

Return ONLY a valid JSON object — no markdown, no explanation:

{{
  "signals": {{
{signal_block}
  }},
  "art28_checklist": {{
{art28_block}
  }},
  "framework_certifications": {{
    "soc2_type2_privacy_tsc": true | false,
    "iso_27701_certified": true | false,
    "soc2_type2_security_only": true | false,
    "iso_27001_only": true | false,
    "csa_star_certified": true | false
  }}
}}

Signal definitions:
- A signal is TRUE if the document contains clear, specific evidence of
  the described practice. Vague or aspirational language is FALSE.
- "d2_published_list_with_locations" = TRUE only if an actual list of
  sub-processors with geographic locations is published or referenced.
- "d5_specific_sla_hours" = TRUE only if a numeric hour/day deadline is
  stated (not "without undue delay" or "promptly").
- "d6_ai_disclosed_as_separate_purpose" = TRUE only if AI/ML training is
  called out as a distinct processing purpose, separate from general
  service delivery.
- "d8_tailored_not_template" = TRUE only if the DPA contains provisions
  clearly specific to this vendor's processing (not generic boilerplate).
- "d8_all_art28_provisions" = TRUE only if ALL 8 items in art28_checklist
  are TRUE.
- "d8_most_art28_provisions" = TRUE if 5-7 of the art28_checklist items
  are TRUE.

DOCUMENT TEXT:
{policy_text[:60000]}"""


# ─────────────────────────────────────────────────────────────────────
# CLI convenience
# ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json, sys

    if len(sys.argv) < 2:
        print(f"Bandit Rubric Engine v{__version__}")
        print("Usage: python rubric.py <evidence.json>")
        print("       python rubric.py --signals  (list all signal keys)")
        sys.exit(0)

    if sys.argv[1] == "--signals":
        for dim_key in sorted(RUBRIC.keys()):
            signals = set()
            for lvl in RUBRIC[dim_key]["levels"].values():
                signals.update(lvl["required_signals"])
            print(f"\n{dim_key} — {RUBRIC[dim_key]['name']}:")
            for s in sorted(signals):
                print(f"  {s}")
        sys.exit(0)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    vendor = data.get("vendor", "Unknown")
    signals = data.get("signals", {})
    text = data.get("extracted_text", "")
    frameworks = data.get("framework_certifications", {})

    # Reshape signals into per-dimension dicts
    per_dim: dict[str, dict[str, bool]] = {}
    for dim_key in RUBRIC:
        prefix = dim_key.lower() + "_"
        # D8 uses d8_ prefix
        per_dim[dim_key] = {
            k: v for k, v in signals.items() if k.startswith(prefix)
        }

    fw_list = [k for k, v in frameworks.items() if v]

    result = score_vendor(vendor, per_dim, text, fw_list)
    print(json.dumps(result_to_dict(result), indent=2))
