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

Run your first assessment:

```bash
bandit assess "Salesforce"
```

---

## Usage

```
bandit assess <vendor>         Run a full privacy risk assessment
bandit assess <vendor> -v      Verbose — see fetched pages and signals
bandit assess <vendor> --json  Output raw JSON
bandit batch <vendors.txt>     Assess a full vendor list
bandit rubric                  Show the scoring rubric summary
bandit rubric --dim D5         Show criteria for one dimension
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

## The HTML report

Every `bandit assess` run saves an HTML report to `./reports/<vendor>-<date>.html`.

The report includes:

- **Score summary** — risk tier (LOW / MEDIUM / HIGH), weighted average, per-dimension scores
- **Per-dimension detail** — evidence found (confirmed signals), gaps identified (missing signals), red flags triggered
- **Vendor follow-up questions** — 2–3 questions per gap, ready to send
- **Contract recommendations** — specific DPA/MSA redline language for scores ≤ 3
- **Team summary** — GRC decision, Legal contract checklist, Security posture (D5/D6/D8)
- **Vendor email template** — consolidated questions formatted as a ready-to-send email

Use `--no-report` to skip saving. Use `--json` to print raw JSON to stdout (report is still saved).

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
