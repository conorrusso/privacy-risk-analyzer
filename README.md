# Bandit — Vendor Risk Intelligence Suite

> Open-source AI agent for vendor privacy risk assessment. Free forever. Provider-agnostic.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Rubric: v1.0.0](https://img.shields.io/badge/Rubric-v1.0.0-brown)](core/scoring/RUBRIC.md)
[![Providers: Claude · GPT-4o · Gemini · Ollama](https://img.shields.io/badge/Providers-Claude%20%C2%B7%20GPT--4o%20%C2%B7%20Gemini%20%C2%B7%20Ollama-blue)](#providers)

---

## What Bandit does

Bandit runs AI agents against vendor privacy policies, DPAs, and compliance
documents. It scores vendors across 8 dimensions using a published,
enforcement-grounded rubric — then tells each team (GRC, Legal, Security)
what to do with the findings.

The AI extracts evidence. Bandit scores it deterministically. GPT-4o and
Claude produce the same score from the same policy.

## The 8 dimensions

| ID | Dimension | Weight | Regulatory basis |
|----|-----------|--------|-----------------|
| D1 | Data minimization | 1.0 | GDPR Art. 5(1)(c) |
| D2 | Sub-processor management | 1.0 | GDPR Art. 28(2),(4) |
| D3 | Data subject rights | 1.0 | GDPR Arts. 12–23 |
| D4 | Transfer mechanisms | 1.0 | GDPR Arts. 44–50 |
| D5 | Breach notification | 1.0 | GDPR Art. 33 |
| D6 | AI/ML data usage | **1.5** | EU AI Act 2024 · FTC |
| D7 | Retention & deletion | 1.0 | GDPR Art. 5(1)(e) |
| D8 | DPA completeness | **1.5** | GDPR Art. 28(3)(a)–(h) |

D6 and D8 are weighted 1.5× — AI/ML is the fastest-moving regulatory
area and DPA quality sets the enforceability ceiling for D2, D5, and D7.

See [core/scoring/RUBRIC.md](core/scoring/RUBRIC.md) for full criteria,
enforcement precedents, and red-flag phrase registry.

## The crew

Each Bandit is a specialised agent with its own tool belt:

| Agent | Status | Scope |
|-------|--------|-------|
| Privacy Bandit | In development | All 8 dimensions from privacy policy |
| Legal Bandit | Planned | D2, D5, D7, D8 from MSA/DPA |
| AI Bandit | Planned | D6 focused, EU AI Act compliance |
| Audit Bandit | Planned | D2, D5, D8 from SOC 2/ISO reports |
| Data Bandit | Planned | Data flow and transfer mapping |

## Providers

Bandit works with any LLM that supports tool/function calling:

| Provider | Model | Notes |
|----------|-------|-------|
| Anthropic | claude-opus-4-6 | Best quality for nuanced analysis |
| OpenAI | gpt-4o | Excellent, widely used in enterprise |
| Google | gemini-1.5-pro | Strong quality at lower cost |
| Mistral | mistral-large-latest | European-hosted option |
| Ollama | llama3.1, mistral | **Fully local. No API key. Free.** |

## Architecture

```
bandit/
├── core/
│   ├── scoring/
│   │   ├── rubric.py        ← deterministic scoring engine
│   │   └── RUBRIC.md        ← published framework document
│   ├── agents/              ← one agent class per Bandit (in dev)
│   ├── llm/                 ← provider adapters (in dev)
│   └── tools/               ← fetch, parse, extract tools (in dev)
├── legacy/
│   ├── README.md            ← legacy n8n workflow docs
│   └── n8n/                 ← original n8n workflows (fully functional)
├── examples/
│   ├── sample-high-risk-output.md
│   └── sample-low-risk-output.md
└── docs/
    └── index.html           ← GitHub Pages landing page
```

## Quick start (rubric engine — available now)

```bash
git clone https://github.com/conorrusso/bandit.git
cd bandit
pip install -r requirements.txt  # minimal: just Python stdlib + anthropic

# List all signal keys the AI needs to extract
python core/scoring/rubric.py --signals

# Score a vendor from a pre-extracted evidence JSON
python core/scoring/rubric.py evidence.json
```

The full Python agent (Privacy Bandit) is in active development.
Watch the repo for releases.

## Legacy n8n workflows

The original Bandit workflows built on n8n are preserved in [/legacy](legacy/).
They are fully functional if you prefer a visual workflow approach.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most impactful contributions:
- Rubric improvements — edit `core/scoring/rubric.py` (no AI expertise needed)
- New red-flag patterns — add enforcement-backed phrases to the registry
- Provider adapters — add a new LLM provider to `core/llm/`
- Agent implementations — build out a Bandit agent class

## License

MIT — see [LICENSE](LICENSE).
