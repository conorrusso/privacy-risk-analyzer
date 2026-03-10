# n8n Setup Guide

**The Privacy Lens — Integration Guide**

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

### Option C: Self-Hosted with Docker

```bash
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  docker.n8nio/n8n
```

### Option D: Docker Compose (Production)

```yaml
version: '3.8'
services:
  n8n:
    image: docker.n8nio/n8n
    restart: always
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=your_secure_password
      - WEBHOOK_URL=https://your-domain.com/
    volumes:
      - n8n_data:/home/node/.n8n
volumes:
  n8n_data:
```

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
