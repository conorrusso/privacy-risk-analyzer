# Bandit — Repo Restructure & Deploy Task

This file tells Claude Code exactly what to do to restructure the repo,
apply all updated files, and push everything. Run top to bottom.

---

## Context

Bandit is migrating from n8n workflows (v0.x) to a native Python agent
architecture (v1.0). The repo needs to be restructured to reflect this.
Nothing gets deleted — n8n workflows move to /legacy.

The local repo is at: `~/projects/privacy-risk-analyzer`
(Note: the GitHub repo has been renamed to `bandit` but the local
folder may still be named `privacy-risk-analyzer`)

---

## Step 1 — Verify repo location

```bash
cd ~/projects/privacy-risk-analyzer
git status
git remote -v
```

Confirm the remote points to `github.com/conorrusso/bandit`. If not,
update it:
```bash
git remote set-url origin https://github.com/conorrusso/bandit.git
```

---

## Step 2 — Create new directory structure

```bash
cd ~/projects/privacy-risk-analyzer

# New core structure
mkdir -p core/scoring
mkdir -p core/agents
mkdir -p core/llm
mkdir -p core/tools

# Legacy structure
mkdir -p legacy/n8n/integrations
mkdir -p legacy/n8n/prompts
```

---

## Step 3 — Move n8n files to legacy

```bash
cd ~/projects/privacy-risk-analyzer

# Move workflow JSONs
git mv workflows/bandit-privacy.json legacy/n8n/bandit-privacy.json
git mv workflows/dpa-gap-checker.json legacy/n8n/dpa-gap-checker.json
git mv workflows/ai-vendor-assessment.json legacy/n8n/ai-vendor-assessment.json

# Move integrations
git mv integrations/n8n-setup.md legacy/n8n/integrations/n8n-setup.md
git mv integrations/google-drive-setup.md legacy/n8n/integrations/google-drive-setup.md
git mv integrations/jira-setup.md legacy/n8n/integrations/jira-setup.md
git mv integrations/slack-setup.md legacy/n8n/integrations/slack-setup.md

# Move prompt template
git mv prompts/PB-1-privacy-policy-analysis.md legacy/n8n/prompts/PB-1-privacy-policy-analysis.md

# Move docker-compose (n8n stack)
git mv docker-compose.yml legacy/n8n/docker-compose.yml

# Move old scoring rubric (superseded by core/scoring/RUBRIC.md)
git mv frameworks/privacy-risk-scoring-rubric.md legacy/n8n/privacy-risk-scoring-rubric-v0.md

# Remove now-empty directories
rmdir workflows 2>/dev/null || true
rmdir integrations 2>/dev/null || true
rmdir prompts 2>/dev/null || true
rmdir frameworks 2>/dev/null || true
```

---

## Step 4 — Copy in new files

These files were produced externally and need to be copied in.
They should be in your Downloads folder or wherever you saved them.

```bash
cd ~/projects/privacy-risk-analyzer

# Rubric engine (from Downloads or wherever saved)
cp ~/Downloads/rubric.py core/scoring/rubric.py
cp ~/Downloads/RUBRIC.md core/scoring/RUBRIC.md

# Legacy README
cp ~/Downloads/legacy-README.md legacy/README.md

# Updated landing page
cp ~/Downloads/index.html docs/index.html
```

If the files are named differently, adjust the paths above.

---

## Step 5 — Fix the license in rubric.py

Open `core/scoring/rubric.py` and find line 7:
```
License : Apache-2.0 (matches Privacy Lens project)
```

Replace with:
```
License : MIT
```

---

## Step 6 — Create placeholder files for new architecture

These let contributors know what's being built:

```bash
cd ~/projects/privacy-risk-analyzer

cat > core/__init__.py << 'EOF'
"""
Bandit Core — Vendor Risk Intelligence Suite
"""
EOF

cat > core/agents/__init__.py << 'EOF'
"""
Bandit agent classes. Each Bandit is a specialised AI agent
with its own tool belt and dimension scope.

In development:
  PrivacyBandit — privacy policy scoring (8 dimensions)
  LegalBandit   — MSA/DPA contract risk
  AIBandit      — AI/ML usage and EU AI Act compliance
  AuditBandit   — SOC 2 / ISO 27001 gap analysis
  DataBandit    — data flow mapping
"""
EOF

cat > core/llm/__init__.py << 'EOF'
"""
Provider-agnostic LLM adapter layer.
Supports: Anthropic, OpenAI, Google Gemini, Ollama (local).
"""
EOF

cat > core/tools/__init__.py << 'EOF'
"""
Tool implementations for Bandit agents.
fetch, parse, extract, storage tools.
"""
EOF

cat > core/scoring/__init__.py << 'EOF'
"""
Bandit Scoring Engine — deterministic rubric-based scoring.
The AI extracts evidence; Bandit scores it.
"""
EOF
```

---

## Step 7 — Update README.md

Replace the entire README.md with the following content:

```bash
cat > ~/projects/privacy-risk-analyzer/README.md << 'READMEEOF'
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
READMEEOF
```

---

## Step 8 — Stage and commit everything

```bash
cd ~/projects/privacy-risk-analyzer

git add -A
git status  # review what's changing

git commit -m "feat: v1.0 architecture — Python agent core, rubric engine, legacy n8n preserved

- Add core/scoring/rubric.py — deterministic v1.0.0 scoring engine
- Add core/scoring/RUBRIC.md — published enforcement-grounded framework
- Move all n8n workflows, integrations, prompts → legacy/n8n/
- Add legacy/README.md explaining v0.x vs v1.0 architecture
- Add core agent/llm/tools scaffolding with __init__.py docs
- Update README.md for v1.0 architecture
- Update docs/index.html — new rubric section, provider section, free forever messaging"

git push origin main
```

---

## Step 9 — Verify GitHub Pages

After push, check:
- https://conorrusso.github.io/bandit/ — landing page updated
- https://github.com/conorrusso/bandit/blob/main/core/scoring/RUBRIC.md — rubric live

GitHub Pages typically updates within 60 seconds of push.

---

## Step 10 — Clean up

Delete this task file once done:
```bash
rm ~/projects/privacy-risk-analyzer/RESTRUCTURE.md
git add -A
git commit -m "chore: remove restructure task file"
git push origin main
```
