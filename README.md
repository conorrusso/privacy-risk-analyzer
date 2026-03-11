# The Privacy Lens — Privacy Risk Analyzer

> AI-powered vendor privacy policy analysis for compliance teams. Works with Claude, GPT-4o, Gemini, Mistral, and Ollama.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Built for n8n](https://img.shields.io/badge/Built%20for-n8n-orange)](https://n8n.io)
[![PDF Engine](https://img.shields.io/badge/PDF%20Engine-Gotenberg-blueviolet)](https://gotenberg.dev)

---

## What It Does

The Privacy Lens automates the review of vendor privacy policies, Data Processing Agreements (DPAs), and AI vendor assessments. It scores each document across 8 risk dimensions (D1–D8) aligned to GDPR, CCPA, and the EU AI Act, then routes results to your existing tools (Google Drive, Jira, Slack).

Each assessment produces a structured JSON risk report **and** a styled PDF report — automatically saved to the vendor's folder in Google Drive.

**Workflows included:**
| File | Purpose |
|------|---------|
| `privacy-policy-analyzer.json` | Full privacy policy intake, scoring, and PDF report generation |
| `dpa-gap-checker.json` | DPA clause coverage vs. GDPR Art. 28 checklist |
| `ai-vendor-assessment.json` | Specialized scoring for AI/ML vendors (EU AI Act) |

---

## Prerequisites

- [Docker](https://www.docker.com) and [Docker Compose](https://docs.docker.com/compose/) — used to run both n8n and Gotenberg
- An AI provider API key — one of:
  - Anthropic (Claude)
  - OpenAI (GPT-4o)
  - Google (Gemini)
  - Mistral AI
  - Ollama (local, no key required)
- Optional: Google Drive, Jira, and/or Slack credentials for output routing

---

## Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/conorrusso/privacy-risk-analyzer.git
cd privacy-risk-analyzer
```

### 2. Start n8n + Gotenberg

This project uses Docker Compose to run both services together. The `docker-compose.yml` in the repo root is exactly what was used to build and test this workflow:

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    container_name: n8n
    ports:
      - "5678:5678"
    volumes:
      - ~/.n8n:/home/node/.n8n
    environment:
      - N8N_HOST=localhost
      - N8N_PORT=5678
    restart: unless-stopped

  gotenberg:
    image: gotenberg/gotenberg:8
    container_name: gotenberg
    ports:
      - "3000:3000"
    restart: unless-stopped
```

```bash
docker compose up -d
```

This starts:
- **n8n** at `http://localhost:5678` — workflow orchestration
- **Gotenberg** at `http://localhost:3000` — HTML to PDF conversion engine

To stop both services:
```bash
docker compose down
```

> **Container networking note:** The workflow's Convert to PDF node calls `http://gotenberg:3000` — this works because both containers are on the same Docker Compose network and resolve each other by service name. If you run Gotenberg separately outside of Docker Compose, change this URL in the workflow node to `http://localhost:3000` instead.

### 3. Import a Workflow

1. Open n8n at `http://localhost:5678`
2. Click **Workflows → Import from File**
3. Select a JSON file from the `/workflows/` folder
4. Configure your credentials (see [integrations/](integrations/))

### 4. Set Up Google Drive

Before running an assessment, create a folder structure in Google Drive:

```
Privacy Reviews/
└── [Vendor Name]/     ← one folder per vendor
```

The workflow will find the vendor folder by name and save both the JSON and PDF report there automatically. See [integrations/google-drive-setup.md](integrations/google-drive-setup.md) for full setup instructions.

### 5. Set Your AI Provider

In each workflow, locate the **AI Provider** node and configure:
- **URL**: your provider's API endpoint
- **API Key**: stored as an n8n credential
- **Model**: e.g. `claude-sonnet-4-6`, `gpt-4o`, `gemini-1.5-pro`

See the [AI Provider switching guide](#ai-provider-switching) below for endpoint details.

### 6. Run Your First Analysis

Trigger the `privacy-policy-analyzer` workflow manually in n8n. The workflow will:

1. Search Google Drive for the vendor's folder
2. Fetch and parse the privacy policy URL
3. Score it across 8 dimensions using your AI provider
4. Generate a styled PDF report via Gotenberg
5. Save both the PDF and JSON to the vendor folder in Drive

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

### Gotenberg
- Gotenberg has **no authentication** by default. It should only be accessible on `localhost`.
- **Never expose port 3000 publicly.** If deploying to a server, bind Gotenberg to `127.0.0.1` only or place it behind a firewall.
- The `docker-compose.yml` in this repo is configured for local use. Review your network configuration before deploying to any shared or cloud environment.

### API Keys
- Store all API keys as **n8n credentials**, never hardcoded in workflow nodes.
- Rotate your AI provider key if it was ever pasted directly into a workflow node during setup.

---

## Repository Structure

```
privacy-risk-analyzer/
├── docker-compose.yml          ← starts n8n + Gotenberg together
├── workflows/
│   ├── privacy-policy-analyzer.json
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
| AI node returns non-JSON response | Model wrapped output in markdown code fences | The Parse Assessment JSON node strips ` ```json ` fences before parsing — ensure this node is present |
| Google Drive folder not found | Vendor folder name doesn't match exactly | Folder name in Drive must match the search query exactly — check for trailing spaces or casing differences |
| Workflow stops at IF node | Vendor folder genuinely missing | Create the folder manually in `Privacy Reviews/[Vendor Name]/` before running |
| `docker compose` command not found | Using older Docker with separate compose plugin | Try `docker-compose up -d` (with hyphen) or upgrade Docker Desktop |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Community prompt contributions and additional workflow templates are very welcome.

## License

MIT — see [LICENSE](LICENSE).
