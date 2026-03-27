# Privacy Risk Scoring Rubric

**Bandit — Privacy Risk Framework v1.0**
Regulatory Coverage: GDPR (EU) 2016/679 · CCPA/CPRA · EU AI Act 2024

---

## Overview

Bandit uses a structured **Bandit Risk Score (BRS)** to provide consistent, repeatable vendor assessments. This rubric defines the scoring criteria for each dimension, the weighting formula, risk thresholds, and recommended escalation paths.

---

## Scoring Scale

All 8 dimensions (D1–D8) are scored on a **1–5 integer scale**:

| Score | Label | Meaning |
|-------|-------|---------|
| 1 | Compliant | Best practice. Meets or exceeds regulatory requirements. |
| 2 | Acceptable | Minor gaps. Meets minimum requirements with low risk. |
| 3 | Marginal | Notable gaps. Meets some requirements; legal review advised. |
| 4 | High Risk | Significant gaps. Multiple regulatory requirements unmet. |
| 5 | Critical | Severe non-compliance. Immediate escalation required. |

---

## Dimension Definitions

### D1 — Data Collection Scope
*Regulatory basis: GDPR Art. 5(1)(b)(c) (purpose & data minimisation), CCPA §1798.100*

Evaluates whether data collection is proportionate and limited to stated purposes. High-risk signals include collection of sensitive categories (GDPR Art. 9), inferred/derived data, and behavioral profiling without explicit disclosure.

**Key questions:**
- Are all collected data categories explicitly named?
- Is sensitive data (health, biometric, financial) called out separately?
- Is there a stated legal basis for each collection purpose?

---

### D2 — Data Retention & Deletion
*Regulatory basis: GDPR Art. 5(1)(e) (storage limitation), Art. 17 (right to erasure)*

Evaluates whether the vendor commits to specific, enforceable retention limits and provides a credible deletion mechanism.

**Key questions:**
- Are retention periods specified per data category?
- What triggers deletion — time, user request, contract end?
- Are backups subject to the same retention policy?

---

### D3 — Third-Party Data Sharing
*Regulatory basis: GDPR Art. 28 (processors), Art. 44–49 (transfers), CCPA §1798.115 (disclosure of sharing)*

Evaluates the scope and control of data shared with third parties, including sub-processors, analytics providers, and data brokers.

**Key questions:**
- Are third parties named, or only described as "partners"?
- Is data sold or shared for advertising?
- Is there a sub-processor list with update notifications?

---

### D4 — International Data Transfers *(1.5× weight)*
*Regulatory basis: GDPR Chapter V (Art. 44–49), Schrems II (C-311/18), EU-US Data Privacy Framework*

Evaluates adequacy of safeguards for personal data transferred outside the EEA. Weighted 1.5× due to elevated legal risk post-Schrems II.

**Key questions:**
- What transfer mechanism is used (SCCs, BCRs, adequacy decision)?
- Are destination countries disclosed?
- Has a Transfer Impact Assessment (TIA) been conducted?

**Note:** References to the invalidated EU-US Privacy Shield should be scored 5.

---

### D5 — User Rights & Enforcement
*Regulatory basis: GDPR Art. 15–21, CCPA §1798.100–145*

Evaluates whether data subject rights are operationalized — i.e., whether a user can actually exercise them, not just whether they are mentioned.

**Key questions:**
- Are all GDPR rights (access, rectification, erasure, portability, objection, restriction) explicitly listed?
- Is there a working contact method for requests?
- What is the committed response timeline?
- Is there a DPA complaint pathway?

---

### D6 — Security & Breach Notification
*Regulatory basis: GDPR Art. 32 (security), Art. 33–34 (breach notification), CCPA §1798.150*

Evaluates technical/organisational security measures and the vendor's ability to detect, respond to, and notify of breaches within GDPR's 72-hour window.

**Key questions:**
- Are specific technical measures named (encryption, access control, pseudonymisation)?
- Does the vendor hold ISO 27001, SOC 2 Type II, or equivalent certification?
- Is the 72-hour breach notification timeline committed to?

---

### D7 — AI & Automated Decision-Making *(1.5× weight)*
*Regulatory basis: GDPR Art. 22 (automated decision-making), EU AI Act 2024 (high-risk AI systems), CCPA automated decision rules*

Evaluates transparency and control over AI/ML processing. Weighted 1.5× due to the EU AI Act's new obligations for AI system providers. Applies to all vendors using AI, not only AI-native products.

**Key questions:**
- Does the policy disclose use of AI or ML?
- Are automated decisions with legal/significant effect disclosed, with human review available?
- Is user data used to train models? Is consent obtained?
- For EU AI Act compliance: is the system categorized by risk level?

---

### D8 — Governance & Accountability
*Regulatory basis: GDPR Art. 5(2) (accountability), Art. 25 (Privacy by Design), Art. 37–39 (DPO)*

Evaluates organizational privacy maturity and the existence of structures required by GDPR accountability principle.

**Key questions:**
- Is a DPO named with contact details?
- Are legal bases stated per processing purpose?
- Is Privacy by Design referenced?
- Is a Record of Processing Activities (ROPA) maintained?

---

## Weighting Formula

```
PRS = (D1 + D2 + D3 + D5 + D6 + D8 + (D4 × 1.5) + (D7 × 1.5)) / 9
```

Maximum PRS = 5.0 (all dimensions scored 5).
Minimum PRS = 1.0 (all dimensions scored 1).

---

## Risk Thresholds & Escalation Matrix

| PRS Range | Risk Level | Colour | Required Actions |
|-----------|------------|--------|-----------------|
| 1.0 – 2.0 | **Low** | Green | Standard procurement approval. Log in vendor register. |
| 2.1 – 3.0 | **Medium-Low** | Yellow | Privacy team review. Request vendor clarifications. |
| 3.1 – 3.5 | **Medium-High** | Amber | Legal review required. DPA negotiation recommended. |
| 3.6 – 4.5 | **High** | Red | DPO review required. DPA amendments mandatory before contract. |
| 4.6 – 5.0 | **Critical** | Black | Do not proceed. DPO sign-off required. Consider alternative vendor. |

---

## Automatic Escalation Triggers

Regardless of overall PRS, the following individual dimension scores trigger mandatory escalation:

| Trigger | Condition | Required Action |
|---------|-----------|----------------|
| International Transfer Critical | D4 = 5 | DPO review + legal opinion on transfer mechanism |
| AI High-Risk System | D7 ≥ 4 | EU AI Act compliance check + legal review |
| No Breach Notification | D6 = 5 | Security team assessment + contractual requirement |
| No Legal Basis | D8 = 5 | Processing may be unlawful — halt procurement |
| Rights Denied | D5 = 5 | GDPR compliance may be impossible — escalate to DPO |

---

## Regulatory Reference Map

| Regulation | Key Articles Assessed | Dimensions |
|------------|----------------------|------------|
| GDPR Art. 5 | Data minimisation, storage limitation, accountability | D1, D2, D8 |
| GDPR Art. 13–14 | Transparency obligations | D1, D3, D7 |
| GDPR Art. 15–21 | Data subject rights | D5 |
| GDPR Art. 22 | Automated decision-making | D7 |
| GDPR Art. 25 | Privacy by Design | D8 |
| GDPR Art. 28 | Processor obligations | D3 |
| GDPR Art. 32–34 | Security & breach notification | D6 |
| GDPR Chapter V | International transfers | D4 |
| CCPA §1798.100–145 | Consumer rights | D5 |
| CCPA §1798.115 | Disclosure of data sharing | D3 |
| CCPA §1798.150 | Security breach liability | D6 |
| EU AI Act 2024 | High-risk AI, transparency, human oversight | D7 |

---

## Versioning

This rubric follows semantic versioning. Breaking changes to scoring criteria increment the major version. Submit proposed changes via pull request — see CONTRIBUTING.md.
