# Bandit — Vendor Risk Intelligence Suite

> Open-source CLI for vendor privacy risk assessment. Free forever. Provider-agnostic.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Rubric: v1.0.0](https://img.shields.io/badge/Rubric-v1.0.0-brown)](core/scoring/RUBRIC.md)
[![Providers: Claude · GPT-4o · Gemini · Ollama](https://img.shields.io/badge/Providers-Claude%20%C2%B7%20GPT--4o%20%C2%B7%20Gemini%20%C2%B7%20Ollama-blue)](#providers)

---

## What Bandit does

Bandit is a Python CLI that assesses vendor privacy policies against a published, enforcement-grounded rubric. Point it at a company name, domain, or URL — it finds the policy, extracts evidence with an LLM, scores it deterministically across 8 dimensions, and saves an HTML report with findings for each team.

The AI extracts evidence. Bandit scores it. GPT-4o and Claude produce the same score from the same policy.

---

## Installation

```bash
git clone https://github.com/conorrusso/bandit.git
cd bandit
pip install -e .
```

Set your API key (or pass `--api-key`):

```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Quick start

```bash
# Step 1 — Configure your profile (recommended)
bandit setup

# Step 2 — Run your first assessment
bandit assess "Salesforce"
```

`bandit setup` takes about 2 minutes and adjusts dimension weights for your industry, regulatory context, and data risk profile. If you skip it, Bandit uses GDPR-focused defaults and shows a reminder after each run.

---

## Usage

```
bandit assess <vendor>         Run a full privacy risk assessment
bandit assess <vendor> -v      Verbose — see fetched pages and signals
bandit assess <vendor> --json  Output raw JSON
bandit batch <vendors.txt>     Assess a full vendor list
bandit rubric                  Show the scoring rubric summary
bandit rubric --dim D5         Show criteria for one dimension
bandit setup                   Configure your industry and regulatory profile
bandit setup --show            Show current profile
bandit setup --reset           Start setup over
```

### Input formats

`bandit assess` accepts three input formats:

| Format | Example | Behaviour |
|--------|---------|-----------|
| Company name | `"Salesforce"` | Full discovery: DDG search → domain probe → AI reasoning |
| Bare domain | `hubspot.com` | Skips domain resolution, probes privacy paths directly |
| Full URL | `https://acme.com/privacy` | Skips all discovery, fetches directly |

### Batch assessment

Create a text file with one vendor per line (names, domains, or URLs — any format):

```
Salesforce
hubspot.com
https://notion.so/privacy
# This line is ignored
Anecdotes AI
```

Run:

```bash
bandit batch vendors.txt
```

HTML reports are saved to `./reports/` after every run. The batch command prints a summary table when all vendors are done.

---

## Commands

### bandit assess

Run a full privacy risk assessment for one vendor.

```bash
bandit assess "Salesforce"                           # company name
bandit assess salesforce.com                         # domain
bandit assess https://salesforce.com/privacy         # full URL
bandit assess "Acme Corp" --verbose                  # show all stages
bandit assess "Acme Corp" --json > acme.json         # raw JSON output
bandit assess "Acme Corp" --no-report                # skip HTML report
bandit assess "Acme Corp" --model claude-opus-4-6    # override model
```

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Show discovery stages and signal extraction detail |
| `--json` | Print raw JSON to stdout (report still saved) |
| `--no-report` | Skip saving the HTML report |
| `--model MODEL` | Override the LLM model |
| `--api-key KEY` | Provide API key directly (default: env var) |

### bandit setup

Run the interactive setup wizard. Configures Bandit for your industry, regulatory frameworks, data types, and company location. Saves to `bandit.config.yml`.

```bash
bandit setup           # Run full wizard
bandit setup --show    # Show current config
bandit setup --reset   # Start over
```

The wizard asks about:
- Where your company operates and where customers are located
- Your industry
- Data types processed (PHI, PCI, children's data, special categories)
- Applicable regulatory frameworks (GDPR, HIPAA, CCPA, PCI-DSS, etc.)
- Risk appetite and escalation thresholds
- Team routing (DPO, Legal, Security)

Based on your answers, Bandit automatically adjusts:
- Dimension weights for your regulatory context
- Auto-escalation triggers
- Contract recommendations citing relevant frameworks
- Team routing in reports

If no config exists, Bandit uses default weights and shows a tip to run setup after each assessment.

### bandit batch

Assess a list of vendors from a text file. See [vendors.txt format](#batch-assessment) above.

### bandit rubric

Show the scoring rubric. Use `--dim D1` through `--dim D8` to see criteria for a specific dimension.

---

## The HTML report

Every `bandit assess` run saves an HTML report to `./reports/<vendor>-<date>.html`.

The report includes:

- **Score summary** — risk tier (LOW / MEDIUM / HIGH), weighted average, per-dimension scores
- **Assessment scope notice** — shows which document types were assessed. Currently: public privacy policy only. D8 (DPA Completeness) is marked "Requires DPA" and D2, D4, D5 are marked "Partially assessed" until a DPA is provided (v1.1 Google Drive integration)
- **Per-dimension detail** — evidence found (confirmed signals), gaps identified (missing signals), red flags triggered
- **Evidence confidence** — each dimension shows whether evidence is Confirmed (genuine score), Partially assessed (DPA would complete), or Requires DPA (cannot score from public policy)
- **Profile header** — active profile shown with industry, frameworks, and modified dimension weights
- **Escalation banner** — HIGH risk vendors with auto-escalation triggers show a prominent banner with specific reasons
- **Vendor follow-up questions** — 2–3 questions per gap, ready to send
- **Contract recommendations** — specific DPA/MSA redline language for scores ≤ 3
- **Team summary** — GRC decision, Legal contract checklist, Security posture (D5/D6/D8)
- **Vendor email template** — consolidated questions formatted as a ready-to-send email

Use `--no-report` to skip saving. Use `--json` to print raw JSON to stdout (report is still saved).

---

## Assessment scope

Bandit v1.0 assesses public privacy policies only.

Different documents reveal different information:

| Document | Available | Dimensions unlocked |
|----------|-----------|---------------------|
| Public privacy policy | Always | D1, D3, D6, D7 fully · D2, D4, D5 partially |
| DPA | On request | D8 fully · D2/D4/D5 complete |
| MSA | On request | D5 contractual SLA |
| SOC 2 Type II | On request | D2, D5, D7, D8 supplemented |
| BAA (healthcare) | On request | D5 HIPAA timeline |

Google Drive and local folder document support is coming in v1.1 — this will unlock full scoring across all 8 dimensions.

Until then, provide documents directly:

```bash
bandit assess "Vendor" --url https://vendor.com/privacy
```

(`--dpa` and `--docs` flags coming in v1.1)

---

## The 8 dimensions

| ID | Dimension | Weight | Regulatory basis |
|----|-----------|--------|-----------------|
| D1 | Data minimization | ×1.0 | GDPR Art. 5(1)(c) |
| D2 | Sub-processor management | ×1.0 | GDPR Art. 28(2),(4) |
| D3 | Data subject rights | ×1.0 | GDPR Arts. 12–23 |
| D4 | Transfer mechanisms | ×1.0 | GDPR Arts. 44–50 |
| D5 | Breach notification | ×1.0 | GDPR Art. 33 |
| D6 | AI/ML data usage | **×1.5** | EU AI Act 2024 · FTC |
| D7 | Retention & deletion | ×1.0 | GDPR Art. 5(1)(e) |
| D8 | DPA completeness | **×1.5** | GDPR Art. 28(3)(a)–(h) |

D6 and D8 are weighted 1.5× — AI/ML is the fastest-moving regulatory area and DPA quality sets the enforceability ceiling for D2, D5, and D7.

Weights are adjusted automatically when you run `bandit setup`. A healthcare company gets D5 weighted higher; an EU company gets D4 weighted higher.

Each dimension is scored 1–5. Risk tier:

| Tier | Weighted average |
|------|-----------------|
| HIGH | < 2.5 |
| MEDIUM | 2.5 – 3.5 |
| LOW | > 3.5 |

See [core/scoring/RUBRIC.md](core/scoring/RUBRIC.md) for full criteria, enforcement precedents, and red-flag phrase registry.

---

## Providers

| Provider | Model | Notes |
|----------|-------|-------|
| Anthropic (default) | `claude-haiku-4-5-20251001` | Fast and cost-effective |
| Anthropic | `claude-opus-4-6` | Best quality for nuanced analysis |
| OpenAI | `gpt-4o` | Excellent, widely used in enterprise |
| Google | `gemini-1.5-pro` | Strong quality at lower cost |
| Mistral | `mistral-large-latest` | European-hosted option |
| Ollama | `llama3.1`, `mistral` | **Fully local. No API key. Free.** |

Override the model with `--model`:

```bash
bandit assess "Acme Corp" --model claude-opus-4-6
bandit assess "Acme Corp" --model gpt-4o
```

---

## Discovery pipeline

When given a company name or domain, Bandit locates the privacy policy through a staged fallback:

1. **DDG search** — queries DuckDuckGo for `{vendor} privacy policy`
2. **TLD probe** — tries common privacy paths (`/privacy`, `/privacy-policy`, etc.)
3. **AI reasoning** — asks the LLM to infer the most likely domain
4. **Homepage scrape** — fetches the homepage and looks for policy links
5. **Manual flag** — logs to `~/.bandit/manual-review.json` if all stages fail

Discovered domain→URL mappings are cached in `~/.bandit/domain-cache.json`.

---

## Troubleshooting

**`ANTHROPIC_API_KEY not set`** — Export the key or pass `--api-key sk-ant-...`.

**`Could not locate a privacy policy`** — Try passing the URL directly: `bandit assess https://vendor.com/privacy`. The vendor is logged to `~/.bandit/manual-review.json`.

**Sparse policy text** — Bandit automatically retries via Jina Reader if the direct fetch returns too little text (JS-rendered pages). If both fail, the policy may require authentication.

**Wrong policy found** — Pass the full URL to bypass discovery entirely.

---

## Roadmap

**v1.0 — Live**
Privacy Bandit, CLI, HTML reports, setup profiles, assessment scope honesty, provider-agnostic.

**v1.1 — Document Sources**
Google Drive integration, local folder support, PDF parsing, full D8 scoring, multi-document assessment.

**v1.2 — Legal Bandit + Notifications**
MSA/DPA contract gap analysis, redline briefs, Slack integration, email notifications.

**v1.3 — AI Bandit + Audit Bandit**
EU AI Act compliance, SOC 2 gap analysis, framework crosswalk.

**v1.4 — Data Bandit + TPRM Register**
Data flow mapping, vendor risk register, policy change monitoring, portfolio dashboard.

**v2.0 — Full Vendor Onboarding Workflow**
Submission portal, approval workflow, vendor self-service, audit trail.

---

## The crew

Each Bandit is a specialised agent with its own tool belt:

| Agent | Status | Scope |
|-------|--------|-------|
| Privacy Bandit | **Live** | All 8 dimensions from privacy policy + DPA |
| Legal Bandit | Planned | D2, D5, D7, D8 from MSA/DPA |
| AI Bandit | Planned | D6 focused, EU AI Act compliance |
| Audit Bandit | Planned | D2, D5, D8 from SOC 2 / ISO 27001 reports |
| Data Bandit | Planned | Data flow and transfer mapping |

---

## Legacy n8n workflows

The original Bandit workflows built on n8n are preserved in [/legacy](legacy/).
They are fully functional if you prefer a visual, no-code approach.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most impactful contributions:

- **Rubric improvements** — edit `core/scoring/rubric.py` (no AI expertise needed)
- **New red-flag patterns** — add enforcement-backed phrases to the signal registry
- **Provider adapters** — add a new LLM provider to `core/llm/`
- **New agent implementations** — build out a Bandit agent class in `core/agents/`

---

## License

MIT — see [LICENSE](LICENSE).
