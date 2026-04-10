"""
Legal Bandit — Contract Gap Analysis Agent
============================================
Reads vendor contracts (DPA, MSA, SCCs) and:

1. Runs GDPR Art. 28(3)(a)-(h) checklist against DPA
2. Extracts verbatim contract language per provision
3. Identifies gaps and vague language
4. Detects conflicts where policy claims more than DPA commits
5. Updates D2, D5, D7, D8 scores based on contract reality
6. Generates data for the standalone legal redline brief

Only runs when DPA or MSA documents are available.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from core.agents.legal_bandit_models import (
    LegalBanditResult, ProvisionAssessment,
    ProvisionStatus, ChangeType, PolicyContractConflict,
    ConflictSeverity, DimensionContractScore,
    MSAAssessment, SCCAssessment,
)
from core.documents.classifier import DocumentType
from core.documents.legal_prompts import (
    get_dpa_legal_prompt, get_msa_legal_prompt,
    get_scc_legal_prompt,
)

# Dimensions primarily assessed from contracts
CONTRACT_PRIMARY_DIMS = {"D2", "D5", "D7", "D8"}

# Redline templates per provision gap
REDLINE_TEMPLATES = {
    "art28_3c_security": (
        'Add to DPA Annex II (Technical and Organisational '
        'Measures): "Processor shall implement and maintain '
        'technical and organisational measures including as '
        'a minimum: (a) AES-256 encryption at rest; '
        '(b) TLS 1.2 or higher in transit; (c) multi-factor '
        'authentication for all privileged access; (d) annual '
        'penetration testing by a qualified third party, '
        'results available to Controller on request under NDA; '
        '(e) ISO 27001 certification or equivalent maintained '
        'throughout the term."'
    ),
    "breach_notification": (
        'Add to DPA §[Breach Notification]: "Processor shall '
        'notify Controller within 24 hours of becoming aware '
        'of a confirmed or reasonably suspected Personal Data '
        'Breach affecting Controller Data. The initial '
        'notification shall include, to the extent then known, '
        'all information required under GDPR Art. 33(3). '
        'Processor shall provide updates as further information '
        'becomes available and shall preserve all forensic '
        'evidence for a minimum of 12 months."'
    ),
    "art28_3d_sub_processors": (
        'Add to DPA §[Sub-processors]: "Processor shall obtain '
        'prior written consent before engaging any new '
        'Sub-processor. Processor shall provide Controller '
        'with at least 30 days written notice of any intended '
        'change. Controller may object in writing within that '
        'period; if Processor cannot accommodate the objection, '
        'Controller may terminate without penalty. Processor '
        'remains fully liable for Sub-processor acts per '
        'GDPR Art. 28(4)."'
    ),
    "art28_3g_deletion_return": (
        'Add to DPA §[Deletion and Return]: "Upon expiry or '
        'termination, Processor shall at Controller\'s election '
        'securely delete or return all Controller Personal Data '
        'within 30 days, including copies held by Sub-processors. '
        'Backup copies shall be purged within the next scheduled '
        'rotation cycle, and in any event within 90 days. '
        'Processor shall provide written certification of '
        'deletion within 10 business days of completion."'
    ),
    "art28_3h_audit_rights": (
        'Add to DPA §[Audit Rights]: "Controller may conduct '
        'or commission audits of Processor\'s compliance with '
        'this DPA on reasonable notice (not less than 30 days) '
        'and no more than once per calendar year, or at any '
        'time following a confirmed Personal Data Breach. '
        'Audit rights extend to Sub-processors. Processor '
        'shall provide reasonable cooperation at its cost."'
    ),
    "ai_ml_restriction": (
        'Add to DPA §[AI and Machine Learning]: "Processor '
        'shall not use Controller Data to train, fine-tune, '
        'evaluate, or improve any AI or machine learning model '
        'without Controller\'s prior written consent. Processor '
        'shall delete or irreversibly anonymise Controller Data '
        'from all training datasets within 30 days of '
        'termination and provide written certification."'
    ),
}

# Enforcement precedents per provision
ENFORCEMENT_PRECEDENTS = {
    "art28_3c_security": (
        "British Airways £20M ICO (2020) — inadequate "
        "technical measures"
    ),
    "breach_notification": (
        "Meta €251M DPC (December 2024) — breach "
        "notification failures"
    ),
    "art28_3d_sub_processors": (
        "CRITEO €40M CNIL (2023) — sub-processor "
        "management failures"
    ),
    "art28_3g_deletion_return": (
        "Netflix €4.75M Dutch DPA (December 2024) — "
        "retention and deletion failures"
    ),
    "ai_ml_restriction": (
        "FTC Everalbum disgorgement (2021) — AI "
        "training without consent"
    ),
}


class LegalBandit:

    def __init__(self, llm_provider):
        self.provider = llm_provider

    def assess(
        self,
        vendor_name: str,
        documents: list,
        policy_signals: dict,
        policy_scores: dict,
    ) -> LegalBanditResult | None:
        """
        Run Legal Bandit assessment.
        Returns None if no contract documents found.

        documents: list of IngestedDocument from v1.1
        policy_signals: evidence dict from Privacy Bandit
        policy_scores: dimension scores from rubric
        """
        dpa_doc = self._find_doc(documents, DocumentType.DPA)
        msa_doc = self._find_doc(documents, DocumentType.MSA)
        scc_doc = self._find_doc(documents, DocumentType.SCCS)

        # Only run if at least DPA or MSA found
        if not dpa_doc and not msa_doc:
            return None

        result = LegalBanditResult(
            vendor_name=vendor_name,
            assessment_date=datetime.now().strftime("%Y-%m-%d"),
            dpa_assessed=bool(dpa_doc),
            msa_assessed=bool(msa_doc),
            scc_assessed=bool(scc_doc),
            dpa_source=dpa_doc.file_name if dpa_doc else None,
            msa_source=msa_doc.file_name if msa_doc else None,
            scc_source=scc_doc.file_name if scc_doc else None,
        )

        # Step 1 — Extract DPA provisions
        if dpa_doc:
            dpa_data = self._extract_dpa(vendor_name, dpa_doc.text)
            result.provisions = self._parse_provisions(dpa_data)

        # Step 2 — Extract MSA terms
        if msa_doc:
            msa_data = self._extract_msa(vendor_name, msa_doc.text)
            result.msa = self._parse_msa(msa_data)

        # Step 3 — Extract SCC assessment
        if scc_doc:
            scc_data = self._extract_scc(vendor_name, scc_doc.text)
            result.sccs = self._parse_scc(scc_data)

        # Step 4 — Calculate contract scores per dimension
        result.dimension_scores = self._calculate_scores(
            result, policy_scores
        )

        # Step 5 — Detect policy/contract conflicts
        result.conflicts = self._detect_conflicts(
            result, policy_signals, policy_scores
        )

        # Step 6 — Calculate summary counts
        result.required_changes = len([
            p for p in result.provisions
            if p.change_type == ChangeType.REQUIRED
        ])
        result.recommended_changes = len([
            p for p in result.provisions
            if p.change_type == ChangeType.RECOMMENDED
        ])
        result.acceptable_provisions = len([
            p for p in result.provisions
            if p.change_type == ChangeType.ACCEPTABLE
        ])
        result.conflicts_count = len(result.conflicts)

        # Step 7 — Check auto-escalation
        high_conflicts = [
            c for c in result.conflicts
            if c.severity == ConflictSeverity.HIGH
        ]
        if high_conflicts:
            result.escalation_required = True
            result.escalation_reasons = [
                f"Policy/contract conflict on {c.dimension}: "
                f"{c.policy_claim} not backed by DPA"
                for c in high_conflicts
            ]

        return result

    def _find_doc(self, documents, doc_type):
        """Find first successfully extracted document of type."""
        for doc in documents:
            if (doc.doc_type == doc_type
                    and doc.extraction_ok
                    and doc.char_count > 1000):
                return doc
        return None

    def _extract_dpa(self, vendor_name: str, text: str) -> dict:
        prompt = get_dpa_legal_prompt(vendor_name, text)
        raw = self.provider.complete_json(prompt, max_tokens=6000)
        return raw if isinstance(raw, dict) else {}

    def _extract_msa(self, vendor_name: str, text: str) -> dict:
        prompt = get_msa_legal_prompt(vendor_name, text)
        raw = self.provider.complete_json(prompt, max_tokens=6000)
        return raw if isinstance(raw, dict) else {}

    def _extract_scc(self, vendor_name: str, text: str) -> dict:
        prompt = get_scc_legal_prompt(vendor_name, text)
        raw = self.provider.complete_json(prompt, max_tokens=6000)
        return raw if isinstance(raw, dict) else {}

    def _parse_provisions(
        self, dpa_data: dict
    ) -> list[ProvisionAssessment]:
        provisions = []

        PROVISION_MAP = {
            "art28_3a_instructions": (
                "Processing on documented instructions",
                "GDPR Art. 28(3)(a)",
            ),
            "art28_3b_confidentiality": (
                "Confidentiality obligations",
                "GDPR Art. 28(3)(b)",
            ),
            "art28_3c_security": (
                "Security measures",
                "GDPR Art. 28(3)(c), Art. 32",
            ),
            "art28_3d_sub_processors": (
                "Sub-processor management",
                "GDPR Art. 28(3)(d), Art. 28(4)",
            ),
            "art28_3e_dsar_assistance": (
                "Data subject rights assistance",
                "GDPR Art. 28(3)(e)",
            ),
            "art28_3f_dpia_assistance": (
                "DPIA assistance",
                "GDPR Art. 28(3)(f), Art. 35-36",
            ),
            "art28_3g_deletion_return": (
                "Deletion or return on termination",
                "GDPR Art. 28(3)(g)",
            ),
            "art28_3h_audit_rights": (
                "Audit rights",
                "GDPR Art. 28(3)(h)",
            ),
            "breach_notification": (
                "Breach notification",
                "GDPR Art. 33, Art. 28(3)(f)",
            ),
            "ai_ml_restriction": (
                "AI/ML data usage restriction",
                "EU AI Act 2024, FTC guidance",
            ),
            "international_transfers": (
                "International transfer mechanisms",
                "GDPR Arts. 44-50",
            ),
        }

        for key, (name, ref) in PROVISION_MAP.items():
            data = dpa_data.get(key, {})
            if not isinstance(data, dict):
                continue

            present = data.get("present", False)
            specific = data.get("specific", False)
            gaps = data.get("gaps", [])
            vague = data.get("vague_phrases", [])

            # Determine status
            if not present:
                status = ProvisionStatus.ABSENT
            elif present and specific and not vague:
                status = ProvisionStatus.PRESENT_SPECIFIC
            else:
                status = ProvisionStatus.PRESENT_VAGUE

            # Determine change type
            core_provisions = {
                "art28_3a_instructions",
                "art28_3c_security",
                "art28_3d_sub_processors",
                "art28_3g_deletion_return",
                "art28_3h_audit_rights",
                "breach_notification",
            }
            if status == ProvisionStatus.ABSENT:
                if key in core_provisions:
                    change_type = ChangeType.REQUIRED
                else:
                    change_type = ChangeType.RECOMMENDED
            elif status == ProvisionStatus.PRESENT_VAGUE:
                if key in {"art28_3c_security", "breach_notification"}:
                    change_type = ChangeType.REQUIRED
                else:
                    change_type = ChangeType.RECOMMENDED
            else:
                change_type = ChangeType.ACCEPTABLE

            provision = ProvisionAssessment(
                provision_id=key,
                provision_name=name,
                regulatory_ref=ref,
                status=status,
                verbatim_quote=data.get("verbatim_quote"),
                section_reference=data.get("section_reference"),
                sla_value=data.get(
                    "sla_hours", data.get("deletion_timeframe_days")
                ),
                gaps=gaps,
                vague_phrases=vague,
                change_type=change_type,
                redline_recommendation=REDLINE_TEMPLATES.get(key),
                enforcement_precedent=ENFORCEMENT_PRECEDENTS.get(key),
            )
            provisions.append(provision)

        return provisions

    def _parse_msa(self, msa_data: dict) -> MSAAssessment:
        liability = msa_data.get("liability_cap", {})
        indemnification = msa_data.get("indemnification", {})
        ownership = msa_data.get("data_ownership", {})
        termination = msa_data.get("termination", {})
        concerns = list(msa_data.get("concerns", []))

        if liability.get("excludes_data_breaches"):
            concerns.append(
                "Liability cap explicitly excludes "
                "data breach claims — extremely high risk"
            )

        return MSAAssessment(
            liability_cap_excludes_breaches=liability.get(
                "excludes_data_breaches"
            ),
            liability_cap_value=liability.get("cap_value"),
            indemnification_for_breaches=indemnification.get(
                "covers_data_breaches"
            ),
            data_ownership_clause=ownership.get("controller_owns_data"),
            governing_law=msa_data.get("governing_law"),
            dispute_resolution=msa_data.get("dispute_resolution"),
            termination_for_cause_includes_breach=termination.get(
                "for_cause_includes_breach"
            ),
            data_return_on_termination_days=termination.get(
                "data_return_days"
            ),
            survival_clauses=termination.get("survival_clauses", []),
            verbatim_liability_clause=liability.get("verbatim_quote"),
            verbatim_termination_clause=termination.get("verbatim_quote"),
            concerns=concerns,
        )

    def _parse_scc(self, scc_data: dict) -> SCCAssessment:
        version = scc_data.get("scc_version", "")
        outdated = "2010" in str(version) or "2004" in str(version)
        return SCCAssessment(
            scc_version=version,
            module=scc_data.get("module"),
            properly_executed=scc_data.get("properly_executed"),
            annex_1a_completed=scc_data.get("annex_1a_completed"),
            annex_1b_completed=scc_data.get("annex_1b_completed"),
            annex_2_completed=scc_data.get("annex_2_completed"),
            annex_3_completed=scc_data.get("annex_3_completed"),
            tia_referenced=scc_data.get("tia_referenced"),
            outdated=outdated,
        )

    def _calculate_scores(
        self,
        result: LegalBanditResult,
        policy_scores: dict,
    ) -> list[DimensionContractScore]:
        """Calculate contract-based scores for each dimension.
        Contract score is authoritative for D2, D5, D7, D8.
        """
        scores = []

        dim_provision_map = {
            "D2": ["art28_3d_sub_processors"],
            "D5": ["breach_notification", "art28_3f_dpia_assistance"],
            "D7": ["art28_3g_deletion_return"],
            "D8": [
                "art28_3a_instructions",
                "art28_3b_confidentiality",
                "art28_3c_security",
                "art28_3d_sub_processors",
                "art28_3e_dsar_assistance",
                "art28_3f_dpia_assistance",
                "art28_3g_deletion_return",
                "art28_3h_audit_rights",
            ],
        }

        provision_lookup = {
            p.provision_id: p for p in result.provisions
        }

        for dim, provision_ids in dim_provision_map.items():
            policy_score = policy_scores.get(dim, 1)
            relevant = [
                provision_lookup[pid]
                for pid in provision_ids
                if pid in provision_lookup
            ]

            if not relevant:
                continue

            contract_score = self._score_from_provisions(dim, relevant)

            if dim in CONTRACT_PRIMARY_DIMS:
                final_score = contract_score
                final_source = "contract"
            else:
                final_score = max(policy_score, contract_score)
                final_source = (
                    "contract" if contract_score > policy_score
                    else "policy"
                )

            changed = final_score != policy_score
            direction = (
                "up" if final_score > policy_score
                else "down" if final_score < policy_score
                else "unchanged"
            )

            scores.append(DimensionContractScore(
                dimension=dim,
                policy_score=policy_score,
                contract_score=contract_score,
                final_score=final_score,
                final_source=final_source,
                score_changed=changed,
                score_direction=direction,
                evidence_summary=self._summarise_evidence(dim, relevant),
            ))

        return scores

    def _score_from_provisions(
        self,
        dimension: str,
        provisions: list[ProvisionAssessment],
    ) -> int:
        """Calculate a 1-5 score for a dimension from provision assessments."""
        if dimension == "D8":
            specific = sum(
                1 for p in provisions
                if p.status == ProvisionStatus.PRESENT_SPECIFIC
            )
            vague = sum(
                1 for p in provisions
                if p.status == ProvisionStatus.PRESENT_VAGUE
            )
            total = len(provisions)

            if specific >= total * 0.8:
                return 4
            elif specific >= total * 0.6:
                return 3
            elif specific + vague >= total * 0.5:
                return 2
            else:
                return 1

        elif dimension == "D5":
            breach = next(
                (p for p in provisions
                 if p.provision_id == "breach_notification"),
                None,
            )
            if not breach or breach.status == ProvisionStatus.ABSENT:
                return 1
            if breach.status == ProvisionStatus.PRESENT_VAGUE:
                return 2
            if breach.sla_value:
                return 4
            return 3

        elif dimension == "D2":
            sub = next(
                (p for p in provisions
                 if p.provision_id == "art28_3d_sub_processors"),
                None,
            )
            if not sub or sub.status == ProvisionStatus.ABSENT:
                return 1
            if sub.status == ProvisionStatus.PRESENT_VAGUE:
                return 2
            return 3

        elif dimension == "D7":
            deletion = next(
                (p for p in provisions
                 if p.provision_id == "art28_3g_deletion_return"),
                None,
            )
            if not deletion or deletion.status == ProvisionStatus.ABSENT:
                return 1
            if deletion.status == ProvisionStatus.PRESENT_VAGUE:
                return 2
            if deletion.sla_value:
                return 4
            return 3

        return 1

    def _summarise_evidence(
        self,
        dimension: str,
        provisions: list[ProvisionAssessment],
    ) -> str:
        specific = [
            p for p in provisions
            if p.status == ProvisionStatus.PRESENT_SPECIFIC
        ]
        vague = [
            p for p in provisions
            if p.status == ProvisionStatus.PRESENT_VAGUE
        ]
        absent = [
            p for p in provisions
            if p.status == ProvisionStatus.ABSENT
        ]

        parts = []
        if specific:
            parts.append(f"{len(specific)} provision(s) specific")
        if vague:
            parts.append(f"{len(vague)} provision(s) vague")
        if absent:
            parts.append(f"{len(absent)} provision(s) absent")
        return " · ".join(parts)

    def _detect_conflicts(
        self,
        result: LegalBanditResult,
        policy_signals: dict,
        policy_scores: dict,
    ) -> list[PolicyContractConflict]:
        """Detect cases where policy claims more than DPA commits."""
        conflicts = []
        provision_lookup = {
            p.provision_id: p for p in result.provisions
        }

        # Check D5 — breach notification
        breach = provision_lookup.get("breach_notification")
        if breach:
            policy_d5 = policy_scores.get("D5", 1)
            contract_d5 = next(
                (s.contract_score for s in result.dimension_scores
                 if s.dimension == "D5"),
                1,
            )
            if policy_d5 > contract_d5:
                policy_sla = policy_signals.get("d5_specific_sla_hours")
                if policy_sla and breach.status == ProvisionStatus.ABSENT:
                    conflicts.append(PolicyContractConflict(
                        dimension="D5",
                        signal_key="d5_specific_sla_hours",
                        policy_claim=(
                            f"Policy implies breach notification "
                            f"within {policy_sla} hours"
                        ),
                        contract_reality=(
                            "No breach notification clause in DPA"
                        ),
                        conflict_type="policy_unbacked",
                        severity=ConflictSeverity.HIGH,
                        recommendation=(
                            "Add breach notification clause to DPA "
                            "— see redline recommendation"
                        ),
                    ))

        # Check D6 — AI/ML
        ai_provision = provision_lookup.get("ai_ml_restriction")
        if ai_provision:
            policy_has_ai = policy_signals.get(
                "d6_training_opt_out_available"
            )
            if (policy_has_ai
                    and ai_provision.status == ProvisionStatus.ABSENT):
                conflicts.append(PolicyContractConflict(
                    dimension="D6",
                    signal_key="d6_training_opt_out_available",
                    policy_claim="Policy mentions AI training opt-out",
                    contract_reality=(
                        "No AI/ML restriction clause in DPA"
                    ),
                    conflict_type="policy_unbacked",
                    severity=ConflictSeverity.HIGH,
                    recommendation=(
                        "Add AI/ML restriction clause to DPA "
                        "— see redline recommendation"
                    ),
                ))

        # Check D8 — DPA quality
        policy_d8 = policy_scores.get("D8", 1)
        d8_contract = next(
            (s.contract_score for s in result.dimension_scores
             if s.dimension == "D8"),
            None,
        )
        if d8_contract is not None and policy_d8 > d8_contract + 1:
            conflicts.append(PolicyContractConflict(
                dimension="D8",
                signal_key="d8_art28_completeness",
                policy_claim=(
                    f"Policy implied DPA quality score {policy_d8}/5"
                ),
                contract_reality=(
                    f"Actual DPA scores {d8_contract}/5 "
                    f"against Art. 28 checklist"
                ),
                conflict_type="contradiction",
                severity=ConflictSeverity.MEDIUM,
                recommendation=(
                    "Request revised DPA addressing all "
                    "Art. 28(3)(a)-(h) provisions"
                ),
            ))

        return conflicts
