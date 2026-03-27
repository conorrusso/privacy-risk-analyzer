# n8n Setup Guide

**Bandit — Integration Guide**

---

## Requirements

- n8n v1.30 or later
- Node.js 18+ (for self-hosted)
- One supported AI provider account (see below)

---

## Installation Options

### Option A: n8n Cloud (Recommended for Quick Start)

1. Sign up at [n8n.io](https://n8n.io)
2. Create a new workspace
3. Import workflows from `/workflows/` via **Workflows → Import from File**

### Option B: Self-Hosted with npm

```bash
npm install -g n8n
n8n start
# Access at http://localhost:5678
```

> Note: If using npm, you will need to run Gotenberg separately. See the Gotenberg section below.

### Option C: Docker Compose (Recommended for local self-hosted)

This is the approach used to build and test this workflow. It runs n8n, Gotenberg, and Browserless together with a single command:

```bash
git clone https://github.com/conorrusso/bandit.git
cd bandit
docker compose up -d
```

All three services will start automatically:
- n8n at `http://localhost:5678`
- Gotenberg at `http://localhost:3000` (HTML → PDF conversion)
- Browserless at `http://localhost:3001` (headless Chromium for policy fetching)

The `docker-compose.yml` in the repo root is pre-configured with the correct network settings so all containers can reach each other by service name (`http://gotenberg:3000`, `http://browserless:3000`).

---

## Setting Up Gotenberg

Gotenberg is an open source Docker-powered PDF conversion engine. Bandit uses it to convert the styled HTML report into a PDF and save it to Google Drive.

### Why Gotenberg?
- No external API account required
- Runs entirely locally inside Docker
- Handles complex CSS, web fonts, and dark themes accurately

### Running Gotenberg standalone (if not using Docker Compose)

```bash
docker run -d \
  --name gotenberg \
  -p 3000:3000 \
  gotenberg/gotenberg:8
```

If running standalone, update the **Convert to PDF** node URL in the workflow from `http://gotenberg:3000` to `http://localhost:3000`.

### Security
- Gotenberg has **no authentication** by default
- **Never expose port 3000 publicly** — bind to localhost only
- The Docker Compose config in this repo is for local development only

---

## Setting Up Browserless

Browserless is a self-hosted headless Chromium service. Bandit uses it for policy fetching instead of plain HTTP requests — this handles JavaScript-rendered pages and bypasses common bot-detection mechanisms.

### Why Browserless?
- Renders JavaScript-heavy pages that a plain `fetch` would miss
- Stealth mode bypasses bot-detection used on many privacy policy pages
- Runs entirely locally inside Docker — no external API calls

### Running Browserless standalone (if not using Docker Compose)

```bash
docker run -d \
  --name browserless \
  -p 3001:3000 \
  -e TOKEN=bandit \
  ghcr.io/browserless/chromium
```

If running standalone, update the **📥 Fetch Privacy Policy** node URL in the workflow from `http://browserless:3000` to `http://localhost:3001`.

### Security
- Browserless is token-protected — the default token is `privacy-lens` (set in `docker-compose.yml`)
- **Change the token** for any shared or production environment
- **Never expose port 3001 publicly**

---

## Configuring AI Provider Credentials

### Anthropic (Claude)

1. Get an API key at [console.anthropic.com](https://console.anthropic.com)
2. In n8n: **Settings → Credentials → New → Anthropic API**
3. Paste your API key
4. In the workflow, set the AI node to use this credential
5. Recommended model: `claude-opus-4-6`

### OpenAI (GPT-4o)

1. Get an API key at [platform.openai.com](https://platform.openai.com)
2. In n8n: **Settings → Credentials → New → OpenAI API**
3. In the workflow, replace the AI node with **OpenAI Chat Model**
4. Recommended model: `gpt-4o`

### Google (Gemini)

1. Enable Generative AI API in Google Cloud Console
2. In n8n: **Settings → Credentials → New → Google Gemini API**
3. Replace AI node with **Google Gemini Chat Model**
4. Recommended model: `gemini-1.5-pro`

### Mistral AI

1. Get an API key at [console.mistral.ai](https://console.mistral.ai)
2. In n8n: **Settings → Credentials → New → Mistral Cloud API**
3. Replace AI node with **Mistral Cloud Chat Model**
4. Recommended model: `mistral-large-latest`

### Ollama (Local / No API Key Required)

1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
2. Pull a model: `ollama pull llama3` or `ollama pull mistral`
3. In n8n: **Settings → Credentials → New → Ollama API**
4. Set base URL to `http://localhost:11434`
5. Replace AI node with **Ollama Chat Model**

> **Note:** Local models via Ollama will produce lower-quality analysis than frontier models. Use for testing only; production use recommended with Claude or GPT-4o.

---

## Importing Workflows

1. Open n8n at `http://localhost:5678`
2. Click **Workflows** in the left sidebar
3. Click **+ New** → **Import from File**
4. Select a JSON file from the `/workflows/` folder
5. Review the imported workflow
6. Update each credential node with your configured credentials
7. Click **Save**, then **Activate**

---

## Environment Variables (Self-Hosted)

```bash
# Required
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=changeme

# Recommended
N8N_ENCRYPTION_KEY=your_32_char_encryption_key
WEBHOOK_URL=https://your-public-domain.com/
N8N_LOG_LEVEL=info

# Optional: External DB (production)
DB_TYPE=postgresdb
DB_POSTGRESDB_HOST=localhost
DB_POSTGRESDB_PORT=5432
DB_POSTGRESDB_DATABASE=n8n
DB_POSTGRESDB_USER=n8n
DB_POSTGRESDB_PASSWORD=your_db_password
```

---

## Switching AI Providers

The workflow uses an **HTTP Request node (Node 4)** to call the AI provider directly. This makes it fully provider-agnostic — swap the URL, headers, and body to use any supported model. No n8n AI node required.

In n8n, open **Node 4 → HTTP Request** and update the fields below for your chosen provider.

---

### 1. Anthropic Claude *(current default)*

**API key:** [console.anthropic.com](https://console.anthropic.com) → API Keys → Create Key

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `https://api.anthropic.com/v1/messages` |
| Header: `x-api-key` | `YOUR_ANTHROPIC_API_KEY` |
| Header: `anthropic-version` | `2023-06-01` |
| Header: `content-type` | `application/json` |

**Body (JSON):**
```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 2000,
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.prompt }}"
    }
  ]
}
```

**Parse response:** `{{ $json.content[0].text }}`

**Estimated cost per assessment:** ~$0.01–0.03 (≈3,000 input + 800 output tokens at Sonnet pricing)

---

### 2. OpenAI GPT-4o

**API key:** [platform.openai.com](https://platform.openai.com) → API Keys → Create new secret key

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `https://api.openai.com/v1/chat/completions` |
| Header: `Authorization` | `Bearer YOUR_OPENAI_API_KEY` |
| Header: `content-type` | `application/json` |

**Body (JSON):**
```json
{
  "model": "gpt-4o",
  "max_tokens": 2000,
  "temperature": 0.1,
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.prompt }}"
    }
  ]
}
```

**Parse response:** `{{ $json.choices[0].message.content }}`

**Estimated cost per assessment:** ~$0.05–0.10 (≈3,000 input + 800 output tokens at GPT-4o pricing)

---

### 3. Google Gemini

**API key:** [aistudio.google.com](https://aistudio.google.com) → Get API key → Create API key

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=YOUR_GEMINI_API_KEY` |
| Header: `content-type` | `application/json` |

> Note: The API key is passed as a query parameter in the URL, not as a header.

**Body (JSON):**
```json
{
  "contents": [
    {
      "parts": [
        {
          "text": "{{ $json.prompt }}"
        }
      ]
    }
  ],
  "generationConfig": {
    "temperature": 0.1,
    "maxOutputTokens": 2000
  }
}
```

**Parse response:** `{{ $json.candidates[0].content.parts[0].text }}`

**Estimated cost per assessment:** ~$0.00–0.01 (Gemini 2.0 Flash is very low cost; free tier available)

---

### 4. Mistral

**API key:** [console.mistral.ai](https://console.mistral.ai) → API Keys → Create new key

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `https://api.mistral.ai/v1/chat/completions` |
| Header: `Authorization` | `Bearer YOUR_MISTRAL_API_KEY` |
| Header: `content-type` | `application/json` |

**Body (JSON):**
```json
{
  "model": "mistral-large-latest",
  "max_tokens": 2000,
  "temperature": 0.1,
  "messages": [
    {
      "role": "user",
      "content": "{{ $json.prompt }}"
    }
  ]
}
```

**Parse response:** `{{ $json.choices[0].message.content }}`

**Estimated cost per assessment:** ~$0.02–0.05 (Mistral Large pricing; Mistral Small available at ~10× lower cost)

---

### 5. Ollama (Local / Completely Free)

No API key or account required. Runs entirely on your machine.

**Prerequisites:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model (run once)
ollama pull mistral        # ~4GB, good quality
ollama pull llama3.1       # ~5GB, best open-source option
ollama pull phi3           # ~2GB, fast, lower quality

# Start the server (if not already running)
ollama serve
```

| Field | Value |
|-------|-------|
| Method | `POST` |
| URL | `http://localhost:11434/api/generate` |
| Header: `content-type` | `application/json` |
| Authentication | None |

**Body (JSON):**
```json
{
  "model": "mistral",
  "prompt": "{{ $json.prompt }}",
  "stream": false,
  "options": {
    "temperature": 0.1,
    "num_predict": 2000
  }
}
```

**Parse response:** `{{ $json.response }}`

> Note: Ollama uses a different response format from the cloud providers — `response` (string) instead of a nested `choices` or `content` array.

**Estimated cost per assessment:** $0.00 — fully local, no API calls, no usage limits

> **Quality note:** Local models produce usable but less precise analysis than frontier models. Recommended for development, testing, and cost-sensitive environments. For production compliance use, prefer Claude or GPT-4o.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Workflow fails with "credential not found" | Re-link credential in affected node |
| AI node returns invalid JSON | Increase `max_tokens`, lower `temperature` to 0.1 |
| Webhook not triggering | Check `WEBHOOK_URL` env var matches your public domain |
| Ollama connection refused | Ensure Ollama is running: `ollama serve` |
| PDF node returns connection error | Confirm Gotenberg is running: `docker ps` — should show `gotenberg` container. Check URL is `http://gotenberg:3000` inside Docker Compose or `http://localhost:3000` if standalone |
| PDF node returns empty binary | Confirm the Generate HTML Report node outputs `binary.htmlFile` — check the node's output in n8n execution view |
| Policy fetch returns 403 or empty | Browserless not running or token mismatch — confirm `browserless` container is up and `TOKEN=bandit` is set |
| IF node routes to wrong branch | Imported IF nodes can silently misroute — delete the node and recreate it fresh from the node panel, then rewire |
| Google Drive folder not found | Folder name in Drive must match search query exactly — check for trailing spaces or casing |
| `docker compose` not found | Try `docker-compose` (with hyphen) or upgrade Docker Desktop |
