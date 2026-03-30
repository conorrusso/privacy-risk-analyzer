# Bandit Setup Guide

`bandit setup` runs a short wizard that tailors Bandit to your organisation's specific regulatory context. This guide explains what it does and how to get the most out of it.

---

## Why run bandit setup?

Without setup, Bandit uses default weights — a GDPR-focused, technology company baseline with D6 (AI/ML) and D8 (DPA) at ×1.5.

With setup, Bandit adjusts for your specific context:

- A **healthcare company** gets D5 (breach notification) and D3 (rights) weighted higher, plus HIPAA breach timeline checks
- An **EU-based company** gets D4 (transfer mechanisms) weighted higher and EU adequacy monitoring checks
- A **financial services company** gets D7 (retention), D5, and D8 weighted higher with PCI-DSS and SOX considerations
- A company handling **special categories of data** gets D1 and D3 weighted higher
- A company buying **AI vendors** gets D6 weighted higher across all assessments

The rubric logic doesn't change. The weights change. Same signals, different emphasis.

---

## Running setup

```bash
bandit setup
```

Takes about 2 minutes. The wizard asks 18 questions across 6 sections, shows you a weight preview, and writes `bandit.config.yml` in the current directory.

Run it once. Update it with `bandit setup --reset` when your regulatory context changes.

To see your current profile without re-running the wizard:

```bash
bandit setup --show
```

---

## Question by question

### Section 1 — Company location

**Q1: Where is your company headquartered?**

Options: EU/EEA, UK, US, Canada, APAC, Other.

If you select EU/EEA or UK: D4 (transfer mechanisms) weight increases by +1.0 and D3 (data subject rights) by +0.5. This reflects that EU/UK organisations face direct regulatory liability for cross-border transfer compliance.

**Q2: Where are your customers located?**

Multi-select. If you include EU/EEA or UK customers: same weight adjustments as Q1 (if not already applied). This catches US companies with EU customer bases who are in scope for GDPR as controllers.

**Q3: Where is your data processed and stored?**

Multi-select. If you select EU + US (cross-border): D4 weight increases by an additional +0.5 on top of any Q1/Q2 adjustment. Cross-border transfers are a distinct enforcement risk from simply having EU customers.

---

### Section 2 — Industry

**Q4: What is your primary industry?**

Options: Technology/SaaS, Healthcare/Life Sciences, Financial Services, Retail/E-commerce, Education, Legal/Professional Services, Government/Public Sector, Other.

Healthcare → D5 (breach) +1.0, D1 (minimization) +0.5, D3 (rights) +0.5
Financial Services → D7 (retention) +0.5, D5 +0.5, D8 (DPA) +0.5

---

### Section 3 — Data types

**Q5: Do you process Protected Health Information (PHI)?**

If yes: D5 (breach) +1.0, D1 (minimization) +0.5, D3 (rights) +0.5, D8 (DPA) +0.5. PHI triggers HIPAA breach notification requirements with a 60-day timeline (stricter than GDPR's 72 hours to the authority).

**Q6: Do you process Payment Card Industry data (PCI)?**

If yes: D7 (retention) +0.5, D8 (DPA) +0.5, D5 (breach) +0.5. PCI-DSS has specific cardholder data deletion and breach notification requirements.

**Q7: Do you process data about children (under 13/16)?**

If yes: D1 (minimization) +0.5, D3 (rights) +0.5. COPPA and GDPR Art. 8 set higher standards for lawful basis and parental consent.

**Q8: Do you process special categories of personal data?**

Special categories include health, biometric, genetic, racial/ethnic origin, religious beliefs, political opinions, sexual orientation, trade union membership, criminal records.

If yes: D1 (minimization) +0.5, D3 (rights) +0.5, D6 (AI/ML) +0.5. Special categories under GDPR Art. 9 require explicit consent or a specific Art. 9(2) exception — the bar is higher.

**Q9: Do you primarily assess AI/ML vendors?**

If yes: D6 (AI/ML usage) +0.5 across all assessments. EU AI Act and FTC disgorgement precedent make AI training clauses a priority risk.

**Q10: Roughly how many vendor assessments per year?**

Informational only. Used to calibrate the escalation threshold recommendations in Section 5.

---

### Section 4 — Regulatory frameworks

**Q11: Which regulatory frameworks apply to your organisation?**

Multi-select: GDPR, UK GDPR, HIPAA/HITECH, CCPA/CPRA, PCI-DSS, SOX, PIPEDA, Other.

This is used to inform contract recommendation language in reports. A HIPAA-scoped company sees HIPAA BAA language in D5 contract recommendations; a CCPA company sees CPRA service provider provisions in D8.

**Q12: Do you have a DPO or privacy lead?**

If yes: Bandit assumes a higher maturity baseline and adjusts the re-assess cycle recommendation accordingly.

---

### Section 5 — Risk appetite

**Q13: What is your organisation's risk appetite?**

Options: Conservative (flag everything), Balanced (flag material risks), Permissive (flag critical risks only).

Conservative → lower escalation thresholds
Permissive → higher thresholds, fewer escalations

**Q14: At what risk tier do you want automatic escalation?**

Options: HIGH only, HIGH or MEDIUM, Never.

If you select HIGH only: an `auto_escalate` trigger is added for `tier: HIGH`.
If you select HIGH or MEDIUM: triggers are added for both tiers.

**Q15: Escalate if a vendor has no AI training opt-out?**

If yes: adds an `auto_escalate` trigger for `red_flag: ai_training_no_opt_out`. Any vendor with this red flag is escalated regardless of their overall tier.

---

### Section 6 — Team routing

**Q16: Who reviews assessments?**

Options: GRC only, GRC + Legal, GRC + Legal + Security, Full team.

Determines which team panels appear in the report.

**Q17: How often should vendors be re-assessed?**

Options: 90 days (quarterly), 180 days (semi-annual), 365 days (annual), 730 days (biennial).

Stored as a number of days. The re-assess date in the GRC panel is calculated from this value.

**Q18: What is your privacy programme maturity?**

Options: Early stage, Developing, Established, Advanced.

Used to calibrate recommendation language — early-stage teams get more prescriptive guidance; advanced teams get more concise output.

---

## Weight calculation summary

Base weights (default): D1=1.0, D2=1.0, D3=1.0, D4=1.0, D5=1.0, D6=1.5, D7=1.0, D8=1.5

Modifiers are additive and stacked across all applicable answers. Weights are clamped between 0.5 and 3.0.

Example — EU healthcare company processing PHI with a conservative risk appetite:

| Dim | Base | EU HQ | Healthcare | PHI | Final |
|-----|------|-------|------------|-----|-------|
| D1 | 1.0 | — | +0.5 | +0.5 | 2.0 |
| D3 | 1.0 | +0.5 | +0.5 | +0.5 | 2.5 |
| D4 | 1.0 | +1.0 | — | — | 2.0 |
| D5 | 1.0 | — | +1.0 | +1.0 | 3.0 |
| D8 | 1.5 | — | — | +0.5 | 2.0 |

---

## Editing the config directly

`bandit.config.yml` is human-readable YAML. Power users can edit it directly.

```yaml
profile:
  hq_region: EU/EEA
  customer_regions:
    - EU/EEA
    - US
  industry: Healthcare/Life Sciences
  processes_phi: true
  processes_pci: false
  processes_children_data: false
  processes_special_categories: true
  assesses_ai_vendors: false
  regulatory_frameworks:
    - GDPR
    - HIPAA/HITECH
  has_dpo: true
  risk_appetite: Conservative
  escalation_tier: HIGH only
  escalate_ai_no_opt_out: true
  review_team: GRC + Legal + Security
  reassess_days: 90
  maturity: Established

auto_escalate:
  - type: tier
    value: HIGH
  - type: red_flag
    value: ai_training_no_opt_out
```

Valid values:

| Key | Valid values |
|-----|-------------|
| `hq_region` | `EU/EEA`, `UK`, `US`, `Canada`, `APAC`, `Other` |
| `industry` | `Technology/SaaS`, `Healthcare/Life Sciences`, `Financial Services`, `Retail/E-commerce`, `Education`, `Legal/Professional Services`, `Government/Public Sector`, `Other` |
| `risk_appetite` | `Conservative`, `Balanced`, `Permissive` |
| `reassess_days` | `90`, `180`, `365`, `730` |
| `maturity` | `Early stage`, `Developing`, `Established`, `Advanced` |
| `auto_escalate[].type` | `tier`, `score_below`, `red_flag`, `weighted_average_below` |

---

## Per-vendor overrides

Some vendors need different settings than your global config — for example, a healthcare vendor assessed by a technology company that doesn't normally process PHI.

Per-vendor flag overrides are planned for v1.1. For now, the simplest approach is to run `bandit setup --reset` before assessing the vendor, then reset back after.

Alternatively, pass the full URL directly to skip discovery and use a temporary config:

```bash
BANDIT_CONFIG=./healthcare.config.yml bandit assess "Epic Systems"
```

(`BANDIT_CONFIG` env var support coming in v1.1)
