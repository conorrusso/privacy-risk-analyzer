# The Privacy Lens — Privacy Risk Analyzer

> AI-powered vendor privacy policy analysis for compliance teams. Works with Claude, GPT-4o, Gemini, Mistral, and Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built for n8n](https://img.shields.io/badge/Built%20for-n8n-orange)](https://n8n.io)
[![PDF Engine](https://img.shields.io/badge/PDF%20Engine-Gotenberg-blueviolet)](https://gotenberg.dev)
[![Policy Fetching](https://img.shields.io/badge/Fetching-Browserless-blue)](https://browserless.io)

---

## What It Does

The Privacy Lens automates the review of vendor privacy policies, Data Processing Agreements (DPAs), and AI vendor assessments. It scores each document across 8 risk dimensions (D1–D8) aligned to GDPR, CCPA, and the EU AI Act, then routes results to your existing tools (Google Drive, Jira, Slack).

Each assessment produces a structured JSON risk report **and** a styled PDF report — automatically saved to the vendor's folder in Google Drive.

**Workflows included:**
| File | Purpose |
|------|---------|
| `privacy-policy-analyzer.json` | Full batch privacy policy intake, scoring, and PDF report generation |
| `dpa-gap-checker.json` | DPA clause coverage vs. GDPR Art. 28 checklist |
| `ai-vendor-assessment.json` | Specialized scoring for AI/ML vendors (EU AI Act) |

---

## Architecture

The main workflow (`privacy-policy-analyzer.json`) runs as a **full batch loop** — it processes every vendor folder in your Google Drive `Privacy Reviews/` root and skips any vendor assessed within the last year.

### Policy Fetching — Browserless

Privacy policies are fetched via [Browserless](https://github.com/browserless/browserless) (a self-hosted headless Chromium service), not a simple HTTP request. This gives:

- **Stealth mode** — bypasses bot-detection and JS-rendered paywalls common on privacy policy pages
- **Full page rendering** — captures content that only appears after JavaScript runs
- **No external dependency** — runs entirely inside Docker alongside n8n and Gotenberg

### 3-Tier URL Discovery

The workflow automatically discovers the privacy policy URL for each vendor using a 3-tier chain, so you don't need to supply URLs manually:

| Tier | Method | Detail |
|------|--------|--------|
| **Tier 1** | Common paths | Tries `/privacy`, `/privacy-policy`, `/legal/privacy`, etc. against the vendor domain |
| **Tier 2** | `robots.txt` | Parses `robots.txt` for a `Sitemap:` or privacy-related path reference |
| **Tier 3** | Homepage scrape | Renders the homepage via Browserless and extracts the first `<a>` tag matching "privacy" |

The **🔗 Prepare Fetch Context** node normalizes the vendor name, domain, and discovered URL into a consistent shape before Browserless fetches the policy — regardless of which tier found it.

### PDF Report Generation — Gotenberg

After AI scoring, the workflow generates a styled retro-terminal HTML report and converts it to PDF via [Gotenberg](https://gotenberg.dev), which runs as a sidecar container in the same Docker Compose network.

### AI Scoring

Policies are scored by `claude-sonnet-4-20250514` across 8 risk dimensions (D1–D8). The prompt and scoring rubric are in [`prompts/PT-1-privacy-policy-analysis.md`](prompts/PT-1-privacy-policy-analysis.md) and [`frameworks/privacy-risk-scoring-rubric.md`](frameworks/privacy-risk-scoring-rubric.md).

---

## Prerequisites

- [Docker](https://www.docker.com) and [Docker Compose](https://docs.docker.com/compose/)
- An Anthropic API key (Claude) — or swap to GPT-4o, Gemini, Mistral, or Ollama
- Optional: Google Drive, Jira, and/or Slack credentials for output routing

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/conorrusso/privacy-risk-analyzer.git
cd privacy-risk-analyzer
```

### 2. Start n8n + Gotenberg + Browserless

```bash
docker compose up -d
```

This starts three services:
- **n8n** at `http://localhost:5678` — workflow orchestration
- **Gotenberg** at `http://localhost:3000` — HTML to PDF conversion
- **Browserless** at `http://localhost:3001` — headless Chromium for policy fetching

The `docker-compose.yml` in the repo root is pre-configured with the correct network settings. All three containers resolve each other by service name (`http://gotenberg:3000`, `http://browserless:3000`).

To stop all services:
```bash
docker compose down
```

### 3. Import the Workflow

1. Open n8n at `http://localhost:5678`
2. Click **Workflows → Import from File**
3. Select `workflows/privacy-policy-analyzer.json`
4. Configure your credentials (see [integrations/](integrations/))

> **IF node import bug:** n8n has a known issue where IF nodes imported from JSON can silently route all traffic through one branch. If your workflow skips the error path or never reaches a downstream node, **delete the IF node and recreate it fresh** by dragging a new IF node from the panel, then rewire it. This is a one-time fix after import.

### 4. Set Up Google Drive

Create this folder structure in Google Drive before running:

```
Privacy Reviews/
└── [Vendor Name]/     ← one folder per vendor
```

The workflow discovers all vendor subfolders automatically on each run and saves both the JSON and PDF report to the matching folder. See [integrations/google-drive-setup.md](integrations/google-drive-setup.md) for full setup instructions.

### 5. Configure Your Anthropic API Key

In the workflow, open the **🧠 AI Provider — Score Privacy Policy** node and set your API key as an n8n credential (never hardcode it in the node directly). The default model is `claude-sonnet-4-20250514`.

To use a different AI provider, see the [AI Provider switching guide](#ai-provider-switching) below.

### 6. Run Your First Batch

Trigger the workflow manually in n8n. For each vendor folder, the workflow will:

1. Check if a recent assessment already exists (skips if assessed within 1 year)
2. Auto-discover the privacy policy URL via 3-tier chain
3. Fetch and render the policy page via Browserless (stealth mode)
4. Extract and clean the policy text
5. Score it across 8 dimensions using your AI provider
6. Generate a styled PDF report via Gotenberg
7. Save both the PDF and JSON to the vendor's folder in Drive
8. Log any failed URL discoveries to a `needs-manual-review` file

---

## AI Provider Switching

The workflow uses a single HTTP Request node for the AI call — swap the endpoint and auth header to change providers:

| Provider | Endpoint | Auth | Response Path |
|----------|----------|------|---------------|
| Claude (Anthropic) | `api.anthropic.com/v1/messages` | `x-api-key` header | `content[0].text` |
| GPT-4o (OpenAI) | `api.openai.com/v1/chat/completions` | `Authorization: Bearer` | `choices[0].message.content` |
| Gemini (Google) | `generativelanguage.googleapis.com/...?key=` | Query param | `candidates[0].content.parts[0].text` |
| Mistral | `api.mistral.ai/v1/chat/completions` | `Authorization: Bearer` | `choices[0].message.content` |
| Ollama (local) | `localhost:11434/api/generate` | None | `response` |

---

## Risk Scoring Framework

Policies are scored across 8 dimensions (D1–D8) on a 1–5 scale. An overall **Privacy Risk Score (PRS)** is calculated as a weighted average. See [`/frameworks/privacy-risk-scoring-rubric.md`](frameworks/privacy-risk-scoring-rubric.md) for full definitions and thresholds.

| Score Range | Risk Level | Recommended Action |
|-------------|------------|-------------------|
| 1.0 – 2.0 | High Risk | Negotiate DPA amendments or escalate to DPO |
| 2.1 – 3.5 | Medium Risk | Legal review required |
| 3.6 – 4.5 | Low-Medium | Approve with standard review |
| 4.6 – 5.0 | Low Risk | Approve |

> **Note:** Scores are inverted — a lower score means higher risk. D6 (AI/ML Data Usage) and D8 (DPA Completeness) carry 1.5× weight.

---

## Security Notes

### API Keys
- Store all API keys as **n8n credentials**, never hardcoded in workflow nodes.
- If a key was ever pasted directly into a workflow node during testing, rotate it immediately.

### Browserless
- Browserless is protected by a token (`TOKEN=privacy-lens` in `docker-compose.yml`). Change this for any shared or production environment.
- **Never expose port 3001 publicly.** Bind to localhost or place behind a firewall.

### Gotenberg
- Gotenberg has **no authentication** by default.
- **Never expose port 3000 publicly.** The `docker-compose.yml` in this repo is for local use only.

---

## Repository Structure

```
privacy-risk-analyzer/
├── docker-compose.yml          ← starts n8n + Gotenberg + Browserless
├── workflows/
│   ├── privacy-policy-analyzer.json   ← batch workflow (current)
│   ├── dpa-gap-checker.json
│   └── ai-vendor-assessment.json
├── prompts/
│   └── PT-1-privacy-policy-analysis.md
├── frameworks/
│   └── privacy-risk-scoring-rubric.md
├── integrations/
│   ├── n8n-setup.md
│   ├── google-drive-setup.md
│   ├── jira-setup.md
│   └── slack-setup.md
├── examples/
│   ├── sample-high-risk-output.md
│   └── sample-low-risk-output.md
├── docs/
│   └── index.html              ← GitHub Pages landing page
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

---

## Troubleshooting

These are real issues encountered during development of this workflow:

| Issue | Cause | Fix |
|-------|-------|-----|
| PDF node returns connection error | Gotenberg not running or wrong URL | Run `docker compose up -d` and confirm Gotenberg is at `localhost:3000`. Inside Docker Compose the URL should be `http://gotenberg:3000` |
| PDF node returns empty file | HTML binary not passed correctly | Confirm the Generate HTML Report node returns a `binary.htmlFile` field, not just JSON |
| Policy fetch returns 403 or empty | Site blocking headless browsers | Browserless stealth mode handles most cases; for stubborn sites, check the Browserless token is set correctly |
| AI node returns non-JSON response | Model wrapped output in markdown code fences | The Parse Assessment JSON node strips ` ```json ` fences before parsing — ensure this node is present |
| Workflow stops at IF node | IF node imported with wrong routing | Delete the IF node and recreate it fresh from the node panel, then rewire. This is a one-time fix after import. |
| Vendor folder not found | Vendor folder name mismatch | Folder name in Drive must match exactly — check for trailing spaces or casing differences |
| All vendors skipped | Assessments exist and are < 1 year old | Expected behaviour — delete old assessment files or set `skipVendor = false` temporarily |
| `docker compose` command not found | Using older Docker with separate compose plugin | Try `docker-compose up -d` (with hyphen) or upgrade Docker Desktop |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Community prompt contributions and additional workflow templates are very welcome.

## License

MIT — see [LICENSE](LICENSE).
