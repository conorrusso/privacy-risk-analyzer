# Bandit Setup Guide

`bandit setup` runs a short wizard that tailors Bandit to your organisation's regulatory context. This guide explains what it does and how to get the most out of it.

---

## Why run bandit setup?

Without setup, Bandit uses default weights — a GDPR-focused, technology company baseline with D6 (AI/ML) and D8 (DPA) at ×1.5.

With setup, Bandit adjusts for your specific context:

- A **healthcare company** gets D5 (breach notification) and D3 (rights) weighted higher, plus HIPAA breach timeline checks
- An **EU-based company** gets D4 (transfer mechanisms) weighted higher and EU adequacy monitoring checks
- A **financial services company** gets D7 (retention), D5, and D8 weighted higher
- A company handling **PHI** gets D5, D3, D1, and D8 escalated with HIPAA framework inference
- A **strict** risk approach sets 6-month HIGH vendor reassessment and escalates MEDIUM vendors too

The rubric logic doesn't change. The weights change. Same signals, different emphasis.

---

## Running setup

```bash
bandit setup
```

Takes about 2 minutes. The wizard asks 5 core questions (+ up to 3 conditional ones based on your answers), then shows you an inferred profile with framework detection, weight changes, and reassessment schedule for review before writing `bandit.config.yml`.

If you run `bandit assess` without a config, Bandit will prompt you to run setup before starting — you can set up inline or skip it and assess with default weights.

Run it once. Update it with `bandit setup --reset` when your regulatory context changes.

To see your current profile without re-running the wizard:

```bash
bandit setup --show
```

Progress is saved after every question. If setup is interrupted (Ctrl+C or crash), running `bandit setup` again will offer to resume.

---

## Choosing an AI provider

Bandit works with five AI providers. Run:

```bash
bandit setup --provider
```

Or edit `bandit.config.yml` directly under the `provider:` section.

All providers use the same scoring engine — only the extraction and analysis calls use the LLM. Scores are always deterministic once signals are extracted.

| Provider | Best for | Cost |
|----------|----------|------|
| Claude (Anthropic) | Best accuracy for GRC/privacy analysis | ~$0.01–0.05/assessment |
| GPT-4o (OpenAI) | Strong general performance | ~$0.05–0.15/assessment |
| Gemini 2.0 Flash | Fast, very low cost | ~$0.00–0.01/assessment |
| Ollama (local) | Privacy-sensitive / offline / free | Free |
| Mistral | European data residency | ~$0.02–0.08/assessment |

For fully local/offline use, choose Ollama with a model like `llama3` or `mistral`. Quality will be lower than cloud providers but no data leaves your machine.

---

## Question by question

### Q1 — Organisation type

Single select from: Healthcare / Pharma, Financial Services / FinTech, Technology / SaaS, Education / EdTech, Government / Public Sector, Retail / E-commerce, Professional Services, Non-profit, Other.

Used to pre-select data type suggestions in Q3 and to apply industry-specific weight modifiers.

- **Healthcare / Pharma** → pre-selects PHI in Q3; adds D5 weight boost
- **Financial Services / FinTech** → pre-selects PCI in Q3; adds D7 + D5 weight boost
- **Education / EdTech** → pre-selects children's data in Q3

---

### Q2 — Locations

Multi-select: United States, European Union / EEA, United Kingdom, Canada, APAC, Other.

This is the biggest weight driver. EU/EEA presence raises D4 (cross-border transfers) by +1.0, D3 (data subject rights) by +0.5, and D8 (DPA) by +0.5. This reflects that EU/UK organisations face direct regulatory liability for cross-border transfer compliance.

Triggers conditional Q6 (infrastructure location) if EU/EEA or UK is selected.

---

### Q3 — Sensitive data types

Multi-select. Shows all options with pre-selected suggestions based on Q1.

| Option | Weight effect |
|--------|--------------|
| PHI / Medical records | D5+1.0, D1+0.5, D3+0.5, D8+0.5 |
| Payment card data | D7+0.5, D8+0.5, D5+0.5 |
| Children's data | D1+0.5, D3+0.5 |
| Biometric data | D1+0.5, D3+0.5, D6+0.5 |
| Employee / HR records | D1+0.3, D3+0.3 |
| Special categories | D1+0.5, D3+0.5, D6+0.5 |

Selecting PHI triggers conditional Q7 (BAA requirement).
Selecting payment card triggers conditional Q8 (PCI merchant level).

---

### Q4 — Required certifications

Multi-select with pre-selected suggestions based on Q2 + Q3.

| Option | Auto-suggested when |
|--------|---------------------|
| SOC 2 Type II | Always (default) |
| ISO 27001 | — |
| HIPAA BAA | PHI selected in Q3 |
| PCI DSS compliance letter | Payment card selected in Q3 |
| GDPR DPA / Article 28 agreement | EU/EEA in Q2 |
| UK GDPR DPA | UK in Q2 |
| None required | — |

Certifications selected here appear in the `document_requirements` and `frameworks.certifications_required` sections of the config.

---

### Q5 — Risk approach

Single select with a default of **Standard**.

| Option | HIGH cadence | MEDIUM cadence | LOW cadence | Escalation |
|--------|-------------|----------------|-------------|------------|
| Strict | Every 6 months | Every year | Every 2 years | HIGH + MEDIUM |
| Standard | Every year | Every 2 years | One-time scan | HIGH only |
| Pragmatic | Every year | Every 3 years | None | HIGH + red flags |

This single question replaces the 9-question reassessment section from the previous wizard version.

---

### Conditional Q6 — Infrastructure location

Only asked if EU/EEA or UK is in Q2.

Options: EU / EEA only, US only, Both EU and US, Other / unknown.

If **Both EU and US** or **US only**: adds an additional D4 +0.5 on top of the Q2 EU presence modifier. This captures the cross-border transfer risk from EU controller → US processor.

---

### Conditional Q7 — BAA requirement

Only asked if PHI / Medical records is selected in Q3.

Records your organisation's HIPAA Business Associate Agreement policy. Written to `company.baa_required` in the config. Informs the HIPAA framework inference.

---

### Conditional Q8 — PCI merchant level

Only asked if payment card data is selected in Q3.

Records PCI merchant level (Level 1, 2, or 3/4). Written to `company.pci_level` in the config. Higher levels have stricter reporting and assessment requirements.

---

## Inference summary

After completing the questions, Bandit shows a review screen before saving. This includes:

- **Profile summary** — org type, locations, inferred frameworks, required certifications
- **Dimension weights** — which dimensions changed and by how much vs default
- **Reassessment schedule** — HIGH/MEDIUM/LOW depth and cadence
- **Auto-escalation** — what triggers escalation

You can choose **Y) Save**, **n) Cancel**, or **e) Edit** (restart wizard) before writing the config.

---

## Weight calculation summary

Base weights (default): D1=1.0, D2=1.0, D3=1.0, D4=1.0, D5=1.0, D6=1.5, D7=1.0, D8=1.5

Modifiers are additive and stacked across all applicable answers. Weights are clamped between 0.5 and 3.0.

Example — EU healthcare company processing PHI with strict risk approach:

| Dim | Base | EU locs | PHI | Final |
|-----|------|---------|-----|-------|
| D1 | 1.0 | — | +0.5 | 1.5 |
| D3 | 1.0 | +0.5 | +0.5 | 2.0 |
| D4 | 1.0 | +1.0 + 0.5 | — | 2.5 |
| D5 | 1.0 | — | +1.0 | 2.0 |
| D8 | 1.5 | +0.5 | +0.5 | 2.5 |

---

## Config format

`bandit.config.yml` uses a structured format. Power users can edit it directly.

```yaml
company:
  org_type: "Healthcare / Pharma"
  locations:
    - "United States"
    - "European Union / EEA"
  infra_location: "both"
  baa_required: "Yes — required for all PHI-handling vendors"

data_types:
  phi: true
  pci: false
  children: false
  biometric: false
  hr_data: false
  special_categories: false

frameworks:
  inferred:
    - GDPR
    - CCPA/CPRA
    - HIPAA
  certifications_required:
    - HIPAA BAA
    - GDPR DPA / Article 28 agreement

risk_appetite: strict

reassessment:
  high:
    depth: full
    days: 180
    triggers:
      - policy_change
      - breach_reported
      - regulatory_change
  medium:
    depth: full
    days: 365
    triggers:
      - policy_change
      - breach_reported
  low:
    depth: scan
    days: 730
    triggers:
      - breach_reported

document_requirements:
  - HIPAA BAA
  - GDPR DPA / Article 28 agreement

dimension_weights:
  D1: 1.5
  D2: 1.0
  D3: 2.0
  D4: 2.5
  D5: 2.0
  D6: 1.5
  D7: 1.0
  D8: 2.5

auto_escalate:
  - type: tier
    tier: HIGH
    label: "Vendor risk tier is HIGH — requires security review"
  - type: tier
    tier: MEDIUM
    label: "Vendor risk tier is MEDIUM — requires conditional approval"
  - type: red_flag
    flag_label: AI training
    label: "AI training on customer PHI data detected — HIPAA violation risk"
```

Valid values:

| Key | Valid values |
|-----|-------------|
| `company.org_type` | Any of the 9 org type options |
| `company.infra_location` | `eu_only`, `us_only`, `both`, `other` |
| `risk_appetite` | `strict`, `standard`, `pragmatic` |
| `reassessment[tier].depth` | `full`, `lightweight`, `scan`, `none` |
| `reassessment[tier].days` | Any positive integer, or `0` for one-time |
| `reassessment[tier].triggers` | `policy_change`, `breach_reported`, `regulatory_change`, `contract_renewal` |
| `auto_escalate[].type` | `tier`, `score_below`, `red_flag`, `weighted_average_below` |

---

## Advanced configuration

`bandit setup --advanced` is coming soon. It will allow direct per-dimension weight editing, custom cadence values, and team routing configuration without re-running the full wizard.

For now, power users can edit `bandit.config.yml` directly — it takes effect immediately on the next `bandit assess` run.

---

## Google Drive integration (bandit setup --drive)

Run this after completing the main setup wizard if you want to use Google Drive for document storage.

```bash
bandit setup --drive
```

This walks you through:
1. Pointing Bandit to your Google credentials file
2. Authenticating with Google (browser opens once)
3. Configuring your Drive root folder ID

Full instructions: [docs/google-drive-setup.md](google-drive-setup.md)

After Drive is configured, every `bandit assess --drive` and `bandit batch --drive` command automatically discovers and reads documents from Drive.

---

## What setup configures

After completing `bandit setup`, your `bandit.config.yml` contains everything Bandit needs to run context-aware assessments:

**Organisation profile:**
- Industry, locations, data types → dimension weights
- Frameworks → what regulations to cite in reports
- Certifications → what documents to expect per vendor

**Risk appetite:**
- Approach (Strict/Standard/Pragmatic) → cadence defaults
- Auto-escalation triggers → when to flag regardless of score

**Reassessment schedule:**
- Per risk tier — depth and frequency
- HIGH vendors assessed more often and more thoroughly
- LOW vendors scanned or skipped based on your approach

**Document expectations:**
Based on industry and data types, Bandit knows what documents to expect per vendor and flags missing required documents in every report.

---

## Tech stack setup (bandit setup --stack)

Collect your internal tools by category. These names appear as options in Q6 of the vendor intake wizard.

```bash
bandit setup --stack
```

You'll be walked through tool categories:

| Category | Examples |
|----------|---------|
| Identity / SSO | Okta, Google Workspace, Azure AD |
| CRM | Salesforce, HubSpot |
| Data warehouse | Snowflake, BigQuery, Databricks |
| HRIS | Workday, BambooHR, Rippling |
| Finance / ERP | NetSuite, QuickBooks, SAP |
| Ticketing / DevOps | Jira, GitHub, PagerDuty |
| Communication | Slack, Teams, Zoom |
| Security | CrowdStrike, Wiz, SentinelOne |

The selected tools are saved to `bandit.config.yml` under `tech_stack:`. Run `--stack` again at any time to update.

---

## IT notification setup (bandit setup --notify)

Configure who receives vendor integration notifications and how. Notifications are queued during `bandit vendor add` and will be sent automatically in v1.4.

```bash
bandit setup --notify
```

You'll be asked:
1. IT contact name
2. IT contact email
3. Delivery method (currently: email / queue only)

The contact is saved to `bandit.config.yml` under `it_contact:`. Queued notifications are stored in each vendor's profile as `pending_it_notification` and include per-integration action items (provision SSO, create service accounts, set field-level permissions, etc.).
