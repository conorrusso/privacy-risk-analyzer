# Vendor Guide

How to add, assess, and manage vendors in Bandit.

---

## Overview

Bandit's vendor management layer sits on top of the assessment engine. Before running an assessment, you can capture structured intake data about a vendor — what data they touch, how they're integrated, and what your contractual obligations are. This data:

- **Adjusts assessment weights** — a vendor with admin access to your infrastructure gets higher D2 and D5 weights
- **Injects integration context** into LLM extraction prompts
- **Feeds the IT notification queue** when new vendor integrations require provisioning
- **Persists assessment history** so you can track risk over time

---

## Quick start

```bash
# 1. Add a vendor profile (optional but recommended)
bandit vendor add "Salesforce"

# 2. Run the assessment
bandit assess "Salesforce" --drive

# 3. View results and history
bandit vendor show "Salesforce"
```

---

## Batch onboarding with bandit workflow

When you have multiple vendors to onboard at once:

```bash
bandit sync              # auto-creates profiles
bandit workflow --drive  # intake + assess all
```

For a single new vendor during procurement:

```bash
bandit vendor add "VendorName"
bandit workflow --vendor "VendorName" --drive
```

The workflow:
1. Shows all vendors missing intake data
2. Asks if you want to proceed
3. Walks through 12 questions per vendor
4. Lets you skip any vendor
5. Offers to assess all completed vendors at once
6. Shows risk tiers and saves reports to Drive

The Legal Bandit redline brief is generated automatically when Drive documents include a DPA or MSA. Use it as a negotiating tool before signing.

---

## bandit vendor add

Runs the 12-question intake wizard. Takes about 3 minutes.

```bash
bandit vendor add "HubSpot"
```

If Google Drive is configured, Bandit checks for an existing vendor folder before the wizard starts. You can link to an existing folder, create a new one, or skip Drive entirely.

### The 12 questions

| # | Question | Why it matters |
|---|----------|----------------|
| Q1 | Data exposure | What data the vendor comes into contact with — adjusts D1, D3, D5, D7, D8 weights |
| Q2 | Volume of records | Calibrates breach impact scoring |
| Q3 | Environment access | Whether vendor touches production, staging, or nothing |
| Q4 | Blast radius | Worst-case impact if vendor access is compromised — shapes D2, D5, D7, D8 weights |
| Q5 | Replaceability | How easily the vendor can be replaced — affects negotiating leverage and escalation |
| Q6 | Internal integrations | Which of your tools the vendor connects to (uses your tech stack) |
| Q7 | SSO required? | Whether vendor is enrolled in your IdP |
| Q8 | AI in the service? | Vendor uses AI in service delivery |
| Q9 | AI trains on your data? | Whether your data improves vendor models |
| Q10 | Criticality | Business criticality rating |
| Q11 | Annual spend | Contract value |
| Q12 | Renewal date | Next contract date |

### Q1 — Data exposure

What data will this vendor come into contact with?
This covers data they store, transmit, process, or can access.

Categories:
- **Public data** — no restrictions
- **Internal / operational data** — internal use, not sensitive (logs, configs, infrastructure)
- **Confidential business data** — financials, strategy, IP, source code
- **Customer or user data** — any data about your customers or users
- **Employee or HR data** — personnel, payroll, HR
- **Regulated — health data (PHI / HIPAA)**
- **Regulated — payment data (PCI)**
- **No personal or confidential data** — infrastructure / tooling only

Why this matters: Q1 directly shapes the dimension weights for this vendor's assessment. PHI and PCI increase D5 and D7 weights significantly. Customer data increases D1 and D3 weights. Selecting "none" reduces GDPR-specific weights for infrastructure tools that don't touch personal data.

### Q4 — Blast radius

If this vendor's access was compromised, what is the worst-case impact?

Options (pick the highest risk that applies):

- **Minimal** — view-only or sandbox access, limited scope. Low blast radius.

- **Data exposure** — could read or export sensitive, personal, or confidential production data.
  (Example: read-only Snowflake connection to customer analytics data)

- **Data or config change** — could modify, delete, or corrupt data or application configuration.
  (Example: CRM write access, Jira admin)

- **Infrastructure or identity risk** — network position, identity provider, secrets manager,
  or infrastructure admin. Compromise affects systems beyond this vendor.
  (Example: Cloudflare, Okta, AWS, Vault)

Why this matters: Q4 directly shapes breach notification (D5) and sub-processor (D2) weights.
"Systemic" access adds significant weight to D5, D2, and D8 because a breach at a network or
identity vendor has cascading effects that require contractual protections beyond a standard SaaS DPA.

Tip: if a vendor has multiple access levels (e.g. read-only to data but agent running on servers),
pick the highest risk scenario.

### Q5 — Replaceability

How easily could you replace this vendor if needed?

- **Easily replaceable** — alternatives exist, low switching cost
- **Difficult to replace** — alternatives exist but migration effort is significant
- **Not replaceable** — no viable alternative, business-critical dependency

Why this matters: replaceability determines your negotiating leverage. A vendor with a 2/5 D5
score is a different risk conversation if you can walk away vs if they're the only option.

When a vendor is HIGH risk AND not replaceable, Bandit flags this in the GRC report — it means
contract gaps are harder to close and risk acceptance requires explicit sign-off.

This doesn't affect scoring directly but affects the escalation and risk acceptance recommendations
in the GRC report. Not-replaceable vendors also show a `(locked in)` indicator in the dashboard.

### After the wizard

A summary is shown. The profile is saved to `~/.bandit/vendor-profiles.json`. If Drive is configured, the profiles file is synced to your Drive root folder.

If the vendor has integrations, IT action items are queued in the profile and shown in the summary. Sending is configured with `bandit setup --notify` and enabled in v1.4.

---

## bandit vendor show

```bash
bandit vendor show "HubSpot"
```

Shows:
- Intake completion status and date
- All intake answers
- Assessment history (last 10 entries) with risk tier, score, and next due date

---

## bandit vendor edit

Re-runs the intake wizard with current values as defaults. Press Enter to keep any existing answer.

```bash
bandit vendor edit "HubSpot"
```

---

## bandit vendor list

```bash
bandit vendor list                    # All vendors
bandit vendor list --due              # Only vendors due for reassessment
bandit vendor list --risk HIGH        # Filter by risk tier
bandit vendor list --risk MEDIUM
bandit vendor list --risk LOW
```

Columns: Vendor · Risk tier · Score · Last assessed · Next due · Intake status

Overdue vendors show a red warning in the Next due column.

---

## How intake affects assessments

When you run `bandit assess` for a vendor that has a completed intake profile, Bandit:

1. **Loads the profile** at the start of the assessment
2. **Injects integration context** into the LLM extraction prompt — e.g. *"This vendor is integrated with Salesforce CRM and Snowflake data warehouse."*
3. **Applies weight modifiers** based on intake data:

| Intake signal | Effect |
|---------------|--------|
| `customer_data` in Q1 | D1 +0.4, D3 +0.4, D5 +0.2, D7 +0.2 |
| `employee_data` in Q1 | D1 +0.4, D3 +0.3, D5 +0.2, D7 +0.2 |
| `confidential_business` in Q1 | D1 +0.4, D6 +0.3, D7 +0.2 |
| `phi` in Q1 | D1 +0.5, D5 +1.0, D7 +0.3, D8 +0.5 |
| `pci` in Q1 | D1 +0.3, D7 +0.5, D8 +0.3 |
| `none` in Q1 | D1 −0.2, D3 −0.3 |
| `data_exposure` access (Q4) | D1 +0.3, D3 +0.2 |
| `data_change` access (Q4) | D2 +0.4, D5 +0.4, D7 +0.3 |
| `systemic` access (Q4) | D2 +0.6, D5 +0.8, D7 +0.3, D8 +0.4 |
| `minimal` access (Q4) | D5 −0.1 |
| Customer data integration | D1 +0.3, D3 +0.3 |
| Healthcare integration | D1 +0.5, D5 +1.0, D8 +0.5 |

Weight modifiers are additive. The org profile weight is applied first, and intake modifiers only apply where the org profile hasn't already maximised a weight (prevents double-counting).

4. **Writes the result to assessment history** in the vendor profile — date, risk tier, score, scope, report path, next due date
5. **Syncs the updated profile to Drive** (if configured)

---

## Assessment history

Every `bandit assess` run writes an entry to the vendor profile. The last 10 entries are retained.

```bash
bandit vendor show "Salesforce"
# Shows:
# 2026-04-01  HIGH  2.1/5.0  next due: 2026-10-01
# 2026-01-15  MEDIUM  2.8/5.0  next due: 2026-07-15
```

Next due dates are calculated from your reassessment config (`bandit setup` → risk approach):

| Risk tier | Default cadence |
|-----------|----------------|
| HIGH | Every 6 months |
| MEDIUM | Every year |
| LOW | Every 2 years |

These defaults can be customised per tier in `bandit.config.yml`. Run `bandit setup --show` to see your active cadence.

### How next due date is calculated

When `bandit assess` completes, it writes the next due date into the vendor profile:

```
next_due = assessment_date + cadence_days[risk_tier]
```

For example: a HIGH-risk vendor assessed on 2026-04-01 with a 6-month cadence gets `next_due = 2026-10-01`.

If the vendor's risk tier changes between assessments (e.g. MEDIUM → HIGH), the next due date is recalculated from the new tier's cadence at the time the new assessment is written.

### bandit vendor list --due

The `--due` flag filters to vendors where `next_due <= today`. Vendors that have never been assessed are always included (no assessment means always due).

```bash
bandit vendor list --due
```

Overdue vendors show a red warning in the Next due column. Use this as your weekly triage view — assess overdue vendors first.

---

## Google Drive workflow

### Linking existing Drive folders

If you already have vendor folders in Drive before running `bandit vendor add`, run:

```bash
bandit sync
```

`bandit sync` automatically discovers and links Drive folders to matching vendor profiles. You will see:

```
✓  Cyera      linked to Cyera
?  Snowflake  no local profile — run: bandit vendor add "Snowflake"
```

### Adding a vendor with an existing Drive folder

If a Drive folder already exists for the vendor, `bandit vendor add` will find it automatically during intake — exact match uses it silently, close match asks for confirmation.

### Sync sequence

```bash
bandit setup --drive     # configure credentials (once)
bandit sync              # discover, link, and pull docs
bandit dashboard         # view updated portfolio
```

---

## Google Drive profile sync

Vendor profiles are stored locally at `~/.bandit/vendor-profiles.json`. When Drive is configured, Bandit also syncs a copy to `.vendor-profiles.json` in your Drive root folder.

Sync happens:
- After `bandit vendor add` completes
- After `bandit assess` completes (writes history entry, then syncs)
- Sync failures are silent — local cache is always the source of truth

To configure Drive:
```bash
bandit setup --drive
```

---

## Tech stack integration

Q6 of the intake wizard asks which of your internal tools the vendor integrates with. The options shown are pulled from your tech stack config.

To set up your tech stack:
```bash
bandit setup --stack
```

This walks you through tool categories (Identity, CRM, Data warehouse, HR, etc.) and saves named tools to `bandit.config.yml`. These names appear as options in Q6 for every future vendor intake.

---

## IT notifications

When a vendor has integrations, Bandit generates IT action items per integration category:

| Category | Example actions |
|----------|----------------|
| Identity | Provision SSO, assign role, set MFA policy |
| CRM | Create Salesforce connected app, set field-level security |
| Data warehouse | Create Snowflake service account, restrict to schema |
| HRIS | Verify data sync scope, confirm no write access |

Actions are queued in the vendor profile as `pending_it_notification`. Sending is configured with `bandit setup --notify` and will be enabled in v1.4.

To configure the IT contact now:
```bash
bandit setup --notify
```
