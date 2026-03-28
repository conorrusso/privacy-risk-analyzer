# Bandit Scoring Rubric

**Version:** 1.0.0  
**Last updated:** 2026-03-27  
**Maintainer:** Conor Russo  
**License:** Apache-2.0  

---

## How Bandit Scores

Bandit separates **evidence extraction** (AI) from **scoring** (deterministic engine). An LLM reads vendor documents and extracts structured true/false signals. The scoring engine in `rubric.py` matches those signals against the criteria below. The AI never assigns scores — Bandit does.

**Scoring algorithm:** For each dimension, the engine walks levels 5 → 1 and awards the highest level whose required signals are *all* satisfied. Red-flag phrases impose hard ceilings. D8 (DPA Completeness) can further cap D2, D5, and D7 via the dependency ceiling rule.

### Risk Tiers

| Tier   | Weighted Average | Meaning                                    |
|--------|------------------|--------------------------------------------|
| HIGH   | < 2.5            | Material gaps; recommend hold on onboarding |
| MEDIUM | 2.5 – 3.5        | Deficiencies to remediate before go-live     |
| LOW    | > 3.5            | Acceptable posture; standard monitoring      |

### Dimension Weights

| Dimension | Weight | Rationale                                                |
|-----------|--------|----------------------------------------------------------|
| D1–D5, D7 | 1.0    | Standard regulatory dimensions                           |
| D6        | 1.5    | Elevated — fastest-moving regulatory landscape (AI Act, FTC disgorgement, ADMT regs) |
| D8        | 1.5    | Elevated — DPA quality sets the enforceability ceiling for D2, D5, D7 |

---

## D1 — Data Minimization

**Weight:** 1.0

### Regulatory Basis

- GDPR Art. 5(1)(c) — "adequate, relevant and limited to what is necessary"
- CCPA/CPRA — CPPA Enforcement Advisory (Apr 2024): data minimization as "foundational principle"
- CJEU *Schrems v Meta* C-446/21 (Oct 2024): unlimited retention for advertising = disproportionate interference

### Framework References

- ISO 27701 Annex A — Privacy by design (minimization)
- SOC 2 Privacy TSC P3.1 — Collection Limitation
- NIST Privacy Framework CT.DP-P4

### Scoring Levels

| Score | Label             | Required Signals                                                                                                    |
|-------|-------------------|---------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d1_categories_linked_to_purposes`, `d1_specific_retention_per_category`, `d1_automated_minimization_controls`, `d1_privacy_by_design_documented`, `d1_periodic_review_cycle` |
| 4     | Strong            | `d1_categories_linked_to_purposes`, `d1_specific_retention_per_category`, `d1_periodic_review_cycle`                |
| 3     | Minimum compliant | `d1_purposes_stated`, `d1_categories_listed`                                                                        |
| 2     | Deficient         | `d1_purposes_stated`                                                                                                |
| 1     | Absent            | *(no signals required — fallback)*                                                                                  |

**Score 5** — Automated enforcement of minimization policies. Data inventory links categories to purposes with periodic review. Privacy-by-design documentation per ISO 27701:2025 Clause 8.

**Score 4** — Documented data inventory linking categories to purposes with periodic review and category-specific retention.

**Score 3** — Collection purposes stated and data categories listed, but no documented linkage or review cycle.

**Score 2** — Purposes mentioned but vague. Language like "we may collect data as needed" or open-ended purposes without category specificity.

**Score 1** — No data minimization disclosure. No stated purposes or categories. Language contradicts minimization.

### Red-Flag Phrases

| Pattern | Ceiling | Precedent |
|---------|---------|-----------|
| "we may collect data as needed" | 2 | Vague open-ended collection |
| "improving our products and services" | 2 | CRITEO / Netflix |
| "data may be retained for legitimate business purposes" | 2 | Amazon France €32M |

### Enforcement Precedents

- **CNIL v Amazon France Logistique — €32M (Dec 2023):** Excessive employee monitoring, data retained longer than necessary, violating minimization and transparency.
- **German DPA v notebooksbilliger.de — €10.4M:** CCTV in break rooms, footage kept over 60 days.

---

## D2 — Sub-processor Management

**Weight:** 1.0

### Regulatory Basis

- GDPR Art. 28(2) and (4) — prior authorization, right to object, full liability
- CCPA/CPRA — notification + same contractual flow-down
- EDPB Guidelines 7/2020 — locations, roles, proof of safeguards, approval timeframe

### Framework References

- ISO 27701 Annex B — Sub-processor authorization
- SOC 2 CC9.2 — Vendor Risk Management
- NIST PF ID.IM-P7
- CSA CCM STA domain

### Scoring Levels

| Score | Label             | Required Signals                                                                                                                                                    |
|-------|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d2_published_list_with_locations`, `d2_change_notification_period`, `d2_objection_right_with_termination`, `d2_audit_rights_extend_to_subs`, `d2_proof_of_compliance_on_request`, `d2_full_liability_retained`, `d2_contractual_flowdown` |
| 4     | Strong            | `d2_published_list_with_locations`, `d2_change_notification_period`, `d2_objection_right_with_termination`, `d2_contractual_flowdown`                               |
| 3     | Minimum compliant | `d2_sub_list_exists`, `d2_general_authorization_with_notification`, `d2_contractual_flowdown`                                                                       |
| 2     | Deficient         | `d2_sub_list_exists`                                                                                                                                                |
| 1     | Absent            | *(no signals required — fallback)*                                                                                                                                  |

**Score 5** — Published sub-processor list with locations and roles, ≥30-day advance notification, objection + termination right, audit rights extending to subs, proof-of-compliance on request (CRITEO standard), full processor liability per Art. 28(4).

**Score 4** — Published list with locations, defined notification period, objection right with contractual consequences (termination), flow-down to sub-processors.

**Score 3** — Sub-processor list exists (possibly URL-based), general authorization with notification of changes, standard contractual flow-down.

**Score 2** — List exists but no notification mechanism, no objection right, no flow-down clause.

**Score 1** — No sub-processor list. No notification mechanism. DPA silent on sub-processing.

### Red-Flag Phrases

| Pattern | Ceiling | Precedent |
|---------|---------|-----------|
| "reasonable efforts to notify" | 2 | Below Art. 28(2) standard |
| "we share data with third parties" (no specifics) | 2 | Netflix €4.75M / WhatsApp €225M |

### Enforcement Precedents

- **CNIL v Criteo — €40M (Jun 2023):** Contractual obligation to obtain consent was insufficient. CNIL required proof-of-compliance on request and actual audits of partner consent practices.

---

## D3 — Data Subject Rights

**Weight:** 1.0

### Regulatory Basis

- GDPR Chapter III (Arts. 12–23) — access, rectification, erasure, restriction, portability, objection, automated decision-making
- GDPR Art. 28(3)(e) — processor DSAR assistance
- CCPA/CPRA — access, deletion, correction, opt-out of sale, limit use of sensitive PI

### Framework References

- ISO 27701 Annex A — Obligations to PII principals
- SOC 2 Privacy TSC P5 (Access), P5.2 (Correction)
- NIST PF CT.DM-P1 through P4

### Scoring Levels

| Score | Label             | Required Signals                                                                                                                                        |
|-------|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d3_all_gdpr_rights_listed`, `d3_ccpa_rights_listed`, `d3_contact_details_provided`, `d3_response_timeline_stated`, `d3_measurable_sla`, `d3_automated_dsar_workflow`, `d3_identity_verification_process` |
| 4     | Strong            | `d3_all_gdpr_rights_listed`, `d3_contact_details_provided`, `d3_response_timeline_stated`, `d3_dsar_procedure_documented`                              |
| 3     | Minimum compliant | `d3_some_rights_listed`, `d3_contact_details_provided`                                                                                                  |
| 2     | Deficient         | `d3_some_rights_listed`                                                                                                                                 |
| 1     | Absent            | *(no signals required — fallback)*                                                                                                                      |

**Score 5** — All 7 GDPR rights + CCPA rights explicitly listed. Measurable SLA targets (ISO 27701 style, e.g. "95% of DSARs within 20 days"). Automated DSAR workflow. Identity verification process documented.

**Score 4** — All GDPR Chapter III rights listed with contact details, defined response timeline, documented DSAR procedure.

**Score 3** — Some rights listed (access, deletion) with contact information, but incomplete coverage and no defined timeline.

**Score 2** — Rights mentioned generically without contact details or response timelines.

**Score 1** — No mention of data subject rights. No contact information.

### Enforcement Precedents

- **DPC v Meta — €390M (Jan 2023):** Failed to transparently disclose processing activities, purposes, and legal basis in Terms of Use.
- **DPC v TikTok — €345M (Sep 2023):** Children's data defaults, inadequate age verification, violations of fairness and privacy by design.

---

## D4 — Cross-Border Transfer Mechanisms

**Weight:** 1.0

### Regulatory Basis

- GDPR Chapter V (Arts. 44–50) — adequacy, SCCs, BCRs
- CJEU *Schrems II* (C-311/18) — supplementary measures required
- EU-US Data Privacy Framework (Jul 2023) — adequacy for DPF-certified orgs
- EDPB Recommendations 01/2020 on supplementary measures
- 2021 SCCs (Modules 2 & 3) — incorporate Art. 28 requirements

### Framework References

- ISO 27701 Annex A — PII sharing/transfer
- ISO 27018 — cloud data location disclosure
- SOC 2 CC9.2 + Privacy P6
- CSA CAIQ DSI-02, DSI-05

### Scoring Levels

| Score | Label             | Required Signals                                                                                                                                                          |
|-------|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d4_transfer_mechanism_identified`, `d4_sccs_module_specified`, `d4_tia_documented`, `d4_supplementary_measures`, `d4_sub_processor_locations_specified`, `d4_monitoring_adequacy_changes`, `d4_notification_of_mechanism_changes` |
| 4     | Strong            | `d4_transfer_mechanism_identified`, `d4_sccs_module_specified`, `d4_tia_documented`, `d4_sub_processor_locations_specified`                                               |
| 3     | Minimum compliant | `d4_transfer_mechanism_identified`                                                                                                                                        |
| 2     | Deficient         | `d4_transfers_acknowledged`                                                                                                                                               |
| 1     | Absent            | *(no signals required — fallback)*                                                                                                                                        |

**Score 5** — Transfer mechanisms specified with SCC module, documented TIA, supplementary measures, sub-processor location specificity, monitoring of adequacy decision changes, notification of mechanism changes.

**Score 4** — Transfer mechanism identified with SCC module, TIA documented per Schrems II, sub-processor locations disclosed (ISO 27018-aligned).

**Score 3** — Transfer mechanism identified (SCCs, DPF, or adequacy) without module specification, TIA, or sub-processor location detail.

**Score 2** — Transfers acknowledged but mechanism is vague ("data stays in region") or outdated (Privacy Shield).

**Score 1** — No mention of cross-border transfers. No transfer mechanism identified.

### Red-Flag Phrases

| Pattern | Ceiling | Precedent |
|---------|---------|-----------|
| "privacy shield" | 2 | Invalidated July 2020 by CJEU |

### Enforcement Precedents

- **DPC v Meta — €1.2B (May 2023):** Art. 46(1) infringement — SCCs + supplementary measures found insufficient for US transfers post-Schrems II.

---

## D5 — Breach Notification

**Weight:** 1.0

### Regulatory Basis

- GDPR Art. 33 — SA notification: 72 hours from awareness
- GDPR Art. 33(2) — Processor → controller: "without undue delay"
- GDPR Art. 33(3) — Required notification content (nature, numbers, consequences, measures)
- GDPR Art. 33(4) — Phased reporting permitted
- GDPR Art. 34 — Individual notification: high-risk threshold
- CA Civil Code §1798.82 — "most expedient time possible"

### Framework References

- ISO 27701 Clause 6.13 — Incident Management (named response lead)
- SOC 2 CC7.3, CC7.4, P6.1
- NIST PF Protect-P (PR.PO-P)

### Scoring Levels

| Score | Label             | Required Signals                                                                                                                                                 |
|-------|-------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d5_specific_sla_hours`, `d5_art33_3_content_commitment`, `d5_covers_suspected_incidents`, `d5_evidence_preservation`, `d5_phased_reporting`, `d5_awareness_trigger_defined`, `d5_sub_processor_breach_cascade` |
| 4     | Strong            | `d5_specific_sla_hours`, `d5_art33_3_content_commitment`, `d5_named_response_lead`                                                                              |
| 3     | Minimum compliant | `d5_notification_obligation_stated`                                                                                                                              |
| 2     | Deficient         | `d5_breach_mentioned`                                                                                                                                            |
| 1     | Absent            | *(no signals required — fallback)*                                                                                                                               |

**Score 5** — Specific SLA (≤24 hrs), commits to all Art. 33(3) content, covers confirmed + suspected incidents, evidence preservation, phased reporting per Art. 33(4), "awareness" trigger defined, sub-processor breach cascade addressed.

**Score 4** — Specific SLA (24–48 hrs), commits to providing Art. 33(3) content elements, named response lead (ISO 27701).

**Score 3** — "Without undue delay" mirrors GDPR Art. 33(2) verbatim. No specific SLA. No Art. 33(3) content commitment.

**Score 2** — Breach mentioned with vague language: "as required by law", "within a reasonable period", "promptly".

**Score 1** — No breach notification clause. No commitment to assist with controller's Art. 33 obligations.

### Red-Flag Phrases

| Pattern | Ceiling | Precedent |
|---------|---------|-----------|
| "notify as required by law / in accordance with applicable law" | 2 | No specific commitment |
| "within a reasonable period" | 2 | Undefined timeline |
| "without undue delay" (with no SLA hours following) | 3 | GDPR verbatim only |

### The Critical Arithmetic

GDPR's 72-hour clock runs from when the **controller** becomes aware. If the vendor DPA only says "without undue delay" and the vendor takes 48 hours, the controller has only 24 hours left. Best-practice DPAs specify ≤24 hours precisely because of this arithmetic.

### Enforcement Precedents

- **DPC v Meta — €251M (Dec 2024):** 2018 breach affecting 29M users. Incomplete Art. 33 notifications, failed to fully document the breach.

---

## D6 — AI/ML Data Usage

**Weight:** 1.5 *(elevated)*

### Regulatory Basis

- EU AI Act (Regulation 2024/1689) Arts. 10, 50, 53
- GDPR Arts. 5(1)(a), 6, 12, 13, 22
- FTC Act Section 5 — algorithmic disgorgement precedent (7+ orders since 2019)
- CCPA/CPRA ADMT Regulations (finalized Jul 2025)
- Colorado AI Act SB 24-205 (effective Jun 2026)
- Illinois HB 3773 (effective Jan 2026)

### Framework References

- ISO 27701:2025 — AI-related privacy controls (explainability, human oversight)
- NIST AI RMF 1.0 — Govern, Map, Measure, Manage
- NIST PF 1.1 — AI privacy risk subcategories (inference, membership inference, bias)

### Scoring Levels

| Score | Label             | Required Signals                                                                                                                                                                                                          |
|-------|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d6_ai_disclosed_as_separate_purpose`, `d6_legal_basis_identified`, `d6_data_categories_specified`, `d6_opt_in_for_training`, `d6_customer_data_segregation`, `d6_data_provenance_documentation`, `d6_training_data_retention_schedule`, `d6_algorithmic_disgorgement_readiness`, `d6_ai_act_art53_compliance`, `d6_bias_mitigation_documented`, `d6_update_cadence_stated` |
| 4     | Strong            | `d6_ai_disclosed_as_separate_purpose`, `d6_legal_basis_identified`, `d6_data_categories_specified`, `d6_opt_out_prominent`, `d6_customer_data_segregation`, `d6_training_data_retention_schedule`, `d6_dpa_ai_restriction_clause` |
| 3     | Minimum compliant | `d6_ai_disclosed_as_separate_purpose`, `d6_opt_out_exists`                                                                                                                                                                |
| 2     | Deficient         | `d6_ai_mentioned`                                                                                                                                                                                                         |
| 1     | Absent            | *(no signals required — fallback)*                                                                                                                                                                                        |

**Score 5** — Explicit separate disclosure of AI/ML training as distinct purpose with legal basis. Affirmative opt-in. Customer data segregation. Data provenance documentation. Algorithmic disgorgement readiness. AI Act Art. 53 compliance. Bias mitigation documented. Update cadence ≥ every 6 months.

**Score 4** — AI training clearly disclosed as distinct purpose with legal basis. Data categories specified. Prominent, accessible opt-out. Customer data segregation. DPA contains explicit AI restriction clause.

**Score 3** — AI/ML training disclosed as distinct purpose. Opt-out available. But no specifics on categories, models, provenance, or derived model treatment.

**Score 2** — AI/ML mentioned but bundled with other purposes, not separately identified (violates CRITEO finding). Opt-out buried or burdensome.

**Score 1** — No mention of AI/ML data usage. Or: vague "improve products and services" without AI disclosure. Or: retroactive policy change for AI training without consent.

### Red-Flag Phrases

| Pattern | Ceiling | Precedent |
|---------|---------|-----------|
| "we may use data to improve our products/services/models" | 2 | CRITEO €40M / OpenAI €15M |
| "by using our service, you consent to AI/training/model" | 2 | GDPR Art. 7 / FTC guidance |
| "industry-standard AI practices" | 2 | No specificity |
| "we reserve the right to update … AI / new uses" | **1** | FTC Feb 2024 / Everalbum |
| "data in anonymized form … machine learning" | 3 | Re-identification risk; no methodology |

### Gold-Standard DPA Language (Reference)

> *"Processor shall not use, access, or process Customer Data or any derivative thereof for the purpose of training, improving, fine-tuning, or developing any artificial intelligence or machine learning model, algorithm, or system, whether for Processor's own use or for the benefit of any third party, unless Controller provides explicit prior written authorization specifying the scope, data categories, duration, and purpose of such use. Processor shall maintain auditable records of all data used in AI/ML model training, including data provenance documentation. Upon termination of authorization or upon Controller's request, Processor shall delete all Customer Data from training datasets and, where technically feasible, retrain or modify affected models to remove the influence of Controller's data."*

### Key Regulatory Dates

| Date | Event | Impact |
|------|-------|--------|
| Dec 2024 | Garante v OpenAI — €15M | First major GDPR fine for AI training data |
| Jul 2025 | CA CPPA adopts ADMT regs | Opt-out rights for AI training |
| Aug 2025 | EU AI Act GPAI obligations apply (new models) | Art. 53 training data summaries mandatory |
| Jan 2026 | Illinois AI employment disclosure | Employer AI notice requirements |
| Jun 2026 | Colorado AI Act effective | Developer documentation + consumer disclosure |
| Aug 2027 | Pre-existing GPAI models must comply with Art. 53 | Full training data transparency deadline |

### Enforcement Precedents

- **Garante v OpenAI — €15M (Dec 2024):** No lawful basis for training. Privacy notice too broad. Failed to report breach. No age verification.
- **CNIL v Criteo — €40M (Jun 2023):** ML training for ad-tech = separate processing purpose requiring independent disclosure.
- **FTC v Everalbum (2021):** Algorithmic disgorgement — ordered to delete models trained on illegally collected face data.
- **FTC v Weight Watchers (2022):** Delete children's data *and* all models/algorithms derived from it.
- **FTC v Rite Aid (2024):** Deployer held liable for AI system accuracy and bias.

---

## D7 — Retention & Deletion

**Weight:** 1.0

### Regulatory Basis

- GDPR Art. 5(1)(e) — storage limitation: "no longer than necessary"
- GDPR Art. 17 — right to erasure
- GDPR Art. 28(3)(g) — deletion/return at contract termination
- CCPA/CPRA — right to know specific retention periods

### Framework References

- ISO 27701 Annex A — Storage limitation controls (documented schedules, automated deletion)
- SOC 2 Privacy TSC P4 — Use, Retention, Disposal
- NIST PF CT.DM-P5

### Scoring Levels

| Score | Label             | Required Signals                                                                                                                                                     |
|-------|-------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d7_category_specific_retention`, `d7_deletion_timeframe_specified`, `d7_deletion_certification`, `d7_backup_copies_addressed`, `d7_derived_data_addressed`, `d7_ai_training_data_retention_separate`, `d7_sub_processor_deletion_obligations`, `d7_periodic_review_cycle` |
| 4     | Strong            | `d7_category_specific_retention`, `d7_deletion_timeframe_specified`, `d7_deletion_certification`, `d7_backup_copies_addressed`                                      |
| 3     | Minimum compliant | `d7_general_retention_stated`, `d7_deletion_at_termination`                                                                                                          |
| 2     | Deficient         | `d7_retention_mentioned`                                                                                                                                             |
| 1     | Absent            | *(no signals required — fallback)*                                                                                                                                   |

**Score 5** — Category-specific retention schedules linked to purposes. Deletion within defined timeframe with certification. Backup copies, derived/aggregated data, AI training data, and sub-processor deletion all addressed. Periodic review cycle.

**Score 4** — Category-specific retention schedules. Defined deletion timeframe (e.g. 30 days). Certification of deletion on request. Backup copies explicitly addressed.

**Score 3** — General retention period stated (e.g. "up to X years"). Deletion at contract end per Art. 28(3)(g). No category-specific schedules or confirmation mechanism.

**Score 2** — Retention mentioned but vague: "as required by law", "commercially reasonable efforts to delete". No specific periods.

**Score 1** — No retention schedule. No deletion mechanism. "Retained indefinitely" or silence.

### Red-Flag Phrases

| Pattern | Ceiling | Precedent |
|---------|---------|-----------|
| "retained as required/permitted by applicable law" | 2 | Netflix €4.75M |
| "retained indefinitely" | 1 | Indefinite retention |
| "commercially reasonable efforts to delete" | 2 | Non-committal language |
| "data may be retained for legitimate business purposes" | 2 | Amazon France €32M |

### Enforcement Precedents

- **Dutch DPA v Netflix — €4.75M (Dec 2024):** Vaguely stated "as required or permitted by applicable laws and regulations." Failed to link data categories to retention periods and purposes.
- **CNIL v Amazon France — €32M (Dec 2023):** Data retained longer than necessary, used for evaluations and scheduling beyond stated purposes.

---

## D8 — DPA Completeness

**Weight:** 1.5 *(elevated)*

### Regulatory Basis

- GDPR Art. 28(3)(a)–(h) — eight mandatory provisions
- EDPB Guidelines 7/2020 — "merely restating Art. 28 is never sufficient"
- EC 2021 SCCs (Modules 2 & 3) — incorporate Art. 28 requirements
- EC Art. 28 SCCs template — high-detail TOM standard
- CCPA/CPRA service provider agreement requirements

### The Art. 28(3) Mandatory Checklist

Every DPA must address all eight provisions. Bandit checks each individually:

| ID | Provision | What It Requires |
|----|-----------|------------------|
| (a) | Documented instructions | Process only on controller's documented instructions; instructions should be in an annex with mechanism for new instructions |
| (b) | Confidentiality | All personnel (employees, contractors, temps) bound by confidentiality under need-to-know access |
| (c) | Security measures | Specific TOMs per Art. 32, not just "appropriate measures"; change approval process; regular review |
| (d) | Sub-processing | Prior authorization + list + notification + right to object + flow-down + liability |
| (e) | DSAR assistance | Defined SLA for DSAR forwarding, technical capability to search/extract/delete |
| (f) | Arts. 32–36 assistance | Breach notification SLA, DPIA cooperation, prior consultation support |
| (g) | Deletion/return | Timeframe, certification, backup treatment, return option |
| (h) | Audit rights | Documentation-based + on-site; frequency; extends to sub-processors |

### Scoring Levels

| Score | Label             | Required Signals                                                                                                                                                                                                      |
|-------|-------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| 5     | Gold standard     | `d8_all_art28_provisions`, `d8_tailored_not_template`, `d8_processing_annex_detailed`, `d8_toms_in_annex`, `d8_measurable_slas`, `d8_ai_restriction_clause`, `d8_ccpa_provisions`, `d8_international_transfers_specified`, `d8_independent_verification`, `d8_version_controlled`, `d8_regular_compliance_reports` |
| 4     | Strong            | `d8_all_art28_provisions`, `d8_processing_annex_detailed`, `d8_toms_in_annex`, `d8_measurable_slas`, `d8_ccpa_provisions`, `d8_international_transfers_specified`, `d8_independent_verification`                      |
| 3     | Minimum compliant | `d8_all_art28_provisions`, `d8_processing_annex_exists`                                                                                                                                                               |
| 2     | Deficient         | `d8_most_art28_provisions`                                                                                                                                                                                            |
| 1     | Absent            | *(no signals required — fallback)*                                                                                                                                                                                    |

**Score 5** — All Art. 28(3) provisions, demonstrably tailored to the specific processing relationship. Detailed processing annex. TOMs annex with change approval. Measurable SLAs. AI/ML restriction clause. CCPA provisions. Transfer mechanisms specified. Independent verification (SOC 2 Type II + Privacy TSC or ISO 27701). Version-controlled with change log.

**Score 4** — All Art. 28 provisions with specificity beyond verbatim. Detailed processing annex. TOMs annex. Measurable SLAs. CCPA provisions. Transfer mechanisms. Independent verification.

**Score 3** — All 8 provisions present with some specificity beyond verbatim restatement. Processing description annex exists. Recognizably a template applied without significant tailoring. *This is where most vendor DPAs land.*

**Score 2** — DPA exists and addresses most (5–7) Art. 28 provisions, but only by restating regulation verbatim. Missing specificity. No processing annex or only generic one-paragraph description.

**Score 1** — No DPA exists. Or DPA missing 3+ of the 8 mandatory provisions. Or references outdated framework (pre-GDPR Directive). Or contains provisions conflicting with GDPR (e.g. processor determines purposes).

### Red-Flag Phrases

| Pattern | Ceiling | Precedent |
|---------|---------|-----------|
| "processor shall process … in accordance with instructions" (verbatim only) | 3 | EDPB: restatement never sufficient |
| "appropriate/reasonable/industry-standard measures" | 3 | No enforceable standard |
| "privacy shield" | 2 | Invalidated July 2020 |

### D8 Dependency Ceiling Rule

D8 quality sets an enforceability ceiling on D2, D5, and D7. A privacy policy promising 24-hour breach notification but sitting on a DPA that says "without undue delay" creates an enforceability gap — the DPA is what the controller can rely on in a dispute.

| D8 Score | D2 Ceiling | D5 Ceiling | D7 Ceiling |
|----------|------------|------------|------------|
| 1        | 2          | 2          | 2          |
| 2        | 3          | 3          | 3          |
| 3        | 4          | 4          | 4          |
| ≥ 4      | *(no ceiling)* | *(no ceiling)* | *(no ceiling)* |

### Enforcement Precedents

- **CNIL v Dedalus Biologie — €1.5M (Apr 2022):** Processor held solely liable for missing DPA. Extracted more data than controller instructed.
- **Hessian DPA (Jan 2019):** Shipping company fined specifically for missing DPA.
- **Aggregate enforcement:** €1.13M across 14 enforcement actions for insufficient DPAs (CMS GDPR Enforcement Tracker).

---

## Framework Evidence Modifiers

Framework certifications are additive modifiers to the base score derived from policy/DPA language, capped at 5. A vendor with excellent DPA language but no certifications can still score 4. A vendor with certifications but vague language gets boosted but still flagged for gaps.

| Evidence | Score Impact | Dimensions | Rationale |
|----------|-------------|------------|-----------|
| SOC 2 Type II with Privacy TSC | +1 | All | Independent attestation of operating controls |
| ISO 27701 certified | +1 | All | Certified privacy management system |
| SOC 2 Type II (security only) | +0.5 | D5, D8 | Security controls attested, privacy not evaluated |
| ISO 27001 only | +0.5 | D5 | Security management, no privacy coverage |
| CSA STAR certified | +0.5 | D4 | Cloud security verified, limited privacy scope |
| NIST PF self-assessment | +0 | — | Self-reported, no independent verification |

**Note:** Certification ≠ compliance. ISO 27701 certifies the *management system* exists. SOC 2 Type II attests that *controls operated effectively* over a period. For vendor assessment, evidence of doing is stronger than evidence of intending.

---

## Framework Crosswalk

| Dimension | GDPR Article | ISO 27701 | SOC 2 | NIST PF |
|-----------|-------------|-----------|-------|---------|
| D1 | Art. 5(1)(c) | Annex A — Privacy by design | P3.1 | CT.DP-P4 |
| D2 | Art. 28(2), (4) | Annex B — Sub-processor auth | CC9.2 | ID.IM-P7 |
| D3 | Arts. 12–23 | Annex A — PII principal obligations | P5.1, P5.2 | CT.DM-P1–P4 |
| D4 | Arts. 44–50 | Annex A — PII transfer | CC9.2 + P6 | ID.IM-P7 |
| D5 | Arts. 33–34 | Clause 6.13 | CC7.3, CC7.4, P6.1 | PR.PO-P |
| D6 | Art. 22 + AI Act Art. 53 | 2025 AI controls | CC8.1 + P4.1 | CT.DP-P + AI RMF |
| D7 | Art. 5(1)(e), 17 | Annex A — Storage limitation | P4.2 | CT.DM-P5 |
| D8 | Art. 28(3)(a)–(h) | Annex B + Annex D | CC9.2 + Privacy | GV.PO-P |

---

## Changelog

### v1.0.0 (2026-03-27)

- Initial release
- 8 dimensions with enforcement-grounded scoring criteria
- Red-flag phrase registry with hard ceilings
- D8 dependency ceiling rule (D8 → D2, D5, D7)
- Framework evidence modifiers (SOC 2, ISO 27701, ISO 27001, CSA STAR)
- Extraction prompt generator for provider-agnostic LLM evidence extraction
- CLI interface for `rubric.py`
