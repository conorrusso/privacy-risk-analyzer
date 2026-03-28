# Legacy — Bandit v0.x (n8n Workflows)

These workflows represent Bandit v0.x, built on n8n. They are fully
functional and documented for users who prefer a visual workflow approach
or are already running an n8n stack.

**Bandit v1.0+ uses a native Python agent architecture.**
See the main [README](../README.md) for the current approach.

---

## What's here

| File | Description |
|------|-------------|
| `n8n/bandit-privacy.json` | Batch privacy policy assessment workflow |
| `n8n/dpa-gap-checker.json` | DPA clause coverage vs GDPR Art. 28 |
| `n8n/ai-vendor-assessment.json` | AI/ML vendor scoring with EU AI Act |
| `n8n/docker-compose.yml` | n8n + Gotenberg + Browserless stack |
| `n8n/integrations/` | Setup guides for n8n, Google Drive, Jira, Slack |
| `n8n/prompts/` | Original PB-1 prompt template |

## Running the legacy workflows

### Prerequisites
- Docker and Docker Compose
- Anthropic API key (or swap to GPT-4o, Gemini, Mistral, Ollama)
- Google Drive credentials (optional)

### Quick start
```bash
cd legacy/n8n
docker compose up -d
# Open n8n at http://localhost:5678
# Import any .json workflow via Workflows → Import from File
```

See `n8n/integrations/n8n-setup.md` for full setup instructions.

---

## Why we migrated

The n8n workflows were a great starting point but had limitations
at scale — no true agent reasoning, hard to contribute to, and
required a Docker stack just to run a single assessment.

The v1.0 Python agent architecture:
- Runs as a single Python script or `pip install`
- Works with any LLM provider including fully local Ollama
- Each Bandit is a proper agent that adapts to what it finds
- The scoring rubric is deterministic and provider-agnostic
- Much easier to contribute to and extend

The legacy workflows are preserved here because they still work
and some users prefer the visual n8n approach.
