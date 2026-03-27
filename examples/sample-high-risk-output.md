# Sample Output — High Risk Assessment

**Bandit v1.0 | Prompt: PB-1 v1.0**
*This is a fictional example for demonstration purposes.*

---

## Assessment Metadata

```json
{
  "assessment_metadata": {
    "vendor_name": "DataHarvest Analytics Inc.",
    "policy_url": "https://example-dataharvest.com/privacy",
    "assessment_date": "2025-09-15",
    "prompt_version": "PB-1 v1.0",
    "model_used": "claude-opus-4-6"
  }
}
```

---

## Dimension Scores

| Dim | Label | Score | Risk |
|-----|-------|-------|------|
| D1 | Data Collection Scope | 4 | High |
| D2 | Data Retention & Deletion | 4 | High |
| D3 | Third-Party Data Sharing | 5 | Critical |
| D4 | International Data Transfers | 4 | High |
| D5 | User Rights & Enforcement | 3 | Medium |
| D6 | Security & Breach Notification | 3 | Medium |
| D7 | AI & Automated Decision-Making | 5 | Critical |
| D8 | Governance & Accountability | 4 | High |

---

## Detailed Findings

### D1 — Data Collection Scope | Score: 4

**Rationale:** The policy claims to collect "all information you provide and all information we infer from your usage," with no enumeration of specific data categories. Sensitive data categories (health, financial, location) are referenced as examples but explicitly not limited to those categories. No legal basis is provided for any collection purpose.

**Evidence Quotes:**
- *"We collect information you provide to us, information we automatically collect, and information we obtain from third parties and other sources, including but not limited to data brokers and advertising partners."*
- *"We may collect sensitive information such as health data, financial information, and location data, as well as other information we determine is relevant to providing our services."*

**Regulatory Gaps:**
- GDPR Art. 5(1)(b) — purpose limitation violated (no specific purposes stated)
- GDPR Art. 5(1)(c) — data minimisation violated (unlimited collection scope)
- GDPR Art. 9 — no explicit consent mechanism for sensitive data processing
- CCPA §1798.100 — categories of personal information not disclosed

---

### D2 — Data Retention & Deletion | Score: 4

**Rationale:** The policy states data is retained "as long as reasonably necessary for business purposes," which provides no enforceable limit. A deletion request process exists but includes a 180-day processing window and broad exceptions for "business records" that could apply to any data.

**Evidence Quotes:**
- *"We retain your personal information for as long as reasonably necessary to fulfill the purposes for which it was collected, including for the purposes of satisfying any legal, accounting, or reporting requirements."*
- *"Deletion requests will be processed within 180 days. We may retain information as necessary for our legitimate business records."*

**Regulatory Gaps:**
- GDPR Art. 5(1)(e) — storage limitation principle not upheld
- GDPR Art. 17 — erasure right undermined by broad business records exception
- CCPA §1798.105 — deletion right: 180-day window far exceeds 45-day requirement

---

### D3 — Third-Party Data Sharing | Score: 5

**Rationale:** The policy permits sharing with an undefined universe of "partners and affiliates" for advertising purposes without an opt-out mechanism. Data is explicitly sold to third parties. No sub-processor list is maintained or available. This represents the most significant risk in this assessment.

**Evidence Quotes:**
- *"We may share, sell, or otherwise disclose your personal information to our partners, affiliates, advertising networks, and other third parties for marketing and advertising purposes."*
- *"We do not maintain a comprehensive list of all third parties with whom we share data, as these relationships change frequently."*
- *"By using our services, you consent to the sale and sharing of your personal information as described in this policy."*

**Regulatory Gaps:**
- GDPR Art. 6 — no valid legal basis for sale of personal data
- GDPR Art. 28(1) — no processor agreements with unnamed third parties
- GDPR Art. 44 — data transferred to third parties without transfer mechanism
- CCPA §1798.120 — no opt-out from sale mechanism provided
- CCPA §1798.115 — categories of third parties not disclosed

---

### D4 — International Data Transfers | Score: 4

**Rationale:** The policy acknowledges international data transfers but references only the EU-US Privacy Shield as a transfer mechanism, which was invalidated by the CJEU in Schrems II (2020). No SCCs, BCRs, or reference to the EU-US Data Privacy Framework are mentioned.

**Evidence Quotes:**
- *"We transfer data internationally in reliance on the EU-US Privacy Shield framework."*
- *"Your data may be processed in the United States and other countries where our servers are located."*

**Regulatory Gaps:**
- GDPR Chapter V (Art. 44–49) — no valid transfer mechanism in place
- Schrems II (C-311/18) — Privacy Shield reliance is unlawful
- GDPR Art. 46 — SCCs or BCRs not mentioned

---

### D5 — User Rights & Enforcement | Score: 3

**Rationale:** Core rights (access, deletion) are mentioned but portability, rectification, and restriction are absent. The policy provides a contact email but no response timeline for rights requests. A DPA complaint pathway is not mentioned.

**Evidence Quotes:**
- *"You may request access to or deletion of your personal information by emailing privacy@example-dataharvest.com."*
- *"We will respond to your request within a reasonable timeframe."*

**Regulatory Gaps:**
- GDPR Art. 18 — right to restriction not mentioned
- GDPR Art. 20 — right to data portability not mentioned
- GDPR Art. 77 — DPA complaint right not communicated

---

### D6 — Security & Breach Notification | Score: 3

**Rationale:** General security language is used ("industry standard measures") without specifics. Breach notification is mentioned but with a vague timeline. No certifications are referenced.

**Evidence Quotes:**
- *"We implement industry standard security measures to protect your personal information."*
- *"In the event of a data breach, we will notify affected users in accordance with applicable law."*

**Regulatory Gaps:**
- GDPR Art. 32 — specific technical measures not enumerated
- GDPR Art. 33 — 72-hour DPA notification not committed to

---

### D7 — AI & Automated Decision-Making | Score: 5

**Rationale:** The policy confirms use of AI-driven profiling and automated scoring but explicitly waives the right to human review. User data is used to train models by default. No EU AI Act compliance information is provided despite the product being used for employment screening (likely a high-risk AI system under Annex III).

**Evidence Quotes:**
- *"We use automated systems, including machine learning models, to analyze your behavior and generate scores that may be used by our clients for employment, credit, and insurance decisions."*
- *"By using our services, you waive your right to human review of automated decisions."*
- *"Your data may be used to train and improve our AI models."*

**Regulatory Gaps:**
- GDPR Art. 22(1) — automated decisions with legal effect without human review
- GDPR Art. 22(3) — right to obtain human intervention waived (unlawful)
- EU AI Act 2024 Annex III — employment screening is high-risk AI; conformity assessment required
- EU AI Act Art. 13 — transparency obligations for high-risk AI not met
- CCPA automated decision-making regulations — opt-out not provided

---

### D8 — Governance & Accountability | Score: 4

**Rationale:** No DPO is named. Legal bases for processing are not stated for any activity. The policy references "compliance with applicable law" as a catch-all without mapping to specific provisions.

**Evidence Quotes:**
- *"We process your data as necessary for our business operations and in compliance with applicable law."*
- *"For privacy questions, contact our team at privacy@example-dataharvest.com."*

**Regulatory Gaps:**
- GDPR Art. 37 — DPO not appointed (likely required given scale of processing)
- GDPR Art. 13(1)(c) — legal basis not stated for any processing purpose
- GDPR Art. 5(2) — accountability principle not demonstrated

---

## Overall Assessment

```json
{
  "overall_assessment": {
    "privacy_risk_score": 4.11,
    "risk_level": "High",
    "weighted_calculation_note": "D7 and D4 weighted 1.5x. Formula: (4+4+5+3+3+4+(4×1.5)+(5×1.5)) / 9 = 4.11",
    "summary": "DataHarvest Analytics presents a high overall privacy risk (PRS 4.11/5.0). The most critical findings are the explicit sale of personal data to unnamed third parties without opt-out (D3=5), the deployment of automated employment-screening AI that waives the right to human review in violation of GDPR Art. 22 (D7=5), and the use of an invalidated transfer mechanism for international data flows (D4=4). Proceeding without significant contractual remediation and DPO review is not recommended.",
    "top_3_risks": [
      {
        "dimension": "D3",
        "finding": "Explicit sale of personal data to unnamed third parties; no sub-processor list; no CCPA opt-out from sale"
      },
      {
        "dimension": "D7",
        "finding": "Automated employment decisions with legal effect; human review contractually waived; high-risk AI system with no EU AI Act conformity assessment"
      },
      {
        "dimension": "D4",
        "finding": "Sole reliance on invalidated EU-US Privacy Shield for international transfers; no SCCs or DPF in place"
      }
    ],
    "recommended_actions": [
      "Do not execute contract until DPO review is completed",
      "Require vendor to provide an updated, valid transfer mechanism (SCCs or EU-US DPF) as a condition of contract",
      "Negotiate DPA with explicit prohibition on data sale, named sub-processor list, and GDPR Art. 22 human review restoration",
      "Request EU AI Act conformity assessment documentation for the employment screening product",
      "Set maximum 90-day contract term with compliance review milestone before renewal"
    ],
    "dpa_required": true,
    "dpo_escalation_required": true,
    "legal_review_required": true
  }
}
```
