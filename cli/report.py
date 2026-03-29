"""
Bandit HTML report generator.

Produces a self-contained, branded HTML file with:
  - Collapsible dimension sections (<details>/<summary>)
  - Evidence found / gaps identified per dimension
  - Red flags triggered per dimension
  - Vendor follow-up questions
  - Contract recommendations (scores ≤ 3)
  - Team summary panels (GRC / Legal / Security)
  - Vendor follow-up email template
"""
from __future__ import annotations

import datetime
import pathlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.agents.privacy_bandit import PrivacyAssessment

from core.scoring.rubric import RUBRIC

# ─────────────────────────────────────────────────────────────────────
# Signal → plain-English labels
# ─────────────────────────────────────────────────────────────────────

_SIGNAL_LABELS: dict[str, str] = {
    # D1 — Data Minimization
    "d1_purposes_stated":                 "Collection purposes stated",
    "d1_categories_listed":               "Data categories listed",
    "d1_categories_linked_to_purposes":   "Categories explicitly linked to specific purposes",
    "d1_specific_retention_per_category": "Category-specific retention schedules documented",
    "d1_automated_minimization_controls": "Automated data minimization controls in place",
    "d1_privacy_by_design_documented":    "Privacy by design approach documented",
    "d1_periodic_review_cycle":           "Periodic data review cycle established",
    # D2 — Sub-processor Management
    "d2_sub_list_exists":                         "Sub-processor list exists",
    "d2_general_authorization_with_notification": "General authorization with change notification",
    "d2_contractual_flowdown":                    "Contractual obligations flow to sub-processors",
    "d2_published_list_with_locations":           "Published sub-processor list with locations and roles",
    "d2_change_notification_period":              "Defined advance notification period for changes",
    "d2_objection_right_with_termination":        "Objection right with termination option",
    "d2_audit_rights_extend_to_subs":             "Audit rights extend to sub-processors",
    "d2_proof_of_compliance_on_request":          "Sub-processor compliance evidence available on request",
    "d2_full_liability_retained":                 "Full liability retained per Art. 28(4)",
    # D3 — Data Subject Rights
    "d3_some_rights_listed":            "Some data subject rights listed",
    "d3_contact_details_provided":      "Contact details provided for privacy requests",
    "d3_all_gdpr_rights_listed":        "All GDPR Chapter III rights explicitly listed",
    "d3_response_timeline_stated":      "Response timeline stated",
    "d3_dsar_procedure_documented":     "DSAR handling procedure documented",
    "d3_ccpa_rights_listed":            "CCPA/CPRA rights listed",
    "d3_measurable_sla":                "Measurable SLA targets for DSAR response",
    "d3_automated_dsar_workflow":       "Automated DSAR intake and workflow",
    "d3_identity_verification_process": "Identity verification process documented",
    # D4 — Cross-Border Transfers
    "d4_transfers_acknowledged":            "Cross-border transfers acknowledged",
    "d4_transfer_mechanism_identified":     "Transfer mechanism identified (SCCs / DPF / adequacy)",
    "d4_sccs_module_specified":             "Applicable SCC module specified",
    "d4_tia_documented":                    "Transfer Impact Assessment (TIA) documented",
    "d4_sub_processor_locations_specified": "Sub-processor processing locations disclosed",
    "d4_supplementary_measures":            "Supplementary technical measures documented",
    "d4_monitoring_adequacy_changes":       "Process for monitoring adequacy decision changes",
    "d4_notification_of_mechanism_changes": "Notification of transfer mechanism changes committed",
    # D5 — Breach Notification
    "d5_breach_mentioned":               "Breach notification mentioned",
    "d5_notification_obligation_stated": "Notification obligation stated",
    "d5_specific_sla_hours":             "Specific notification timeline committed",
    "d5_art33_3_content_commitment":     "Art. 33(3) notification content committed (nature, numbers, consequences, measures)",
    "d5_named_response_lead":            "Named incident response lead identified",
    "d5_covers_suspected_incidents":     "Covers suspected (not just confirmed) incidents",
    "d5_evidence_preservation":          "Evidence preservation committed",
    "d5_phased_reporting":               "Phased reporting per Art. 33(4) supported",
    "d5_awareness_trigger_defined":      "Awareness trigger clearly defined",
    "d5_sub_processor_breach_cascade":   "Sub-processor breach notification cascade addressed",
    # D6 — AI/ML Data Usage
    "d6_ai_mentioned":                       "AI/ML usage mentioned",
    "d6_ai_disclosed_as_separate_purpose":   "AI/ML training disclosed as distinct purpose",
    "d6_opt_out_exists":                     "Opt-out mechanism exists",
    "d6_opt_out_prominent":                  "Opt-out is prominent and accessible",
    "d6_legal_basis_identified":             "Legal basis for AI/ML processing identified",
    "d6_data_categories_specified":          "Data categories used for AI training specified",
    "d6_customer_data_segregation":          "Customer data segregated from training pool",
    "d6_training_data_retention_schedule":   "AI training data retention schedule defined",
    "d6_dpa_ai_restriction_clause":          "DPA contains explicit AI/ML restriction clause",
    "d6_opt_in_for_training":                "Opt-in (not just opt-out) required for AI training",
    "d6_data_provenance_documentation":      "Training data provenance documented",
    "d6_algorithmic_disgorgement_readiness": "Algorithmic disgorgement readiness (FTC precedent)",
    "d6_ai_act_art53_compliance":            "EU AI Act Art. 53 compliance addressed",
    "d6_bias_mitigation_documented":         "Bias and fairness mitigation documented",
    "d6_update_cadence_stated":              "Model update and policy review cadence stated",
    # D7 — Retention & Deletion
    "d7_retention_mentioned":                  "Retention topic addressed",
    "d7_general_retention_stated":             "General retention period stated",
    "d7_deletion_at_termination":              "Deletion at contract termination committed",
    "d7_category_specific_retention":          "Category-specific retention schedules defined",
    "d7_deletion_timeframe_specified":         "Specific deletion timeframe defined",
    "d7_deletion_certification":               "Deletion certification provided on request",
    "d7_backup_copies_addressed":              "Backup copies addressed in deletion process",
    "d7_derived_data_addressed":               "Derived and aggregated data addressed",
    "d7_ai_training_data_retention_separate":  "AI training data retention separately addressed",
    "d7_sub_processor_deletion_obligations":   "Sub-processor deletion obligations included",
    "d7_periodic_review_cycle":                "Periodic retention review cycle documented",
    # D8 — DPA Completeness
    "d8_most_art28_provisions":             "Most Art. 28(3) provisions present",
    "d8_all_art28_provisions":              "All Art. 28(3)(a)–(h) provisions addressed",
    "d8_processing_annex_exists":           "Processing description annex exists",
    "d8_processing_annex_detailed":         "Detailed processing annex included",
    "d8_toms_in_annex":                     "Technical and organisational measures in annex",
    "d8_measurable_slas":                   "Measurable SLAs included",
    "d8_ai_restriction_clause":             "AI/ML restriction clause in DPA",
    "d8_ccpa_provisions":                   "CCPA service provider provisions included",
    "d8_international_transfers_specified": "International transfer mechanisms specified",
    "d8_independent_verification":          "Independent verification (SOC 2 / ISO 27701)",
    "d8_version_controlled":                "DPA is version-controlled",
    "d8_regular_compliance_reports":        "Regular compliance reporting committed",
    "d8_tailored_not_template":             "DPA is tailored, not a verbatim template",
    # Art. 28 checklist
    "art28_3a_documented_instructions": "Art. 28(3)(a) — Processing on documented instructions only",
    "art28_3b_confidentiality":         "Art. 28(3)(b) — Confidentiality obligations on processing staff",
    "art28_3c_security_measures":       "Art. 28(3)(c) — Technical and organisational security measures",
    "art28_3d_sub_processing":          "Art. 28(3)(d) — Sub-processor authorization and obligations",
    "art28_3e_dsar_assistance":         "Art. 28(3)(e) — Assistance with data subject rights",
    "art28_3f_arts32_36_assistance":    "Art. 28(3)(f) — Assistance with Arts. 32–36 obligations",
    "art28_3g_deletion_return":         "Art. 28(3)(g) — Deletion or return of data at termination",
    "art28_3h_audit_rights":            "Art. 28(3)(h) — Audit rights and information provision",
}

# ─────────────────────────────────────────────────────────────────────
# Per-signal vendor follow-up questions
# ─────────────────────────────────────────────────────────────────────

_SIGNAL_QUESTIONS: dict[str, str] = {
    # D1
    "d1_categories_linked_to_purposes":   "Can you provide a data inventory mapping each category of data you collect to its specific processing purpose?",
    "d1_specific_retention_per_category": "What is your documented retention schedule for each category of personal data you process on our behalf?",
    "d1_automated_minimization_controls": "What technical controls enforce data minimization — automated deletion, access restrictions, or similar?",
    "d1_privacy_by_design_documented":    "Do you have a documented privacy-by-design methodology? Can you share your PbD policy?",
    "d1_periodic_review_cycle":           "How frequently do you review your data collection and retention practices, and who owns that process?",
    "d1_categories_listed":               "What categories of personal data do you collect and process on behalf of your customers?",
    "d1_purposes_stated":                 "For what specific purposes do you process our users' personal data?",
    # D2
    "d2_published_list_with_locations":        "Can you provide your current sub-processor list including each sub-processor's country of operation and data categories processed?",
    "d2_change_notification_period":           "How much advance notice do you provide before adding or replacing a sub-processor, and how is that notice delivered?",
    "d2_objection_right_with_termination":     "If we object to a new sub-processor, what is the process and can we terminate without penalty if the objection is not resolved?",
    "d2_audit_rights_extend_to_subs":          "Do our audit rights extend to your sub-processors, and how do you exercise those rights on our behalf?",
    "d2_proof_of_compliance_on_request":       "Can you provide evidence of sub-processor compliance (e.g. their SOC 2 or ISO 27701) on request?",
    "d2_contractual_flowdown":                 "What data protection obligations do you contractually impose on sub-processors? Can we review a sample sub-processor agreement?",
    "d2_sub_list_exists":                      "Do you maintain a list of the third parties who process our personal data? Can you share it?",
    "d2_general_authorization_with_notification": "How do you notify us of changes to your sub-processor list?",
    # D3
    "d3_all_gdpr_rights_listed":          "Do you support all eight GDPR data subject rights? Which do you handle directly vs. pass through to us as controller?",
    "d3_response_timeline_stated":        "What is your committed timeline for responding to data subject requests (DSARs)?",
    "d3_dsar_procedure_documented":       "Can you walk us through your DSAR intake and fulfillment process? Is it documented?",
    "d3_ccpa_rights_listed":              "How do you support CCPA rights — access, deletion, opt-out of sale, and correction — for California residents?",
    "d3_measurable_sla":                  "What percentage of DSARs do you fulfill within the regulatory deadline? Do you track and report DSAR metrics?",
    "d3_automated_dsar_workflow":         "Is your DSAR process manual or automated? What tooling supports it?",
    "d3_identity_verification_process":   "How do you verify the identity of individuals submitting data subject requests before acting on them?",
    "d3_contact_details_provided":        "Who is the designated contact for privacy requests on our behalf, and what is the response channel?",
    # D4
    "d4_sccs_module_specified":               "Which SCC module (Module 2 or 3) applies to our data processing relationship?",
    "d4_tia_documented":                      "Have you conducted a Transfer Impact Assessment for transfers to the US or other third countries? Can you share it or a summary?",
    "d4_supplementary_measures":              "What supplementary technical measures do you apply to data transferred outside the EEA (e.g. encryption, pseudonymisation)?",
    "d4_sub_processor_locations_specified":   "In which countries do your sub-processors process personal data, and how do you ensure adequate protections in each?",
    "d4_monitoring_adequacy_changes":         "How do you monitor changes to EU adequacy decisions or SCC requirements that could affect our transfers?",
    "d4_transfer_mechanism_identified":       "What legal mechanism do you rely on for cross-border data transfers — SCCs, EU-US DPF, or adequacy decision?",
    "d4_transfers_acknowledged":              "Do you transfer any of our personal data outside the EEA or UK? To which countries?",
    # D5
    "d5_specific_sla_hours":             "What is your committed timeline for notifying us of a personal data breach affecting our data?",
    "d5_art33_3_content_commitment":     "Can you confirm your breach notifications will include all Art. 33(3) elements — nature of breach, data categories and volumes, likely consequences, and measures taken?",
    "d5_covers_suspected_incidents":     "Does your breach notification obligation cover suspected incidents, or only confirmed breaches?",
    "d5_evidence_preservation":          "What is your process for preserving forensic evidence during and after a security incident?",
    "d5_phased_reporting":               "Do you support phased breach reporting per Art. 33(4) — an initial notification followed by updates as information becomes available?",
    "d5_awareness_trigger_defined":      "How do you define the moment your 72-hour notification obligation is triggered — discovery, internal escalation, or another event?",
    "d5_sub_processor_breach_cascade":   "What obligation do your sub-processors have to notify you of incidents, and what are your escalation timelines?",
    "d5_notification_obligation_stated": "What specific commitments have you made regarding breach notification timelines in your DPA or privacy policy?",
    "d5_named_response_lead":            "Who is your designated incident response lead, and how do we contact them in an emergency?",
    # D6
    "d6_ai_disclosed_as_separate_purpose": "Do you use our data to train AI or ML models? If so, is this disclosed as a separate processing purpose with its own legal basis?",
    "d6_opt_out_exists":                   "How can we opt our data out of AI/ML training? Is that opt-out retroactive for data already used?",
    "d6_opt_out_prominent":                "Where in your product or DPA can we find and exercise the AI training opt-out — is it available without opening a support ticket?",
    "d6_legal_basis_identified":           "What legal basis do you rely on for processing our data for AI/ML training purposes?",
    "d6_data_categories_specified":        "Which specific categories of our data are used to train or improve AI models?",
    "d6_customer_data_segregation":        "How do you ensure our data is not commingled with other customers' data in your AI training pipelines?",
    "d6_training_data_retention_schedule": "How long do you retain data used for AI model training, and is this separate from your main retention schedule?",
    "d6_dpa_ai_restriction_clause":        "Does your DPA include an explicit clause restricting use of our data for AI training without our prior written consent?",
    "d6_opt_in_for_training":              "Do you require opt-in consent (rather than opt-out) before using our data for AI model training?",
    "d6_data_provenance_documentation":    "Can you provide documentation on the provenance of training data used in models that process our data?",
    "d6_ai_mentioned":                     "In what ways is AI or machine learning applied to our data within your platform?",
    # D7
    "d7_category_specific_retention":         "Can you provide a retention schedule broken down by data category?",
    "d7_deletion_timeframe_specified":         "What is your specific committed timeframe for deleting our data after contract termination (e.g. 30 days)?",
    "d7_deletion_certification":               "Can you provide written certification of data deletion upon request?",
    "d7_backup_copies_addressed":              "How do you handle deletion of our data from backup systems, and what is the timeline for purging those backups?",
    "d7_derived_data_addressed":               "How do you handle deletion of data derived or aggregated from our data — including analytics outputs and model weights?",
    "d7_ai_training_data_retention_separate":  "Do you maintain a separate retention schedule for data used in AI model training, including when model weights derived from our data are deleted?",
    "d7_sub_processor_deletion_obligations":   "What deletion obligations do you impose on sub-processors, and how do you verify their compliance?",
    "d7_general_retention_stated":             "What are your general data retention periods, and what triggers the start of the retention clock?",
    "d7_deletion_at_termination":              "What is your standard process for deleting or returning our data at contract end?",
    # D8
    "d8_processing_annex_detailed":         "Can you provide a detailed processing annex identifying data types, purposes, storage locations, and access controls?",
    "d8_toms_in_annex":                     "Does your DPA include a specific annex detailing your technical and organisational security measures?",
    "d8_measurable_slas":                   "Does your DPA include measurable SLAs for breach notification, deletion, and DSAR assistance?",
    "d8_ai_restriction_clause":             "Does your DPA include a clause explicitly restricting use of our data for AI/ML training?",
    "d8_independent_verification":          "What independent audit reports can you provide — SOC 2 Type II, ISO 27701 certificate, or similar?",
    "d8_ccpa_provisions":                   "Does your DPA include the required CCPA/CPRA service provider provisions?",
    "d8_international_transfers_specified": "Does your DPA specify the legal mechanisms used for each international data transfer?",
    "art28_3h_audit_rights":                "What is the process for exercising our audit rights — do you offer on-site audits, third-party audit report sharing, or questionnaire-based reviews?",
    "art28_3e_dsar_assistance":             "How do you assist us in responding to data subject access requests under Art. 28(3)(e)?",
    "art28_3g_deletion_return":             "What is your process for returning or deleting our data at contract end per Art. 28(3)(g)?",
    "art28_3f_arts32_36_assistance":        "How do you assist us with our Art. 32–36 obligations — security, DPIAs, prior consultation, and breach notification to supervisory authorities?",
}

# ─────────────────────────────────────────────────────────────────────
# Per-dimension contract recommendations (shown for scores ≤ 3)
# ─────────────────────────────────────────────────────────────────────

_DIM_CONTRACT: dict[str, str] = {
    "D1": (
        'Add to DPA Annex I: "Processor shall maintain a data inventory mapping each '
        'category of Personal Data processed to its specific processing purpose and '
        'maximum retention period, consistent with GDPR Art. 5(1)(b) and Art. 5(1)(e). '
        'Processor shall provide Controller with a copy of this inventory on request '
        'and shall update it within 30 days of any material change."'
    ),
    "D2": (
        'Add to DPA §[Sub-processors]: "Processor shall maintain and publish a list of '
        'all Sub-processors, including name, country of processing, and processing '
        'activity. Processor shall provide Controller with at least 30 days\' written '
        'notice before adding or replacing any Sub-processor. Controller may object in '
        'writing within that period; if Processor cannot accommodate the objection, '
        'Controller may terminate the Agreement without penalty. Processor remains '
        'fully liable for the acts of its Sub-processors per GDPR Art. 28(4)."'
    ),
    "D3": (
        'Add to DPA §[Data Subject Rights]: "Processor shall forward to Controller all '
        'data subject requests received within 2 business days of receipt, and shall '
        'provide all reasonably requested assistance to enable Controller to fulfil its '
        'obligations under GDPR Arts. 15–22 and CCPA §1798.100–1798.199. Processor '
        'shall document and report DSAR volumes and response times to Controller on '
        'request."'
    ),
    "D4": (
        'Add to DPA §[International Transfers]: "All transfers of Personal Data to '
        'third countries shall be governed by the Standard Contractual Clauses '
        '(EU) 2021/914 [Module 2 / Module 3] or another mechanism approved under '
        'GDPR Chapter V. Processor shall maintain a Transfer Impact Assessment per '
        'EDPB Recommendations 01/2020 and provide a copy to Controller on request. '
        'Processor shall notify Controller within 30 days of any change to an '
        'applicable transfer mechanism or relevant adequacy decision."'
    ),
    "D5": (
        'Add to DPA §[Breach Notification]: "Processor shall notify Controller within '
        '24 hours of becoming aware of a confirmed or reasonably suspected Personal '
        'Data Breach affecting Controller Data. The initial notification shall include, '
        'to the extent then known, all information required under GDPR Art. 33(3): '
        'the nature of the breach, categories and approximate number of data subjects '
        'and records affected, likely consequences, and measures taken or proposed. '
        'Processor shall provide updates as further information becomes available and '
        'shall preserve all forensic evidence for a minimum of 12 months."'
    ),
    "D6": (
        'Add to DPA §[AI and Machine Learning]: "Processor shall not use Controller '
        'Data to train, fine-tune, evaluate, or improve any AI or machine learning '
        'model without Controller\'s prior written consent. Where AI/ML processing is '
        'separately agreed in writing, Processor shall identify the specific data '
        'categories used, the applicable legal basis, and shall provide a prominent '
        'opt-out mechanism. Processor shall delete or irreversibly anonymise '
        'Controller Data from all training datasets within 30 days of termination, '
        'and shall provide written certification of deletion on request."'
    ),
    "D7": (
        'Add to DPA §[Retention and Deletion]: "Upon expiry or termination of the '
        'Agreement, Processor shall, at Controller\'s election, securely delete or '
        'return all Controller Personal Data within 30 days, including all copies '
        'held by Sub-processors. Data in backup systems shall be purged within the '
        'next scheduled backup rotation cycle, and in any event within 90 days. '
        'Processor shall provide written certification of deletion within 10 business '
        'days of completion. Processor shall maintain a documented, category-specific '
        'retention schedule and provide a copy to Controller on request."'
    ),
    "D8": (
        'Request a revised DPA that: (1) addresses all Art. 28(3)(a)–(h) provisions '
        'with specificity beyond verbatim restatement of the regulation; (2) includes '
        'a detailed processing annex identifying data categories, purposes, and '
        'storage locations; (3) contains a TOMs annex specifying concrete security '
        'controls; (4) includes measurable SLAs for breach notification (≤24 hrs), '
        'deletion (≤30 days), and DSAR assistance (≤5 business days); and (5) '
        'addresses international transfer mechanisms. Reference EDPB Guidelines '
        '7/2020 and the EC Art. 28 SCC template as baseline standards.'
    ),
}

# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

_SCORE_COLOR = ["", "#C0392B", "#E07832", "#D4A017", "#6AAA40", "#27AE60"]
_TIER_COLOR  = {"HIGH": "#C0392B", "MEDIUM": "#D4A017", "LOW": "#27AE60"}
_TIER_BG     = {"HIGH": "#C0392B", "MEDIUM": "#D4A017", "LOW": "#27AE60"}


def _h(s: object) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _label(sig: str) -> str:
    if sig in _SIGNAL_LABELS:
        return _SIGNAL_LABELS[sig]
    parts = sig.split("_", 1)
    raw = parts[1] if len(parts) == 2 else sig
    return raw.replace("_", " ").capitalize()


def _all_gaps(dim_key: str, dr) -> list[str]:
    """Signal slugs required at levels above capped_score not in matched_signals."""
    confirmed = set(dr.matched_signals)
    seen: set[str] = set()
    gaps: list[str] = []
    dim_levels = RUBRIC[dim_key]["levels"]
    for level in range(dr.capped_score + 1, 6):
        if level not in dim_levels:
            continue
        for sig in dim_levels[level]["required_signals"]:
            if sig not in confirmed and sig not in seen:
                seen.add(sig)
                gaps.append(sig)
    return gaps


def _dim_questions(gaps: list[str]) -> list[str]:
    """Up to 3 follow-up questions based on gap signals."""
    seen: set[str] = set()
    qs: list[str] = []
    for sig in gaps:
        if sig in _SIGNAL_QUESTIONS:
            q = _SIGNAL_QUESTIONS[sig]
            if q not in seen:
                seen.add(q)
                qs.append(q)
            if len(qs) >= 3:
                break
    return qs


def _bar_html(score: int, color: str, width: int = 80) -> str:
    pct = score / 5 * 100
    return (
        f'<div style="width:{width}px;height:7px;background:#D4C9B8;border-radius:3px;display:inline-block;vertical-align:middle">'
        f'<div style="width:{pct:.0f}%;height:7px;background:{color};border-radius:3px"></div>'
        f'</div>'
    )


# ─────────────────────────────────────────────────────────────────────
# Dimension section HTML
# ─────────────────────────────────────────────────────────────────────

def _dim_section(dim_key: str, dr, result_red_flags: list[dict]) -> str:
    score = dr.capped_score
    color = _SCORE_COLOR[min(score, 5)]
    wt_badge = f' <span style="color:#8B5A2B;font-size:10px">×{dr.weight:.1f}</span>' if dr.weight != 1.0 else ""

    # ── Evidence found ────────────────────────────────────────────────
    ev_items = "".join(
        f'<li class="ev-y">✓&nbsp; {_h(_label(s))}</li>'
        for s in dr.matched_signals
    )
    ev_html = (
        f'<div class="sub-sec"><h4 class="sh">Evidence found</h4><ul class="ev-list">{ev_items}</ul></div>'
        if dr.matched_signals else
        '<div class="sub-sec"><h4 class="sh">Evidence found</h4>'
        '<p class="none-p">No signals confirmed in retrieved documents.</p></div>'
    )

    # ── Gaps identified ───────────────────────────────────────────────
    gaps = _all_gaps(dim_key, dr)
    gap_items = "".join(
        f'<li class="ev-n">✗&nbsp; {_h(_label(s))}</li>'
        for s in gaps
    )
    gap_html = (
        f'<div class="sub-sec"><h4 class="sh">Gaps identified</h4><ul class="ev-list">{gap_items}</ul></div>'
        if gaps else
        '<div class="sub-sec"><h4 class="sh">Gaps identified</h4>'
        '<p class="none-p">No gaps — dimension is fully evidenced.</p></div>'
    )

    # ── Red flags ─────────────────────────────────────────────────────
    dim_rfs = [rf for rf in result_red_flags if dim_key in rf["dims"]]
    rf_html = ""
    if dim_rfs:
        rf_items = ""
        for rf in dim_rfs:
            match_text = _h(rf.get("match", "")[:100])
            rf_items += (
                f'<div class="rf-item">'
                f'<div class="rf-sym">⚠</div>'
                f'<div>'
                f'<div class="rf-q">&ldquo;{match_text}&rdquo;</div>'
                f'<div class="rf-l">{_h(rf["label"])}</div>'
                f'<div class="rf-c">→ Score capped at {rf["ceiling"]}/5</div>'
                f'</div></div>'
            )
        rf_html = f'<div class="sub-sec rf-sec"><h4 class="sh">Red flags triggered</h4>{rf_items}</div>'

    # ── Vendor questions ──────────────────────────────────────────────
    questions = _dim_questions(gaps)
    q_html = ""
    if questions:
        q_items = "".join(f'<li>{_h(q)}</li>' for q in questions)
        q_html = (
            f'<div class="sub-sec">'
            f'<h4 class="sh">Vendor follow-up questions</h4>'
            f'<ul class="q-list">{q_items}</ul>'
            f'</div>'
        )

    # ── Contract recommendation (scores ≤ 3 only) ─────────────────────
    cr_html = ""
    if score <= 3 and dim_key in _DIM_CONTRACT:
        cr_html = (
            f'<div class="sub-sec">'
            f'<h4 class="sh">Contract recommendation</h4>'
            f'<div class="cr-box">{_h(_DIM_CONTRACT[dim_key])}</div>'
            f'</div>'
        )

    bar = _bar_html(score, color, width=72)

    return f"""
<details class="dim-det">
  <summary class="dim-sum">
    <span class="dk-lbl">{_h(dim_key)}{wt_badge}</span>
    <span class="dn-lbl">{_h(dr.name)}</span>
    <span class="bar-cell">{bar}</span>
    <span class="ds-lbl" style="color:{color}">{score}/5</span>
    <span class="dl-lbl" style="color:{color}">{_h(dr.level_label)}</span>
    <span class="arr">▶</span>
  </summary>
  <div class="dim-body">
    <div class="dim-grid">
      <div>{ev_html}{gap_html}</div>
      <div>{rf_html}{q_html}{cr_html}</div>
    </div>
  </div>
</details>"""


# ─────────────────────────────────────────────────────────────────────
# Team summary panels
# ─────────────────────────────────────────────────────────────────────

def _team_summary(result, assessment) -> str:
    _GRC_DECISION = {
        "HIGH":   ("Escalate",                "#C0392B", "Do not proceed to contract. Escalate to security review board."),
        "MEDIUM": ("Approve with conditions",  "#D4A017", "Address flagged gaps before go-live. Negotiate DPA improvements."),
        "LOW":    ("Approve",                  "#27AE60", "Standard onboarding process. Confirm DPA is on file and current."),
    }
    action, a_color, detail = _GRC_DECISION.get(result.risk_tier, ("Review", "#8B5A2B", ""))

    high_dims     = [k for k, dr in result.dimensions.items() if dr.capped_score <= 2]
    def_dims      = [k for k, dr in result.dimensions.items() if dr.capped_score == 3]
    total_gaps    = sum(len(_all_gaps(k, dr)) for k, dr in result.dimensions.items())
    reassess_days = {"HIGH": 90, "MEDIUM": 180, "LOW": 365}.get(result.risk_tier, 365)
    reassess_date = (datetime.date.today() + datetime.timedelta(days=reassess_days)).strftime("%B %Y")

    def row(k: str, v: str, vc: str = "") -> str:
        style = f' style="color:{vc};font-weight:700"' if vc else ""
        return f'<div class="tp-row"><span class="tp-k">{_h(k)}</span><span class="tp-v"{style}>{v}</span></div>'

    grc = f"""<div class="tp">
  <div class="tp-hdr" style="background:#4A2E1A">FOR GRC</div>
  <div class="tp-body">
    {row("Decision", _h(action), a_color)}
    {row("Detail", _h(detail))}
    {row("Risk tier", f'{result.risk_tier}  {result.weighted_average}/5.0', a_color)}
    {row("High-risk dims (≤2)", _h(", ".join(high_dims)) if high_dims else "None")}
    {row("Deficient dims (3)", _h(", ".join(def_dims)) if def_dims else "None")}
    {row("Total signal gaps", str(total_gaps))}
    {row("Re-assess by", reassess_date)}
  </div>
</div>"""

    legal_items = ""
    for dim_key, dr in result.dimensions.items():
        if dr.capped_score <= 3 and dim_key in _DIM_CONTRACT:
            legal_items += (
                f'<div class="lc-item">'
                f'<div class="lc-hdr">{_h(dim_key)} — {_h(dr.name)} &nbsp;<span style="color:#8B5A2B">(score {dr.capped_score}/5)</span></div>'
                f'<div class="lc-body">{_h(_DIM_CONTRACT[dim_key])}</div>'
                f'</div>'
            )
    if not legal_items:
        legal_items = '<p class="none-p">No contract changes required — all dimensions at score 4+.</p>'

    legal = f"""<div class="tp">
  <div class="tp-hdr" style="background:#1A3A2A">FOR LEGAL</div>
  <div class="tp-body">{legal_items}</div>
</div>"""

    sec_dims = ["D5", "D6", "D8"]
    sec_rows = ""
    for dk in sec_dims:
        if dk in result.dimensions:
            dr = result.dimensions[dk]
            c = _SCORE_COLOR[min(dr.capped_score, 5)]
            sec_rows += row(f"{dk} {dr.name}", f"{dr.capped_score}/5 — {_h(dr.level_label)}", c)

    fw = result.framework_evidence
    fw_text = ", ".join(fw) if fw else "None evidenced"
    has_soc2 = any("soc2" in f.lower() for f in fw)
    has_iso  = any("iso_277" in f.lower() or "iso_2700" in f.lower() for f in fw)

    reqs = ""
    if not has_soc2:
        reqs += '<div class="sec-req">→ Request SOC 2 Type II report (with Privacy TSC if available)</div>'
    if not has_iso:
        reqs += '<div class="sec-req">→ Request ISO 27701 or ISO 27001 certificate</div>'

    ai_flags = [rf for rf in result.red_flags if "D6" in rf["dims"]]
    breach_flags = [rf for rf in result.red_flags if "D5" in rf["dims"]]

    af_html = "".join(f'<div class="sec-flag">⚠ {_h(rf["label"])}</div>' for rf in ai_flags) or "<span style='color:#6B5B4E'>None</span>"
    bf_html = "".join(f'<div class="sec-flag">⚠ {_h(rf["label"])}</div>' for rf in breach_flags) or "<span style='color:#6B5B4E'>None</span>"

    security = f"""<div class="tp">
  <div class="tp-hdr" style="background:#1A2A4A">FOR SECURITY</div>
  <div class="tp-body">
    {sec_rows}
    {row("Frameworks evidenced", _h(fw_text))}
    {row("AI/ML flags", af_html)}
    {row("Breach response flags", bf_html)}
    {'<div class="tp-gap">' + reqs + '</div>' if reqs else ''}
  </div>
</div>"""

    return f'<div class="team-wrap">{grc}{legal}{security}</div>'


# ─────────────────────────────────────────────────────────────────────
# Vendor email template
# ─────────────────────────────────────────────────────────────────────

def _email_template(vendor: str, result) -> str:
    all_qs: list[str] = []
    seen: set[str] = set()
    for dim_key, dr in result.dimensions.items():
        gaps = _all_gaps(dim_key, dr)
        for sig in gaps:
            if sig in _SIGNAL_QUESTIONS:
                q = _SIGNAL_QUESTIONS[sig]
                if q not in seen:
                    seen.add(q)
                    all_qs.append(q)

    numbered = "\n".join(f"{i}. {q}" for i, q in enumerate(all_qs, 1))

    body = f"""Subject: Privacy & Security Due Diligence — {vendor} Onboarding Review

Dear [Vendor Privacy/Legal Team],

As part of our vendor onboarding process, we are conducting a privacy and security due diligence review for {vendor}. We have reviewed your publicly available privacy documentation and have the following follow-up questions.

Please provide written responses by [DATE]:

{numbered}

Please also provide copies of the following:
  • Most recent SOC 2 Type II audit report (Privacy Trust Services Criteria preferred)
  • Current signed Data Processing Agreement (or your standard template)
  • Sub-processor list with countries of processing
  • ISO 27701 certificate (if applicable)
  • Any Transfer Impact Assessment (TIA) in place for EEA data transfers

We aim to complete our review within [X] business days of receiving your full responses. Please confirm receipt of this request and your expected response timeline.

Thank you for your cooperation.

Best regards,
[Your Name]
[Title] | GRC / Privacy Team
[Company]
[Email]"""

    return (
        f'<details class="email-det">'
        f'<summary class="email-sum">Vendor Follow-up Email Template</summary>'
        f'<div class="email-body"><pre>{_h(body)}</pre></div>'
        f'</details>'
    )


# ─────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────

def write_html_report(
    path: pathlib.Path,
    assessment,
    timestamp: str | None = None,
) -> None:
    """Write a self-contained branded HTML report for a PrivacyAssessment."""
    result  = assessment.result
    sources = assessment.sources
    ts = timestamp or datetime.datetime.now().strftime("%Y-%m-%d %H:%M UTC")

    tier_color = _TIER_COLOR.get(result.risk_tier, "#8B5A2B")

    # ── Summary stats bar ─────────────────────────────────────────────
    high_count = sum(1 for dr in result.dimensions.values() if dr.capped_score <= 2)
    def_count  = sum(1 for dr in result.dimensions.values() if dr.capped_score == 3)
    stats_html = (
        f'<div class="stats-bar">'
        f'<span>{len(result.dimensions)} dimensions</span>'
        f'<span class="sep">·</span>'
        f'<span style="color:#C0392B;font-weight:{"700" if high_count else "400"}">'
        f'{high_count} high-risk</span>'
        f'<span class="sep">·</span>'
        f'<span style="color:#D4A017;font-weight:{"700" if def_count else "400"}">'
        f'{def_count} deficient</span>'
        f'<span class="sep">·</span>'
        f'<span>{len(result.red_flags)} red flag{"s" if len(result.red_flags) != 1 else ""}</span>'
        f'<span class="sep">·</span>'
        f'<span>{len(sources)} page{"s" if len(sources) != 1 else ""} analysed</span>'
        f'</div>'
    )

    # ── Dimension sections ────────────────────────────────────────────
    dims_html = "\n".join(
        _dim_section(k, dr, result.red_flags)
        for k, dr in result.dimensions.items()
    )

    # ── Pages analysed ────────────────────────────────────────────────
    src_rows = "".join(
        f'<tr><td>{i}</td>'
        f'<td><a href="{_h(s.url)}">{_h(s.url)}</a></td>'
        f'<td>{s.chars:,}</td><td>{_h(s.via)}</td></tr>'
        for i, s in enumerate(sources, 1)
    )

    # ── Frameworks ────────────────────────────────────────────────────
    fw_html = (
        "<ul class='fw-list'>"
        + "".join(f"<li>✓&nbsp; {_h(f)}</li>" for f in result.framework_evidence)
        + "</ul>"
        if result.framework_evidence else '<p class="none-p">None detected.</p>'
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bandit — {_h(result.vendor)}</title>
<style>
:root{{--cr:#F4EFE4;--br:#8B5A2B;--ink:#1A1510;--mu:#6B5B4E;--bd:#D4C9B8}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'SF Mono','Fira Code','Cascadia Code','Courier New',monospace;
  font-size:13px;line-height:1.65;max-width:1040px;margin:0 auto;
  padding:40px 24px 80px;color:var(--ink);background:var(--cr)}}
a{{color:var(--br);text-decoration:none}}
a:hover{{text-decoration:underline}}

/* ── Header ── */
.hdr{{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;
  border-bottom:2px solid var(--br);padding-bottom:20px;margin-bottom:16px;flex-wrap:wrap}}
.brand{{color:var(--br);font-size:10px;letter-spacing:.18em;text-transform:uppercase;margin-bottom:6px}}
.vn{{font-size:22px;font-weight:700;margin-bottom:10px}}
.meta{{font-size:12px;color:var(--mu);line-height:2}}
.tb{{display:inline-block;padding:4px 14px;border-radius:3px;font-weight:700;
  font-size:13px;letter-spacing:.06em;margin-bottom:8px;color:#fff}}
.sb{{font-size:32px;font-weight:700}}.sd{{font-size:16px;color:var(--mu)}}

/* ── Stats bar ── */
.stats-bar{{font-size:11px;color:var(--mu);margin-bottom:24px;display:flex;
  flex-wrap:wrap;gap:6px;align-items:center}}
.sep{{color:var(--bd)}}

/* ── Section headings ── */
h2{{font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;
  color:var(--br);border-bottom:1px solid var(--bd);padding-bottom:6px;
  margin:32px 0 12px}}

/* ── Collapsible dimensions ── */
.dim-det{{border:1px solid var(--bd);border-radius:4px;margin-bottom:6px}}
.dim-sum{{display:flex;align-items:center;gap:10px;padding:10px 14px;
  cursor:pointer;list-style:none;background:rgba(139,90,43,.04);
  border-radius:4px;user-select:none}}
.dim-sum::-webkit-details-marker{{display:none}}
.dk-lbl{{font-weight:700;color:var(--br);min-width:52px;flex-shrink:0}}
.dn-lbl{{flex:1;color:var(--ink)}}
.bar-cell{{flex-shrink:0}}
.ds-lbl{{width:36px;text-align:right;font-weight:700;flex-shrink:0}}
.dl-lbl{{width:110px;font-size:11px;flex-shrink:0}}
.arr{{margin-left:auto;font-size:9px;color:var(--mu);transition:transform .15s;flex-shrink:0}}
details[open] .arr{{transform:rotate(90deg)}}
.dim-body{{padding:12px 16px 16px}}
.dim-grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}
@media(max-width:640px){{.dim-grid{{grid-template-columns:1fr}}}}

/* ── Sub-sections ── */
.sub-sec{{margin-top:16px}}
.sh{{font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;
  color:var(--br);margin-bottom:8px}}
.ev-list{{list-style:none;padding:0}}
.ev-list li{{padding:3px 0;font-size:12px}}
.ev-y{{color:#1A5C2A}}
.ev-n{{color:#7A5500}}
.none-p{{color:var(--mu);font-style:italic;font-size:12px}}

/* ── Red flags (in dimension) ── */
.rf-sec{{background:rgba(139,26,26,.05);border-left:3px solid #8B1A1A;
  padding:10px 12px;border-radius:0 4px 4px 0}}
.rf-item{{display:flex;gap:10px;margin-bottom:10px}}
.rf-item:last-child{{margin-bottom:0}}
.rf-sym{{color:#8B1A1A;font-size:15px;flex-shrink:0}}
.rf-q{{color:#5A1A1A;font-style:italic;font-size:12px;margin-bottom:3px}}
.rf-l{{font-weight:700;color:#8B1A1A;font-size:11px}}
.rf-c{{color:var(--mu);font-size:11px}}

/* ── Vendor questions ── */
.q-list{{list-style:none;padding:0}}
.q-list li{{padding:5px 0 5px 12px;border-left:2px solid var(--bd);
  margin-bottom:4px;font-size:12px;color:var(--ink)}}

/* ── Contract recommendation ── */
.cr-box{{background:#E8F0FE;border:1px solid #B0C8F8;border-radius:4px;
  padding:10px 14px;color:#1A2A5A;font-style:italic;line-height:1.7;font-size:12px}}

/* ── Frameworks / Sources tables ── */
.fw-list{{list-style:none;padding:0}}
.fw-list li{{padding:5px 0;border-bottom:1px solid var(--bd);color:#1A5C2A}}
table{{width:100%;border-collapse:collapse}}
td,th{{padding:7px 10px;border-bottom:1px solid var(--bd);vertical-align:top;text-align:left;font-size:12px}}
th{{background:rgba(139,90,43,.07);font-weight:700;font-size:9px;
  letter-spacing:.08em;text-transform:uppercase;color:var(--br)}}

/* ── Team summary ── */
.team-wrap{{margin-top:8px}}
.tp{{display:block;width:100%;border:1px solid var(--bd);border-radius:4px;overflow:hidden;margin-bottom:16px}}
.tp-hdr{{padding:8px 14px;font-size:9px;font-weight:700;letter-spacing:.16em;
  text-transform:uppercase;color:#fff}}
.tp-body{{padding:12px 14px}}
.tp-row{{display:flex;gap:8px;padding:5px 0;border-bottom:1px solid var(--bd);
  align-items:flex-start}}
.tp-k{{font-size:10px;color:var(--mu);min-width:120px;flex-shrink:0;padding-top:1px}}
.tp-v{{font-size:12px;flex:1}}
.tp-gap{{margin-top:8px;padding-top:8px;border-top:1px solid var(--bd)}}
.lc-item{{margin-bottom:12px;padding-bottom:12px;border-bottom:1px solid var(--bd)}}
.lc-item:last-child{{margin-bottom:0;border-bottom:none}}
.lc-hdr{{font-size:11px;font-weight:700;color:var(--br);margin-bottom:5px}}
.lc-body{{font-style:italic;color:#1A2A5A;background:#E8F0FE;padding:8px 10px;
  border-radius:3px;font-size:11px;line-height:1.6}}
.sec-req{{color:#2A4A7A;font-size:11px;padding:3px 0}}
.sec-flag{{color:#8B1A1A;font-size:11px;padding:2px 0}}

/* ── Email template ── */
.email-det{{border:1px solid var(--bd);border-radius:4px;margin-top:32px}}
.email-sum{{padding:12px 16px;cursor:pointer;font-size:10px;font-weight:700;
  letter-spacing:.14em;text-transform:uppercase;color:var(--br);
  background:rgba(139,90,43,.04);list-style:none;display:flex;
  justify-content:space-between}}
.email-sum::-webkit-details-marker{{display:none}}
.email-sum::after{{content:"▶";font-size:9px;color:var(--mu);transition:transform .15s}}
details[open] .email-sum::after{{transform:rotate(90deg)}}
.email-body{{padding:16px}}
.email-body pre{{white-space:pre-wrap;font-size:12px;line-height:1.75;
  color:var(--ink);background:var(--cr)}}

/* ── Footer ── */
.footer{{margin-top:56px;padding-top:14px;border-top:1px solid var(--bd);
  font-size:11px;color:var(--mu);display:flex;justify-content:space-between;
  flex-wrap:wrap;gap:8px}}

/* ── Print ── */
@media print{{
  details > *:not(summary){{display:block !important}}
  .dim-det, .email-det{{page-break-inside:avoid}}
  .tp{{margin-bottom:12px}}
}}
</style>
</head>
<body>

<div class="hdr">
  <div>
    <div class="brand">Bandit · Privacy Risk Assessment</div>
    <div class="vn">{_h(result.vendor)}</div>
    <div class="meta">Assessed: {_h(ts)}&nbsp;·&nbsp;Rubric v{_h(result.version)}</div>
  </div>
  <div style="text-align:right">
    <div><span class="tb" style="background:{tier_color}">{result.risk_tier} RISK</span></div>
    <div><span class="sb" style="color:{tier_color}">{result.weighted_average}</span><span class="sd"> / 5.0</span></div>
  </div>
</div>

{stats_html}

<h2>Dimension Scores</h2>
{dims_html}

<h2>Framework Certifications</h2>
{fw_html}

<h2>Team Summary</h2>
{_team_summary(result, assessment)}

<h2>Pages Analysed</h2>
<table>
  <thead><tr><th>#</th><th>URL</th><th>Chars</th><th>Via</th></tr></thead>
  <tbody>{src_rows}</tbody>
</table>

{_email_template(result.vendor, result)}

<div class="footer">
  <span>Generated by <a href="https://github.com/conorrusso/bandit">Bandit</a> v1.0.0 &nbsp;·&nbsp; Rubric v{_h(result.version)}</span>
  <span>{_h(ts)}</span>
</div>

</body>
</html>"""

    path.write_text(html, encoding="utf-8")
