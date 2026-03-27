# Sample Output — Low Risk Assessment

**Bandit v1.0 | Prompt: PB-1 v1.0**
*This is a fictional example for demonstration purposes.*

---

## Assessment Metadata

```json
{
  "assessment_metadata": {
    "vendor_name": "ClearData Solutions GmbH",
    "policy_url": "https://example-cleardata.eu/datenschutz",
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
| D1 | Data Collection Scope | 1 | Low |
| D2 | Data Retention & Deletion | 2 | Acceptable |
| D3 | Third-Party Data Sharing | 1 | Low |
| D4 | International Data Transfers | 1 | Low |
| D5 | User Rights & Enforcement | 1 | Low |
| D6 | Security & Breach Notification | 2 | Acceptable |
| D7 | AI & Automated Decision-Making | 1 | Low |
| D8 | Governance & Accountability | 1 | Low |

---

## Detailed Findings

### D1 — Data Collection Scope | Score: 1

**Rationale:** The policy provides an exhaustive, categorised list of data types collected, each linked to a specific processing purpose and legal basis. Sensitive data categories are explicitly named as not collected unless contractually agreed in advance. Data minimisation is explicitly referenced as a guiding principle.

**Evidence Quotes:**
- *"We collect only the following categories of personal data, each linked to a specific processing purpose as set out in Schedule 1 of this policy: [full enumerated list follows]."*
- *"We do not collect special categories of personal data as defined in GDPR Article 9 unless explicitly agreed in a separate Data Processing Schedule."*
- *"Our data collection practices are guided by the principle of data minimisation (GDPR Art. 5(1)(c)). We collect only what is strictly necessary."*

**Regulatory Gaps:** None identified.

---

### D2 — Data Retention & Deletion | Score: 2

**Rationale:** Retention periods are specified for most data categories in a dedicated retention schedule appended to the policy. One category ("support correspondence") lists only "up to 3 years" without a more specific trigger. Deletion is automated with written confirmation available on request. Minor gap noted on backup retention specifics.

**Evidence Quotes:**
- *"Retention periods for each data category are set out in our Retention Schedule (Appendix B), ranging from 30 days (session logs) to 7 years (invoicing records, per legal obligation)."*
- *"Personal data is automatically deleted at the end of its retention period. You may request written confirmation of deletion."*
- *"User-initiated deletion requests are processed within 14 days."*

**Regulatory Gaps:**
- GDPR Art. 5(1)(e) — minor: backup retention period not explicitly stated (recommend clarification)

---

### D3 — Third-Party Data Sharing | Score: 1

**Rationale:** A complete sub-processor list is published and linked from the policy, with commit to 30-day advance notice of any additions. Data is explicitly never sold or used for advertising. All sub-processors are bound by DPAs with equivalent protections.

**Evidence Quotes:**
- *"We maintain a current list of all sub-processors at [link]. We provide 30 days' notice of any new sub-processor appointment."*
- *"We do not sell, rent, or share personal data with third parties for marketing or advertising purposes."*
- *"All sub-processors are contractually bound to process data only on our instructions and to maintain equivalent security standards."*

**Regulatory Gaps:** None identified.

---

### D4 — International Data Transfers | Score: 1

**Rationale:** The vendor is headquartered in Germany and processes all data within the EU/EEA. For the limited use of US-based sub-processors (AWS EU regions), Standard Contractual Clauses are in place with Transfer Impact Assessments completed and available to customers upon request.

**Evidence Quotes:**
- *"All personal data is processed within the European Economic Area. Our primary infrastructure is located in Frankfurt (AWS eu-central-1) and Amsterdam (AWS eu-west-1)."*
- *"Where we engage US-based sub-processors, we rely on EU Standard Contractual Clauses (2021 SCCs) as our transfer mechanism. Transfer Impact Assessments are available to customers upon written request."*

**Regulatory Gaps:** None identified.

---

### D5 — User Rights & Enforcement | Score: 1

**Rationale:** All GDPR data subject rights (Art. 15–21) are explicitly enumerated with individual explanations. Response timeline is 30 days (extendable to 90 days for complex requests with notification). A direct link to the German DPA (BfDI) complaint pathway is provided.

**Evidence Quotes:**
- *"You have the following rights under GDPR: [Art. 15 access, Art. 16 rectification, Art. 17 erasure, Art. 18 restriction, Art. 20 portability, Art. 21 objection — each described in detail]."*
- *"We will respond to all data subject requests within 30 days. For complex requests, we may extend this by a further 60 days with notice."*
- *"You have the right to lodge a complaint with the BfDI (Federal Commissioner for Data Protection and Freedom of Information): www.bfdi.bund.de."*

**Regulatory Gaps:** None identified.

---

### D6 — Security & Breach Notification | Score: 2

**Rationale:** Security measures are described with reasonable specificity (encryption in transit and at rest, role-based access, annual penetration testing). SOC 2 Type II audit is referenced but the report is not publicly available. Breach notification within 72 hours to the DPA is committed to in writing.

**Evidence Quotes:**
- *"We implement: AES-256 encryption at rest; TLS 1.3 in transit; role-based access controls with MFA required; annual third-party penetration testing."*
- *"We hold SOC 2 Type II certification. Reports are available to enterprise customers under NDA."*
- *"In the event of a personal data breach, we will notify the competent supervisory authority within 72 hours of becoming aware and notify affected individuals without undue delay where required."*

**Regulatory Gaps:**
- GDPR Art. 32 — minor: ISO 27001 not held; SOC 2 report not publicly available (recommend requesting report as part of vendor due diligence)

---

### D7 — AI & Automated Decision-Making | Score: 1

**Rationale:** The policy explicitly states no AI is used in processing personal data beyond spam filtering, which is categorised as not producing legal or similarly significant effects. No model training on customer data occurs. EU AI Act classification is noted as "minimal risk."

**Evidence Quotes:**
- *"We do not use artificial intelligence or automated decision-making that produces legal or similarly significant effects on individuals (GDPR Art. 22)."*
- *"Automated spam filtering is the only ML-based process applied to personal data. This is classified as minimal-risk under the EU AI Act 2024."*
- *"We do not use customer data to train or improve AI or machine learning models."*

**Regulatory Gaps:** None identified.

---

### D8 — Governance & Accountability | Score: 1

**Rationale:** A named DPO with contact details is provided. Legal bases for each processing activity are listed in a table. Privacy by Design is referenced in the development lifecycle section. ROPA maintenance is confirmed.

**Evidence Quotes:**
- *"Our Data Protection Officer is Dr. Anna Weber (dpo@example-cleardata.eu, +49 30 1234567)."*
- *"The legal basis for each processing activity is set out in the Processing Register (Appendix A), which includes: contract performance (Art. 6(1)(b)), legal obligation (Art. 6(1)(c)), and legitimate interests (Art. 6(1)(f)) with balancing tests available on request."*
- *"Privacy by Design is embedded in our software development lifecycle (SDLC). All new features undergo a Data Protection Impact Assessment (DPIA) screening before development begins."*

**Regulatory Gaps:** None identified.

---

## Overall Assessment

```json
{
  "overall_assessment": {
    "privacy_risk_score": 1.28,
    "risk_level": "Low",
    "weighted_calculation_note": "D7 and D4 weighted 1.5x. Formula: (1+2+1+1+1+2+(1×1.5)+(1×1.5)) / 9 = 1.28",
    "summary": "ClearData Solutions GmbH presents a low overall privacy risk (PRS 1.28/5.0) and demonstrates strong GDPR compliance maturity. The policy is transparent, specific, and operationalizable. The two minor gaps — backup retention specificity and SOC 2 report availability — do not pose material compliance risk and can be addressed through standard vendor questionnaire.",
    "top_3_risks": [
      {
        "dimension": "D2",
        "finding": "Backup retention period not explicitly stated — minor gap, recommend vendor clarification"
      },
      {
        "dimension": "D6",
        "finding": "SOC 2 Type II report available to enterprise customers only under NDA — request as part of procurement"
      },
      {
        "dimension": "D2",
        "finding": "Support correspondence retention ('up to 3 years') could be more precisely defined"
      }
    ],
    "recommended_actions": [
      "Proceed with standard procurement approval",
      "Request SOC 2 Type II report under NDA before contract execution",
      "Clarify backup retention period via vendor questionnaire",
      "Ensure DPA (GDPR Art. 28) is in place before processing EU personal data",
      "Log in vendor register with annual review date"
    ],
    "dpa_required": true,
    "dpo_escalation_required": false,
    "legal_review_required": false
  }
}
```
