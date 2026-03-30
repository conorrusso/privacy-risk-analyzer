# Reading a Bandit Report

Every `bandit assess` run saves an HTML report to `./reports/`. This guide explains each section.

Open the file in any browser. All sections are collapsible — click a dimension heading to expand it. Print to PDF with Ctrl+P / Cmd+P (all sections expand automatically).

---

## Understanding assessment scope

Every report shows what documents were assessed. In v1.0 this is always the public privacy policy.

What this means for each dimension:

| Dimension | Status | Notes |
|-----------|--------|-------|
| D1, D3, D6, D7 | Fully assessed | Sufficient from public privacy policy |
| D2, D4, D5 | Partially assessed | Scores reflect what's in the policy — DPA would complete these |
| D8 | Not assessed | Requires DPA document |

When you see **Requires DPA** on D8: this is not a failure. It means Bandit cannot assess DPA completeness without the DPA document. This is expected in v1.0. Google Drive integration in v1.1 will enable full D8 scoring.

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
