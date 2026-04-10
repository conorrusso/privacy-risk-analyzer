# Legal Bandit Guide

Legal Bandit analyses vendor contracts — DPAs and MSAs — against GDPR Art. 28 requirements, EDPB guidance, and enforcement precedents. It produces a standalone redline brief with specific replacement language per gap.

---

## When Legal Bandit runs

### Automatically during bandit assess

If a DPA or MSA is present in the documents you provide, Legal Bandit runs automatically after the main privacy assessment:

```bash
bandit assess "Salesforce" --docs ./vendor-docs/salesforce/
bandit assess "Salesforce" --drive
```

The terminal shows contract findings after the main score, and the HTML report gains a legal section. A separate redline brief HTML file is saved alongside the main report.

### Standalone

Run Legal Bandit on its own when you only need contract analysis — no privacy policy assessment required:

```bash
bandit legal "Salesforce" --docs ./vendor-docs/salesforce/
bandit legal "Salesforce" --drive
```

This is faster than a full assess run when you already have a recent assessment and just received an updated DPA.

### Skipping the brief

If you want the contract findings in the terminal and main report but not the full redline brief HTML:

```bash
bandit assess "Salesforce" --drive --no-legal-brief
```

---

## The GDPR Art. 28(3) checklist

Every DPA is checked against all eight provisions of Art. 28(3). These are the mandatory terms a DPA must contain for GDPR compliance.

| Provision | What must be in the DPA |
|-----------|------------------------|
| Art. 28(3)(a) | Processor processes data only on documented instructions from the controller |
| Art. 28(3)(b) | Persons authorised to process the data have committed to confidentiality |
| Art. 28(3)(c) | Processor implements appropriate technical and organisational security measures (Art. 32) |
| Art. 28(3)(d) | Processor does not engage sub-processors without prior written authorisation; sub-processors are bound by equivalent obligations |
| Art. 28(3)(e) | Processor assists the controller with data subject rights requests (access, erasure, rectification, portability) |
| Art. 28(3)(f) | Processor assists with security obligations, breach notification, DPIAs, and prior consultation |
| Art. 28(3)(g) | At the controller's choice, processor deletes or returns all personal data after the end of services |
| Art. 28(3)(h) | Processor makes available all information necessary to demonstrate compliance; allows and contributes to audits |

A missing provision is a contract gap — a point where the DPA does not satisfy the GDPR minimum. Missing provisions are marked as **Required** in the redline brief.

### Vague language detection

Beyond presence or absence, Legal Bandit flags provisions that are technically present but written too vaguely to be enforceable. Common patterns:

- *"appropriate measures"* — no specification of what measures
- *"reasonable efforts"* — not an obligation, just a best-efforts commitment
- *"as required by applicable law"* — circular, adds nothing to GDPR's existing requirements
- *"in accordance with industry standards"* — undefined standard

Vague provisions are present but weak. They appear as **Recommended** improvements in the brief rather than Required gaps, unless the vagueness makes the provision effectively absent (e.g. Art. 28(3)(c) with no security specificity whatsoever).

### Absent vs present but vague

| Status | Meaning | Brief classification |
|--------|---------|---------------------|
| Absent | Provision not found in the DPA at all | Required |
| Present — vague | Found, but language is too generic to enforce | Recommended |
| Present — specific | Found with concrete, enforceable language | Acceptable |

---

## How to read the redline brief

The brief is a self-contained HTML file. Open it in a browser. It is structured into three sections.

### Required changes

Provisions that must be remediated before the DPA is GDPR-compliant. For each:

1. **Provision** — which Art. 28(3) clause is affected
2. **Current status** — Absent or Present but vague
3. **Verbatim current language** — the exact text from the DPA (or "Not found" if absent)
4. **Recommended replacement language** — specific clause text you can paste into redline negotiations
5. **Enforcement precedent** — a real GDPR enforcement action where this gap resulted in a fine, with the authority, year, and outcome

Example entry:

```
Art. 28(3)(h) — Audit rights

Status: Present — vague

Current language:
  "Vendor will cooperate with reasonable audit requests."

Recommended replacement:
  "Processor shall, upon reasonable written notice of no fewer than 30 days,
  make available to Controller or Controller's appointed auditor all information
  necessary to demonstrate compliance with the obligations set out in this DPA,
  and shall allow for and contribute to audits and inspections conducted by
  Controller or its mandated auditor."

Precedent: ICO (UK), 2022 — DPA lacking specific audit rights contributed to
  a £4.4M fine. Vague cooperation language found insufficient.
```

### Recommended improvements

Provisions that are legally present but would be materially strengthened with more specific language. Not required for GDPR compliance, but recommended for enforceability. Same format as Required — current language, replacement language, and rationale.

### Acceptable provisions

Provisions that are present with adequate specificity. Listed for completeness — no action needed. The verbatim DPA language is shown so Legal can confirm the assessment is reading the correct clause.

---

## SCC version and completeness check

Legal Bandit checks whether Standard Contractual Clauses are present and current.

**Outdated SCC detection:** SCCs published before June 2021 (the EU Commission's replacement set) are flagged as invalid. Contracts still referencing the 2010 Controller-to-Processor SCCs or the 2001 Controller-to-Controller SCCs are not valid transfer mechanisms under current GDPR. These appear as a Required gap in the brief.

**Module check:** The 2021 SCCs come in four modules. Legal Bandit checks which module the DPA references:

| Module | Transfer type |
|--------|--------------|
| Module 1 | Controller → Controller |
| Module 2 | Controller → Processor (most common) |
| Module 3 | Processor → Processor |
| Module 4 | Processor → Controller |

A missing module designation is flagged as a Recommended improvement — technically valid but ambiguous.

**TIA commitment:** Legal Bandit checks whether the DPA includes a commitment to conduct or make available a Transfer Impact Assessment. Absence is flagged as Recommended for vendors in high-risk third countries.

---

## MSA commercial terms assessment

When an MSA is provided, Legal Bandit assesses commercial data protection terms alongside the DPA review.

| Term | What is assessed |
|------|-----------------|
| Liability cap | Whether the cap covers data protection breaches specifically, or excludes them |
| Indemnification | Whether the vendor indemnifies the controller for third-party claims arising from processor breach |
| Data on termination | Whether the MSA commits to deletion/return timelines consistent with the DPA |
| DPA incorporation | Whether the MSA explicitly incorporates the DPA by reference |
| Regulatory cooperation | Whether the vendor commits to cooperate with supervisory authority investigations |

MSA findings appear in a separate **MSA Commercial Terms** section of the redline brief. A summary is also shown in the For Legal panel of the main HTML report.

---

## Policy/contract conflict detection

If the vendor's public privacy policy and DPA make contradictory commitments, Legal Bandit flags the conflict. Common examples:

- Privacy policy references Privacy Shield (invalid) — DPA uses SCCs (valid)
- Privacy policy says data is retained for 2 years — DPA says data is deleted within 30 days of termination
- Privacy policy claims sub-processor approval is not required — DPA grants prior general authorisation

**Bandit always scores based on the DPA** in a conflict. Contractual commitments take precedence over policy statements for scoring purposes.

Conflicts appear as:
- A yellow banner at the top of the main HTML report
- A dedicated **Conflicts** section in the redline brief
- A note in the For Legal panel recommending policy update

The policy should be updated to match the DPA. Having inconsistent public-facing claims and contractual terms is a regulatory risk even when the DPA is correct.

---

## Score changes from Legal Bandit

When the DPA provides stronger evidence than the public policy, dimension scores are updated. The terminal shows:

```
Contract findings
─────────────────────────────────────────────
D5  Breach Notification   1 → 4  ↑ Contract   48-hour SLA in DPA §8.2
D8  DPA Completeness      N/A → 2  ↑ Contract  3 gaps found in Art.28 checklist
D2  Sub-processors        2 → 4  ↑ Contract   Sub-processor list + flow-down confirmed
```

Score changes are also reflected in the main HTML report header (updated weighted average and risk tier).

In rare cases a DPA can lower a score — for example, if the DPA explicitly limits the vendor's obligations in a way the public policy does not mention. These appear with ↓ in the terminal.

---

## Disclaimer

The legal redline brief is generated by an AI agent and is not legal advice. Replacement language suggestions are based on GDPR Art. 28 requirements and enforcement precedents, but should be reviewed by qualified legal counsel before use in contract negotiations.
