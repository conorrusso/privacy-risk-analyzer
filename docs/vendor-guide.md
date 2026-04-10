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

## bandit vendor add

Runs the 12-question intake wizard. Takes about 3 minutes.

```bash
bandit vendor add "HubSpot"
```

If Google Drive is configured, Bandit checks for an existing vendor folder before the wizard starts. You can link to an existing folder, create a new one, or skip Drive entirely.

### The 12 questions

| # | Question | Why it matters |
|---|----------|----------------|
| Q1 | Data types processed | Adjusts D1, D2, D7 weights; flags if inconsistent with access level |
| Q2 | Volume of records | Calibrates breach impact scoring |
| Q3 | Environment access | Whether vendor touches production, staging, or nothing |
| Q4 | Access level | Read-only vs admin triggers D2 weight increase |
| Q5 | Sole source? | Flags vendor as critical / difficult to replace |
| Q6 | Internal integrations | Which of your tools the vendor connects to (uses your tech stack) |
| Q7 | SSO required? | Whether vendor is enrolled in your IdP |
| Q8 | AI in the service? | Vendor uses AI in service delivery |
| Q9 | AI trains on your data? | Whether your data improves vendor models |
| Q10 | Criticality | Business criticality rating |
| Q11 | Annual spend | Contract value |
| Q12 | Renewal date | Next contract date |

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
| `personal_data` or `sensitive_data` in data types | D1 +0.2 |
| `financial_data` in data types | D2 +0.1 |
| `health_data` in data types | D5 +0.3, D8 +0.2 |
| Admin environment access | D2 +0.3 |
| AI trains on your data | D6 +0.3 |
| Any integration present | D2 +0.15 |

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

If you already have vendor folders in Drive before running `bandit vendor add`, link them with:

```bash
bandit sync --discover
```

Bandit scans the root folder and links matches automatically. You will see:

```
✓  Cyera      linked to Cyera
?  Snowflake  no local profile — run: bandit vendor add "Snowflake"
```

### Adding a vendor with an existing Drive folder

If a Drive folder already exists for the vendor, `bandit vendor add` will find it automatically during intake — exact match uses it silently, close match asks for confirmation.

### Sync sequence

```bash
bandit sync --discover   # link existing folders
bandit sync              # pull latest docs + profiles
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
