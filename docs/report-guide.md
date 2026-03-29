# Reading a Bandit Report

Every `bandit assess` run saves an HTML report to `./reports/`. This guide explains each section.

Open the file in any browser. All sections are collapsible — click a dimension heading to expand it. Print to PDF with Ctrl+P / Cmd+P (all sections expand automatically).

---

## Summary header

The top of the report shows:

- **Vendor name** and assessment date
- **Risk tier** — LOW, MEDIUM, or HIGH
- **Weighted average** — the overall score (1–5 scale)
- **Per-dimension bar chart** — a quick visual of where the vendor is strong or weak

Risk tier thresholds:

| Tier | Weighted average |
|------|-----------------|
| HIGH | < 2.5 |
| MEDIUM | 2.5 – 3.5 |
| LOW | > 3.5 |

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

D6 (AI/ML data usage) and D8 (DPA completeness) are weighted ×1.5 in the average.

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
- Risk tier and recommended action (approve / conditional / reject)
- Re-assess trigger date based on risk tier
- Summary of the key findings driving the decision

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
