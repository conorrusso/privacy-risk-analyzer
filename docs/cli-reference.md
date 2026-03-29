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
| `--model MODEL` | `claude-haiku-4-5-20251001` | Claude model ID |
| `--api-key KEY` | `$ANTHROPIC_API_KEY` | Anthropic API key |
| `--json` | off | Print raw JSON to stdout (report still saved) |
| `-v`, `--verbose` | off | Show discovery stages, fetched pages, and signal detail |
| `--no-report` | off | Skip saving the HTML report |

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
| `--model MODEL` | `claude-haiku-4-5-20251001` | Claude model ID |
| `--api-key KEY` | `$ANTHROPIC_API_KEY` | Anthropic API key |
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

`bandit assess` and `bandit batch` accept three formats:

### Company name

```
bandit assess "Salesforce"
bandit assess "Anecdotes AI"
```

Full discovery pipeline: DDG search → domain probe → AI reasoning → homepage scrape.

### Bare domain

```
bandit assess hubspot.com
bandit assess anecdotes.ai
```

Skips domain resolution. Probes common privacy paths on the domain directly.

### Full URL

```
bandit assess https://anecdotes.ai/privacy
bandit assess https://legal.hubspot.com/privacy-policy
```

Skips all discovery. Fetches the URL directly.

---

## vendors.txt format

One vendor per line. Names, domains, and URLs can be mixed. Lines starting with `#` and blank lines are ignored.

```
# SaaS tools
Salesforce
hubspot.com
https://notion.so/privacy

# Infrastructure
stripe.com
https://aws.amazon.com/privacy/
```

---

## Environment variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key (used by `--api-key` default) |

You can also set variables in `config.env` at the repo root — they are loaded automatically on startup and do not override existing environment variables.

---

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (or graceful Ctrl+C cancel) |
| 1 | Error (API key missing, fetch failure, etc.) |

---

## Output files

HTML reports are saved to `./reports/` by default, named `<vendor-slug>-<date>.html`.

Examples:
- `reports/salesforce-2026-03-29.html`
- `reports/hubspot-com-2026-03-29.html`
- `reports/anecdotes-ai-2026-03-29.html`

---

## Cache files

| Path | Contents |
|------|----------|
| `~/.bandit/domain-cache.json` | Discovered domain → privacy URL mappings |
| `~/.bandit/manual-review.json` | Vendors where discovery failed, for follow-up |
