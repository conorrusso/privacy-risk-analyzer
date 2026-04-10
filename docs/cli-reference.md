# Bandit CLI Reference

## Quick reference

| Command | What it does |
|---------|-------------|
| `bandit assess "Vendor"` | Assess a single vendor's privacy practices |
| `bandit vendor add "Vendor"` | Run 12-question intake wizard for a new vendor |
| `bandit vendor show "Vendor"` | View vendor profile and assessment history |
| `bandit vendor edit "Vendor"` | Update intake answers |
| `bandit vendor list` | List all vendors with risk tier and next due date |
| `bandit vendor list --due` | Vendors due for reassessment only |
| `bandit legal "Vendor"` | Standalone contract gap analysis (DPA/MSA) |
| `bandit setup` | Run the setup wizard (~2 min, infers frameworks automatically) |
| `bandit setup --stack` | Collect your internal tools by category |
| `bandit setup --notify` | Configure IT notification contact |
| `bandit setup --show` | Print your current profile |
| `bandit setup --reset` | Start the wizard over |
| `bandit profile "Vendor"` | Show vendor function profile and doc requirements |
| `bandit profile --show` | List all cached vendor profiles |
| `bandit batch vendors.txt` | Assess a list of vendors from a file |
| `bandit rubric` | Show the full scoring rubric |
| `bandit rubric --dim D6` | Show detail for one dimension |
| `bandit sync` | Full Drive sync — discovers new folders, detects deletions, pulls documents |
| `bandit sync "Vendor"` | Sync a single vendor |
| `bandit sync --verbose` | Show document names found |
| `bandit dashboard` | Portfolio risk overview |
| `bandit schedule` | Reassessment schedule |
| `bandit schedule --due` | Overdue vendors only |
| `bandit register` | Export TPRM register (CSV) |
| `bandit register --format html` | HTML register |
| `bandit notify --all` | Send all pending IT notifications |

---

## Installation

### Prerequisites

- Python 3.9+
- An API key for your chosen provider (or [Ollama](https://ollama.com) for local inference)

### Steps

```bash
git clone https://github.com/conorrusso/bandit.git
cd bandit
pip install -e .
```

Set your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or add to config.env in the repo root:
# ANTHROPIC_API_KEY=sk-ant-...
```

Verify the install:

```bash
bandit
```

---

## Commands

### `bandit assess`

Run a full privacy risk assessment for one vendor.

```
bandit assess <vendor> [OPTIONS]
```

**Arguments**

| Argument | Description |
|----------|-------------|
| `<vendor>` | Vendor name, domain, or URL (see Input formats below) |

**Options**

| Option | Default | Description |
|--------|---------|-------------|
| `--model MODEL` | `claude-haiku-4-5-20251001` | LLM model ID |
| `--api-key KEY` | `$ANTHROPIC_API_KEY` | API key for your provider |
| `--json` | off | Print raw JSON to stdout (report still saved) |
| `-v`, `--verbose` | off | Show discovery stages, fetched pages, and signal detail |
| `--no-report` | off | Skip saving the HTML report |
| `--force` | off | Run assessment even if cadence says vendor is not due yet |
| `--docs PATH` | — | Folder containing vendor documents (DPA, MSA, SOC 2, etc.) |
| `--drive` | off | Fetch vendor documents from configured Google Drive folder |

**Examples**

```bash
bandit assess "Salesforce"
bandit assess hubspot.com --verbose
bandit assess https://anecdotes.ai/privacy
bandit assess "Acme Corp" --json > acme.json
bandit assess "Acme Corp" --model claude-opus-4-6
bandit assess "Acme Corp" --no-report
bandit assess "Acme Corp" --docs ./vendor-docs/acme/
bandit assess "Acme Corp" --drive
```

---

### `bandit setup`

Run the interactive setup wizard. 5 core questions + up to 3 conditional. Automatically infers applicable frameworks (GDPR, HIPAA, CCPA, etc.) and calculates dimension weights. Saves to `./bandit.config.yml`.

```
bandit setup [OPTIONS]
```

**Options**

| Option | Description |
|--------|-------------|
| `--show` | Print current config summary and exit |
| `--reset` | Remove existing config and start the wizard fresh |
| `--drive` | Configure Google Drive integration — accepts folder URL or bare ID in Step 3 |
| `--stack` | Collect your internal tools by category (used in vendor intake Q6) |
| `--notify` | Configure IT notification contact and method |
| `--advanced` | Advanced configuration (coming soon) |

**Examples**

```bash
bandit setup              # Run wizard (~2 minutes)
bandit setup --stack      # Configure internal tech stack
bandit setup --notify     # Set IT contact for vendor notifications
bandit setup --show       # Print current profile
bandit setup --reset      # Start over
bandit setup --drive      # Configure Google Drive integration
bandit setup --advanced   # Advanced mode (coming soon)
```

The wizard asks:
1. **Organisation type** — industry-specific defaults
2. **Locations** — where you and your customers operate (biggest weight driver)
3. **Sensitive data types** — PHI, PCI, children's, biometric, HR, special categories
4. **Required certifications** — SOC 2, HIPAA BAA, GDPR DPA, PCI AOC, etc.
5. **Risk approach** — Strict / Standard / Pragmatic (sets cadence and escalation thresholds)

Plus conditional questions about infrastructure location, BAA requirements, and PCI merchant level when relevant.

After the questions, Bandit shows an inferred profile for review (Y/n/edit) then writes `bandit.config.yml`.

See [docs/setup-guide.md](setup-guide.md) for a question-by-question walkthrough.

---

### `bandit profile`

Show or manage vendor function profiles. Auto-detects what category a vendor belongs to from a library of 330+ known vendors.

```
bandit profile [VENDOR] [OPTIONS]
```

**Arguments**

| Argument | Description |
|----------|-------------|
| `[VENDOR]` | Vendor name, domain, or partial name (optional) |

**Options**

| Option | Description |
|--------|-------------|
| `--show` | List all cached vendor profiles |
| `--unknown` | Show vendors with unknown function classification |

**Examples**

```bash
bandit profile "Salesforce"   # Detect and show function profile
bandit profile stripe.com     # Detect from domain
bandit profile --show         # List all cached profiles
bandit profile --unknown      # Find vendors that need manual classification
```

Bandit detects vendor functions through a 4-stage pipeline:
1. Known vendor library (~330 vendors)
2. Domain segment match
3. Keyword inference from the vendor name
4. Unknown → GENERAL_SAAS fallback

Profiles are cached in `~/.bandit/vendor-profiles.json` and reused across assessments.

---

### `bandit vendor`

Manage vendor profiles, intake data, and assessment history.

```
bandit vendor add <vendor>
bandit vendor show <vendor>
bandit vendor edit <vendor>
bandit vendor list [OPTIONS]
```

**Subcommands**

| Subcommand | Description |
|-----------|-------------|
| `add <vendor>` | Run 12-question intake wizard. Checks Drive for existing folder first. Queues IT actions. |
| `show <vendor>` | Display full profile and last 5 assessment history entries |
| `edit <vendor>` | Re-run intake wizard with current values as defaults |
| `list` | Table of all vendors with risk tier, score, dates, and intake status |

**list options**

| Option | Description |
|--------|-------------|
| `--due` | Show only vendors where next due date has passed |
| `--risk TIER` | Filter by risk tier: HIGH, MEDIUM, or LOW |

**Examples**

```bash
bandit vendor add "HubSpot"
bandit vendor show "HubSpot"
bandit vendor edit "HubSpot"
bandit vendor list
bandit vendor list --due
bandit vendor list --risk HIGH
```

See [docs/vendor-guide.md](vendor-guide.md) for a full walkthrough.

---

### `bandit legal`

Run a standalone Legal Bandit contract gap analysis against a vendor's DPA or MSA. Produces a legal redline brief HTML report.

```
bandit legal <vendor> [OPTIONS]
```

**Options**

| Option | Default | Description |
|--------|---------|-------------|
| `--docs PATH` | — | Folder containing DPA/MSA documents |
| `--drive` | off | Fetch documents from Google Drive |
| `--no-legal-brief` | off | Skip saving the HTML legal redline brief |
| `--model MODEL` | `claude-haiku-4-5-20251001` | LLM model ID |

**Examples**

```bash
bandit legal "Salesforce" --docs ./vendor-docs/salesforce/
bandit legal "Salesforce" --drive
bandit legal "Salesforce" --docs ./docs/ --no-legal-brief
```

Legal Bandit checks:
- GDPR Art. 28(3)(a)–(h) provisions against the DPA
- Vague language detection ("appropriate measures", "commercially reasonable efforts")
- Policy/contract conflicts
- SCC version and completeness (flags pre-2021 SCCs)
- MSA commercial data protection terms

Score changes from contract analysis are shown in the terminal: `D5 1→4 ↑ Contract`.

---

### `bandit batch`

Assess a list of vendors from a text file.

```
bandit batch <file> [OPTIONS]
```

**Arguments**

| Argument | Description |
|----------|-------------|
| `<file>` | Path to a text file with one vendor per line |

**Options**

| Option | Default | Description |
|--------|---------|-------------|
| `--model MODEL` | `claude-haiku-4-5-20251001` | LLM model ID |
| `--api-key KEY` | `$ANTHROPIC_API_KEY` | API key for your provider |
| `--out-dir DIR` | `reports` | Directory to save HTML reports |
| `--docs-root PATH` | — | Root folder with vendor subfolders (`./docs-root/<vendor-name>/`) |
| `--drive` | off | Fetch documents from Google Drive for each vendor |

**Examples**

```bash
bandit batch vendors.txt
bandit batch vendors.txt --out-dir ./output
bandit batch vendors.txt --docs-root ./vendor-docs/
bandit batch vendors.txt --drive
```

---

### `bandit rubric`

Show the scoring rubric.

```
bandit rubric [OPTIONS]
```

**Options**

| Option | Description |
|--------|-------------|
| `--dim DIM` | Show detail for one dimension, e.g. `--dim D5` |

**Examples**

```bash
bandit rubric
bandit rubric --dim D6
```

---

## Input formats

`bandit assess` and `bandit batch` accept three formats. Detection is automatic — no flags needed.

### Company name

```
bandit assess "Salesforce"
bandit assess "Anecdotes AI"
```

Full discovery pipeline: DDG search → domain probe → AI reasoning → homepage scrape.

### Bare domain

Contains a dot, no spaces. Skips domain resolution. Probes common privacy paths on the domain directly.

```
bandit assess hubspot.com
bandit assess anecdotes.ai
```

### Full URL

Starts with `https://`. Skips all discovery and fetches the URL directly. Use this if discovery finds the wrong page.

```
bandit assess https://anecdotes.ai/privacy
bandit assess https://legal.hubspot.com/privacy-policy
```

---

## All flags at a glance

| Flag | Command | Description |
|------|---------|-------------|
| `-v`, `--verbose` | `assess` | Show discovery stages and signal detail live |
| `--json` | `assess` | Output raw JSON to terminal |
| `--no-report` | `assess` | Skip saving the HTML report |
| `--force` | `assess` | Run even if cadence says vendor is not due |
| `--docs PATH` | `assess` | Folder containing vendor documents |
| `--drive` | `assess`, `batch` | Fetch documents from Google Drive |
| `--model MODEL` | `assess`, `batch` | Override the LLM model |
| `--api-key KEY` | `assess`, `batch` | Provide API key directly |
| `--out-dir DIR` | `batch` | Output directory for HTML reports |
| `--docs-root PATH` | `batch` | Root folder with vendor subfolders |
| `--show` | `setup` | Print current config and exit |
| `--reset` | `setup` | Remove existing config and restart wizard |
| `--drive` | `setup` | Configure Google Drive integration (saves progress, resumes on restart) |
| `--dim D1–D8` | `rubric` | Show detail for one dimension |

---

## Environment variables

| Variable | Provider | Required |
|----------|----------|---------|
| `ANTHROPIC_API_KEY` | Claude | Yes (if using Claude) |
| `OPENAI_API_KEY` | GPT-4o | Yes (if using OpenAI) |
| `GOOGLE_API_KEY` | Gemini | Yes (if using Gemini) |
| `MISTRAL_API_KEY` | Mistral | Yes (if using Mistral) |
| *(none)* | Ollama | No — fully local |

Variables can also be set in `config.env` at the repo root. They are loaded automatically on startup and do not override existing environment variables.

---

## Exit behaviour

| Code | Meaning |
|------|---------|
| 0 | Success (including graceful Ctrl+C cancel) |
| 1 | Error (API key missing, fetch failure, etc.) |

**Ctrl+C during assessment:**

- Single vendor: prints `Assessment cancelled` cleanly, exits 0
- Batch: prints `Batch cancelled after N/M vendors`, lists completed reports and remaining vendors, exits 0

---

## vendors.txt format

One vendor per line. Supports up to four columns separated by commas.

| Column | Field | Required |
|--------|-------|---------|
| 1 | Vendor name or domain | Yes |
| 2 | Policy URL (skips URL discovery) | No |
| 3 | Vendor functions (comma-separated) | No |
| 4 | Local docs path | No |

**Examples:**

```
# Simplest — just vendor names
Salesforce
HubSpot
Notion

# With direct URL (skips discovery)
Anecdotes, https://anecdotes.ai/privacy

# With vendor function profiling
NetSuite,,financial_processing,hr_people

# With local docs folder
Salesforce,,,./vendor-docs/salesforce/

# All columns
Salesforce,https://salesforce.com/privacy,customer_data,./docs/sf/

# Comments and blank lines ignored
# Healthcare vendors
Epic,,healthcare_clinical
Cerner,,healthcare_clinical
```

The `docs_path` column (4th) overrides `--docs-root` for that specific vendor.

---

## Document folder structure

Create a root folder with one subfolder per vendor. Bandit auto-detects document types — any filename works.

```
vendor-docs/
├── Salesforce/
│   ├── dpa.pdf                  ← DPA (auto-detected)
│   ├── msa.pdf                  ← MSA (auto-detected)
│   └── soc2-2025.pdf            ← SOC 2 Type II (auto-detected)
├── HubSpot/
│   ├── hubspot-dpa.docx
│   └── sub-processors.html
└── Stripe/
    └── privacy-policy.pdf
```

Run with the root folder for batch assessments:

```bash
bandit batch vendors.txt --docs-root ./vendor-docs/
```

Bandit matches vendor names to subfolders automatically (case-insensitive, partial match fallback). Vendors without a matching subfolder are assessed from public policy only.

---

## Output files

HTML reports are saved to `./reports/` by default, named `<vendor-slug>-<date>.html`.

Examples:
- `reports/salesforce-2026-03-29.html`
- `reports/hubspot-com-2026-03-29.html`
- `reports/anecdotes-ai-2026-03-29.html`

---

## Cache and config files

| Path | Contents |
|------|----------|
| `./bandit.config.yml` | Setup wizard output — industry and regulatory profile |
| `~/.bandit/bandit.config.yml` | Fallback config location (searched if `./bandit.config.yml` not found) |
| `~/.bandit/vendor-profiles.json` | All vendor profiles, intake data, and assessment history |
| `~/.bandit/domain-cache.json` | Discovered domain → privacy URL mappings (30-day TTL) |
| `~/.bandit/vendor-history.json` | Legacy assessment history (superseded by vendor-profiles.json) |
| `~/.bandit/manual-review.json` | Vendors where discovery failed, for follow-up |
| `~/.bandit/.setup_progress.json` | In-progress setup wizard state (deleted on completion) |
| `~/.bandit/.intake_progress.json` | In-progress intake wizard state (deleted on completion) |
| `~/.bandit/google-token.json` | Google OAuth token for Drive integration |

---

## Supported document types

Bandit auto-detects these document types:

**Privacy & Data Protection**
- Privacy Policy · Cookie Policy · CCPA Notice · Children's Privacy Policy

**Contracts**
- DPA (Data Processing Agreement)
- MSA (Master Services Agreement)
- BAA (Business Associate Agreement — HIPAA)
- SaaS Agreement · NDA
- Data Sharing Agreement
- Joint Controller Agreement (GDPR Art. 26)
- Standard Contractual Clauses (SCCs)
- Order Form

**Audit & Certification**
- SOC 2 Type II · SOC 2 Type I · SOC 1 Type II
- ISO 27001 · ISO 27701 · ISO 42001
- HITRUST · PCI AOC · PCI ROC
- FedRAMP ATO · NIST 800-171 · CMMC
- NYDFS Part 500 · DORA Compliance

**AI-Specific**
- AI Policy · Model Card · AI System Card
- EU AI Act Conformity Documentation
- Algorithm Impact Assessment

**Transfer & International**
- Transfer Impact Assessment (TIA)
- Record of Processing Activities (ROPA entry)

**Security**
- Penetration Test Summary
- Vulnerability Disclosure Policy
- Incident Response Policy
- Sub-processor List
- Security Policy
- Data Retention Schedule

**Healthcare Specific**
- HIPAA Security Addendum

**Financial Specific**
- GLBA Privacy Notice · PCI SAQ

**Supported file formats:**
PDF (`.pdf`) · Word (`.docx` `.doc`) · HTML (`.html` `.htm`) · Text (`.txt` `.md`) · JSON (`.json`)

---

## bandit sync

Sync vendor profiles and documents from Google Drive. Runs in four steps automatically — no flags required:

1. **Discover** — scans your Bandit root folder in Drive and links any subfolders that match local vendor profiles (case-insensitive name match)
2. **Detect deletions** — checks all linked profiles; if a Drive folder has been moved or deleted, clears the link so it can be rediscovered later
3. **Pull documents** — downloads the latest docs for every vendor with a linked folder
4. **Report** — shows a summary and flags any Drive folders with no matching local profile

```
bandit sync [VENDOR_NAME] [OPTIONS]
```

**Options**

| Option | Description |
|--------|-------------|
| `--verbose`, `-v` | Show each document name found |
| `--json` | Output structured JSON |

```bash
bandit sync                   # all vendors — discover, link, sync
bandit sync "Cyera"           # one vendor only
bandit sync --verbose         # show each document found
bandit sync --json            # structured JSON output
```

Unmatched Drive folders (no local profile) are shown at the end:

```
✓  Cyera        linked — 3 docs
·  Salesforce   already linked — 5 docs
?  Snowflake    no local profile — run: bandit vendor add "Snowflake"
```

Sync runs automatically at the start and end of every `bandit assess --drive` run. Use `bandit sync` standalone when you want to refresh profiles or check document counts without running a full assessment.

---

## bandit dashboard

Portfolio risk overview across all vendors.

```bash
bandit dashboard                    # full portfolio table
bandit dashboard --risk HIGH        # filter by tier
bandit dashboard --due              # vendors due for reassessment
bandit dashboard --json             # structured JSON
```

---

## bandit schedule

Reassessment schedule sorted by urgency.

```bash
bandit schedule                     # all vendors
bandit schedule --due               # overdue + due soon only
bandit schedule --within 30         # due within 30 days
bandit schedule --json
```

Urgency levels: `OVERDUE` · `DUE SOON` (≤30 days) · `UPCOMING` (≤90 days) · `OK`

---

## bandit register

Export the full TPRM vendor register.

```bash
bandit register                     # CSV to stdout
bandit register --format json       # JSON to stdout
bandit register --format html       # saves HTML file
bandit register --out report.csv    # save to path
```

---

## bandit notify

Send queued IT notifications for vendor integrations.

```bash
bandit notify "Cyera"               # single vendor
bandit notify --all                 # all pending
bandit notify --all --json
```

Requires `bandit setup --notify` to configure Slack webhook or email address.
