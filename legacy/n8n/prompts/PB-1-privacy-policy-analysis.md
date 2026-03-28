# Prompt Template: PB-1 — Privacy Policy Risk Analysis

**Version:** 1.0
**Compatible Models:** Claude, GPT-4o, Gemini, Mistral, Ollama
**Output Format:** Structured JSON
**Regulatory Coverage:** GDPR, CCPA, EU AI Act 2024

---

## System Prompt

```
You are a senior privacy counsel and data protection specialist. Your role is to analyze vendor privacy policies and data processing agreements for compliance risk. You apply GDPR (EU) 2016/679, CCPA/CPRA (California), and the EU AI Act 2024 as your primary frameworks. You are precise, evidence-based, and conservative: when a policy is ambiguous or silent on a point, you score it as a risk rather than an assumption of compliance.

Always return valid JSON. Never add commentary outside the JSON block.
```

---

## User Prompt

```
Analyze the following vendor privacy policy and produce a structured risk assessment.

## Vendor Information
- Vendor Name: {{vendor_name}}
- Policy URL: {{policy_url}} (if available)
- Assessment Date: {{assessment_date}}
- Assessor: Bandit Automated Review

## Policy Text
{{policy_text}}

---

## Instructions

Score this policy across the 8 dimensions below (D1–D8). For each dimension:
1. Assign a score from 1 (low risk) to 5 (critical risk)
2. Provide a brief rationale (2–4 sentences) citing specific language or absence of language from the policy
3. List specific evidence quotes from the policy (or note "Not found" if absent)
4. Identify applicable regulatory gaps (GDPR Articles, CCPA provisions, EU AI Act articles)

### Scoring Dimensions

**D1 — Data Collection Scope**
Assess breadth and proportionality of data collected. Look for: categories of personal data, sensitive data (Art. 9 GDPR / CCPA), inferred data, behavioral profiling.
- Score 1: Only collects what's explicitly necessary, named categories only
- Score 3: Collects broad categories with some vague "including but not limited to" language
- Score 5: Collects all available data without limitation, includes sensitive categories without explicit consent mechanism

**D2 — Data Retention & Deletion**
Assess clarity and enforceability of retention periods. Look for: specific retention periods per data type, deletion procedures, user deletion rights, backup retention.
- Score 1: Specific retention periods for each data category, automated deletion, user-triggered deletion honored within 30 days
- Score 3: General retention language ("as long as necessary") with some exceptions noted
- Score 5: No retention periods specified, no deletion commitment, or "indefinite" language present

**D3 — Third-Party Data Sharing**
Assess scope and control over data sharing. Look for: named third parties or categories, purpose limitation for sharing, sub-processor lists, data broker relationships.
- Score 1: Exhaustive list of named third parties, purpose-limited sharing, no selling/sharing with data brokers
- Score 3: Categories of third parties named, sharing for "business purposes," opt-out for sale available
- Score 5: Broad sharing with unnamed "partners," data sold/shared without restriction, no sub-processor transparency

**D4 — International Data Transfers**
Assess adequacy of cross-border transfer safeguards. Look for: SCCs, BCRs, adequacy decisions, transfer impact assessments, specific countries named.
- Score 1: SCCs or BCRs in place, transfer countries listed, TIA conducted
- Score 3: References SCCs or "adequate safeguards" without specifics
- Score 5: No transfer mechanism named, US-based vendor processing EU data without safeguard mention, or Privacy Shield (invalidated) cited

**D5 — User Rights & Enforcement**
Assess comprehensiveness and operationalizability of data subject rights. Look for: access, rectification, erasure, portability, objection, restriction, complaint pathways, response timelines.
- Score 1: All GDPR Art. 15–21 rights explicitly granted, response within 30 days, DPA complaint pathway linked
- Score 3: Core rights (access, deletion) mentioned, response timeline vague or longer than 90 days
- Score 5: Rights not mentioned, claim rights aren't applicable, no contact method for requests

**D6 — Security & Breach Notification**
Assess security commitment and breach response capability. Look for: encryption standards, access controls, certifications (ISO 27001, SOC 2), breach notification timeline, incident contact.
- Score 1: Specific technical measures listed, certified (SOC 2 / ISO 27001), 72-hour GDPR breach notification committed
- Score 3: General "industry standard" security language, breach notification mentioned without timeline
- Score 5: No security specifics, no breach notification commitment, or notification timeline exceeds GDPR 72-hour requirement

**D7 — AI & Automated Decision-Making**
Assess transparency and control over AI/ML processing. Look for: profiling disclosure, automated decision-making (Art. 22 GDPR), AI system transparency (EU AI Act), model training on user data, human review options.
- Score 1: AI use disclosed, no automated decisions with legal effect, human review available, no training on user data without consent
- Score 3: Some AI disclosure, automated decisions present but opt-out available, training data use vague
- Score 5: AI processing not disclosed, automated decisions with legal/significant effect with no human review, user data used to train models by default without consent

**D8 — Governance & Accountability**
Assess organizational privacy maturity. Look for: DPO appointment (GDPR Art. 37), Privacy by Design (Art. 25), ROPA maintenance, legal basis for each processing activity, privacy contact.
- Score 1: DPO named with contact, ROPA maintained, legal basis stated per processing purpose, Art. 25 compliance claimed
- Score 3: Privacy contact exists, legal bases partially stated, some accountability language
- Score 5: No privacy contact, no DPO, no legal basis stated for any processing activity

---

## Required Output Format

Return ONLY the following JSON structure with no additional text:

{
  "assessment_metadata": {
    "vendor_name": "string",
    "policy_url": "string or null",
    "assessment_date": "ISO 8601 date",
    "prompt_version": "PB-1 v1.0",
    "model_used": "string — fill with the model identifier you are running on"
  },
  "dimension_scores": {
    "D1": {
      "label": "Data Collection Scope",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": ["GDPR Art. X", "CCPA §Y", "..."]
    },
    "D2": {
      "label": "Data Retention & Deletion",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": []
    },
    "D3": {
      "label": "Third-Party Data Sharing",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": []
    },
    "D4": {
      "label": "International Data Transfers",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": []
    },
    "D5": {
      "label": "User Rights & Enforcement",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": []
    },
    "D6": {
      "label": "Security & Breach Notification",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": []
    },
    "D7": {
      "label": "AI & Automated Decision-Making",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": []
    },
    "D8": {
      "label": "Governance & Accountability",
      "score": 1-5,
      "rationale": "string",
      "evidence_quotes": ["string", "..."],
      "regulatory_gaps": []
    }
  },
  "overall_assessment": {
    "privacy_risk_score": 0.0,
    "risk_level": "Low | Medium | High | Critical",
    "weighted_calculation_note": "D7 and D4 weighted 1.5x for EU AI Act and international transfer relevance",
    "summary": "2–3 sentence executive summary of the key risks",
    "top_3_risks": [
      {"dimension": "DX", "finding": "string"},
      {"dimension": "DX", "finding": "string"},
      {"dimension": "DX", "finding": "string"}
    ],
    "recommended_actions": [
      "string",
      "string",
      "string"
    ],
    "dpa_required": true | false,
    "dpo_escalation_required": true | false,
    "legal_review_required": true | false
  }
}
```

---

## Weighting Formula

The Privacy Risk Score (PRS) is calculated as:

```
PRS = (D1 + D2 + D3 + D5 + D6 + D8 + (D4 × 1.5) + (D7 × 1.5)) / 9
```

D4 (International Transfers) and D7 (AI/Automated Decision-Making) carry 1.5× weight to reflect the elevated regulatory exposure under GDPR Chapter V and the EU AI Act respectively.

---

## Usage Notes

- If the policy text is truncated or unavailable, score D1–D8 as 4 (high risk) with rationale "Policy not available for review."
- If the vendor is not subject to GDPR (no EU operations, no EU data subjects), mark EU regulatory gaps as "N/A — not in scope."
- For AI vendors, D7 should always be scored even if the policy does not mention AI.
- This prompt is intended for initial triage only. A score of 3.6+ should always trigger human legal review.
