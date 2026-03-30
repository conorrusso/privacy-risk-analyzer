# Bandit CLI Reference

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
| `--dpa PATH` | — | Path to vendor DPA document (coming in v1.1) |

**Examples**

```bash
bandit assess "Salesforce"
bandit assess hubspot.com --verbose
bandit assess https://anecdotes.ai/privacy
bandit assess "Acme Corp" --json > acme.json
bandit assess "Acme Corp" --model claude-opus-4-6
bandit assess "Acme Corp" --no-report
```

---

### `bandit setup`

Run the interactive setup wizard. Configures dimension weights and escalation triggers for your industry and regulatory context. Saves to `./bandit.config.yml`.

```
bandit setup [OPTIONS]
```

**Options**

| Option | Description |
|--------|-------------|
| `--show` | Print current config summary and exit |
| `--reset` | Remove existing config and start the wizard fresh |

**Examples**

```bash
bandit setup             # Run full wizard (~2 minutes)
bandit setup --show      # Print current profile
bandit setup --reset     # Start over
```

The wizard covers 6 sections across 18 questions:

1. **Company location** — HQ region, customer regions, infrastructure regions
2. **Industry** — 8 options including healthcare, finance, technology, retail
3. **Data types** — PHI, PCI, children's data, special categories, AI vendors
4. **Regulatory frameworks** — GDPR, HIPAA, CCPA, PCI-DSS, SOX, and others
5. **Risk appetite** — escalation thresholds, AI flag escalation
6. **Team routing** — DPO, Legal, Security review contacts

After the wizard, Bandit shows a weight preview table and writes `bandit.config.yml` in the current directory.

See [docs/setup-guide.md](setup-guide.md) for a question-by-question walkthrough.

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

**Example**

```bash
bandit batch vendors.txt --out-dir ./output
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
| `--model MODEL` | `assess`, `batch` | Override the LLM model |
| `--api-key KEY` | `assess`, `batch` | Provide API key directly |
| `--dpa PATH` | `assess` | Path to vendor DPA document (v1.1) |
| `--out-dir DIR` | `batch` | Output directory for HTML reports |
| `--show` | `setup` | Print current config and exit |
| `--reset` | `setup` | Remove existing config and restart wizard |
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

One vendor per line. Names, domains, and URLs can be mixed freely. Lines starting with `#` and blank lines are ignored.

```
# SaaS tools
Salesforce                        ← company name
hubspot.com                       ← domain
https://notion.so/privacy         ← full URL

# Infrastructure
stripe.com
https://aws.amazon.com/privacy/
```

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
| `~/.bandit/domain-cache.json` | Discovered domain → privacy URL mappings |
| `~/.bandit/manual-review.json` | Vendors where discovery failed, for follow-up |
| `./bandit.config.yml` | Setup wizard output — industry and regulatory profile |
| `~/.bandit/bandit.config.yml` | Fallback config location (searched if `./bandit.config.yml` not found) |
