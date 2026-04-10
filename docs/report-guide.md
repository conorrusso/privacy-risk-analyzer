# Reading a Bandit Report

Every `bandit assess` run saves an HTML report to `./reports/`. This guide explains each section.

Open the file in any browser. All sections are collapsible — click a dimension heading to expand it. Print to PDF with Ctrl+P / Cmd+P (all sections expand automatically).

---

## Understanding assessment scope

Every report shows what documents were assessed. The scope depends on what you provided:

| Dimension | Public policy only | With DPA | With DPA + supporting docs |
|-----------|--------------------|----------|---------------------------|
| D1, D3, D6, D7 | Fully assessed | Fully assessed | Fully assessed |
| D2, D4, D5 | Partially assessed | Fully assessed | Fully assessed |
| D8 | Not assessed | Fully assessed | Fully assessed |

When you see **Requires DPA** on D8: this is not a failure. It means Bandit cannot assess DPA completeness without the DPA document. Upload the DPA with `--docs` or connect Google Drive with `--drive` to enable full D8 scoring.

When you see **Partially assessed** on D2, D4, or D5: the score reflects genuine evidence from the policy. The DPA would fill in the contractual obligations that a privacy policy doesn't cover.

---

## Evidence confidence levels

Each dimension in the report shows a confidence indicator:

**Confirmed** — policy was successfully fetched with substantial content. The score reflects genuine evidence or a genuine gap. High confidence that the vendor either has the practice or doesn't.

**Partially assessed** — the dimension can be partially scored from the public policy but a DPA would complete it. The score is real; it's just based on partial information. Indicated with ◐ in the terminal and a note in the expanded dimension body.

**Requires DPA** — dimension cannot be scored from public policy alone. Excluded from the weighted average. The overall score and tier are calculated without this dimension. Indicated with ○ N/A.

---

## Summary header

The top of the report shows:

- **Vendor name** and assessment date
- **Active profile** — if `bandit.config.yml` exists, the profile is shown with the industry label and any modified dimension weights
- **Risk tier** — LOW, MEDIUM, or HIGH
- **Weighted average** — the overall score (1–5 scale), calculated over assessed dimensions only

Risk tier thresholds:

| Tier | Weighted average |
|------|-----------------|
| HIGH | < 2.5 |
| MEDIUM | 2.5 – 3.5 |
| LOW | > 3.5 |

---

## Active profile in the report header

If `bandit.config.yml` exists, the report header shows your active profile:

```
Profile: EU Technology · GDPR · CCPA/CPRA
Modified weights: D4 ×2.0 · D3 ×1.5 · D8 ×2.0
```

This means dimension weights were adjusted based on your setup configuration. A score that would be MEDIUM on default weights may be HIGH on an EU profile because D4 (transfer mechanisms) carries more weight. The weighted average in the header reflects your profile weights, not the defaults.

---

## Escalation banner

Some findings trigger automatic escalation regardless of the weighted average score.

Configured in `bandit setup` under Risk appetite. Common default triggers:

- AI training on customer data with no opt-out
- No DPA exists (D8 = 1, Confirmed)
- Breach notification entirely absent (D5 = 1)
- Privacy Shield referenced (outdated transfer mechanism)

When triggered, a red banner appears at the top of the report with the specific reason. The GRC section decision changes to **ESCALATE**.

---

## Dimension scores

Eight dimensions, each scored 1–5:

| Score | Meaning |
|-------|---------|
| 5 | All signals present, no red flags |
| 4 | Strong — minor gaps only |
| 3 | Partial — material gaps present |
| 2 | Weak — most signals absent |
| 1 | No evidence found |

D6 (AI/ML data usage) and D8 (DPA completeness) are weighted ×1.5 in the average by default. Weights change based on your `bandit setup` profile.

Click any dimension row to expand it.

---

## Evidence found

Green ✓ items — signals that were confirmed present in the policy text. These are the specific criteria the vendor met for their score level.

---

## Gaps identified

Amber ✗ items — signals that are absent or not confirmed. These are the criteria that would be required to reach the next score level.

Each gap includes **follow-up questions** to ask the vendor (2–3 per gap). These feed directly into the vendor email template at the bottom of the report.

---

## Red flags

Red ⚠ items — enforcement-backed phrases or patterns that cap the dimension score, regardless of other signals.

Each red flag shows:
- The flag label and what it means
- The matched text from the policy (so you can verify it)
- The score ceiling it enforces

Red flags are drawn from GDPR enforcement actions, FTC settlements, and EDPB guidance.

---

## Contract recommendations

For any dimension scoring ≤ 3, the report includes specific DPA or MSA language to request from the vendor.

These are ready for Legal to paste into contract negotiations. Each recommendation names the clause type and the specific language to add.

---

## Team summary

Three stacked panels, one per team:

### GRC
- Risk tier and recommended action (approve / conditional / escalate)
- Re-assess trigger date based on risk tier
- Summary of the key findings driving the decision
- If auto-escalation was triggered, decision shows **ESCALATE** with specific reasons

### Legal
- All contract recommendations consolidated in one place
- Prioritised by dimension weight and score

### Security
- D5 (breach notification), D6 (AI/ML), D8 (DPA completeness) scores in detail
- Framework certifications found (SOC 2, ISO 27001, etc.)
- Gaps that require technical controls to compensate

---

## Vendor email template

A ready-to-send email at the bottom of the report, pre-populated with:
- All gap questions from across all dimensions
- Grouped by topic (not by internal dimension code)
- Professional framing suitable for sending to a vendor's privacy or legal contact

Copy the template, paste it into your email client, and add the vendor contact.

---

## Sources

The footer of the report lists every URL that was fetched and used in the assessment, with the character count and fetch method (direct or via Jina Reader).

Use this to verify Bandit found the right policy — if the URL looks wrong, re-run with the correct URL passed directly:

```bash
bandit assess https://vendor.com/correct-privacy-policy
```

---

## Documents assessed section

Every report shows exactly what was assessed:

```
Documents assessed:
✓ Privacy policy    https://salesforce.com/privacy
✓ DPA               dpa.pdf (24 pages)
✓ SOC 2 Type II     soc2-2025.pdf (142 pages)
✓ Sub-processor list sub-processors.pdf
✗ MSA               not provided
✗ BAA               not applicable (no PHI in profile)
```

Status meanings:
- **✓ Assessed** — document was read and signals extracted
- **✗ Not provided** — document not in the docs folder
- **— Not applicable** — not relevant for this vendor profile

Required documents that are missing show in red with a note recommending you request them from the vendor before proceeding to contract.

---

## Signal source attribution

In each expanded dimension section, every piece of evidence shows which document it came from:

```
Evidence found:
✓ Breach notification SLA: 48 hours
  Source: dpa.pdf §8.2 Breach Notification

✓ Sub-processor list available (23 processors)
  Source: sub-processors.pdf

✓ AI training opt-out available
  Source: privacy-policy (salesforce.com/privacy)
```

This is important for the Legal team — they need to know whether a commitment came from the public policy (not contractually binding) or the DPA (contractually binding and enforceable).

A commitment in a DPA is worth significantly more than the same commitment in a privacy policy. Bandit shows both and distinguishes them.

---

## How signal merging works

When multiple documents are assessed, Bandit merges signals from all sources into a unified evidence set.

The merging logic:
- If a signal appears only in one document → use it
- If multiple documents confirm the same signal → keep
- If a document provides a stronger commitment than the policy → upgrade to the stronger version
- If documents contradict each other → flag both, use the stronger commitment, note the contradiction

**Example:** privacy policy says "we will notify you of breaches promptly" (vague). DPA says "within 48 hours" (specific). The DPA commitment wins. D5 scores based on the 48-hour SLA not the vague policy language. The report shows both and notes the DPA as the source.

---

## D8 DPA Completeness — public policy vs DPA

**Without a DPA:**

D8 shows as "Requires DPA" — not scored. Excluded from weighted average. The For Legal section recommends requesting a DPA before contract signature.

**With a DPA:**

D8 is fully scored against the GDPR Art. 28(3)(a)-(h) checklist. Each provision is checked:

| Provision | What is checked |
|-----------|----------------|
| Art. 28(3)(a) | Processing only on controller instructions |
| Art. 28(3)(b) | Confidentiality obligations on personnel |
| Art. 28(3)(c) | Security measures (specific vs generic language) |
| Art. 28(3)(d) | Sub-processor approval requirement and flow-down |
| Art. 28(3)(e) | Data subject rights assistance committed |
| Art. 28(3)(f) | DPIA and prior consultation assistance |
| Art. 28(3)(g) | Deletion or return of data on termination |
| Art. 28(3)(h) | Audit rights and inspection access |

Missing provisions appear as gaps with specific redline language in the For Legal section.

---

## Legal Bandit additions to the report

When DPA or MSA documents are present, Bandit automatically runs Legal Bandit after the main assessment. This adds several elements to both the terminal output and the HTML report.

### Score source attribution

Each dimension header in the expanded view shows where its score came from:

```
D5  Breach Notification   4/5   Source: Contract
D2  Sub-processors        3/5   Source: Policy
D8  DPA Completeness      2/5   Source: Contract
```

- **Policy** — score derived from the public privacy policy
- **Contract** — score upgraded (or downgraded) by a contractual commitment in the DPA or MSA
- **Policy + Contract** — both sources contributed; the stronger commitment was used

This matters because a contractual commitment is enforceable. A policy claim is not.

### Contract findings in the terminal

After the assessment completes, the terminal shows a contract findings summary:

```
Contract findings
─────────────────────────────────────────────
D5  Breach Notification   1 → 4  ↑ Contract   48-hour SLA in DPA §8.2
D8  DPA Completeness      N/A → 2  ↑ Contract  Art.28 checklist — 3 gaps
D7  Data Retention        3 → 3    Contract    No change — policy and DPA consistent
```

The format `D5 1→4 ↑ Contract` means: D5 was scored 1 from the public policy alone; the DPA raised it to 4.

### Policy/contract conflict banner

If the DPA and privacy policy make contradictory commitments, a conflict banner appears at the top of the report:

```
⚠ Policy/contract conflict detected
  D4 Transfer Mechanisms: Privacy policy references Privacy Shield (invalid).
  DPA §6 uses SCC Module 2 (valid). DPA governs — score based on DPA.
```

Bandit always scores based on the DPA in a conflict. The banner is shown so Legal can reconcile or update the public policy.

### For Legal panel — brief summary

The Legal team summary panel at the bottom of the report is extended when Legal Bandit runs. It includes:

- A brief summary of contract gap findings (gaps, vague provisions, missing provisions)
- Link to the standalone legal redline brief HTML file (saved alongside the main report)
- Policy/contract conflicts requiring policy updates
- MSA commercial terms summary (liability cap, indemnification, data on termination)

The full redline brief with verbatim quotes, specific replacement language, and enforcement precedents is in the separate brief file. See [Legal Bandit Guide](legal-guide.md) for how to read it.
