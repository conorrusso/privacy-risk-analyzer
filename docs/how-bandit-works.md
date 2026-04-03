# How Bandit Works

Architecture and design decisions behind the Bandit assessment engine.

---

## The core principle

**AI extracts evidence. Bandit scores it deterministically.**

The LLM reads the privacy policy and returns structured boolean signals — *is this claim present, absent, or unclear?* Bandit's rubric engine converts those signals to scores using fixed rules. The same policy always produces the same score, regardless of which AI model you use.

This separation matters: it means the rubric can be audited, challenged, and improved independently of the AI. Scoring logic lives in `core/scoring/rubric.py`, not in a prompt.

---

## The 3-phase assessment pipeline

### Phase 1 — Discovery

Given a company name, domain, or URL, Bandit locates the privacy policy through a staged fallback:

1. **DuckDuckGo search** — `{vendor} privacy policy`
2. **TLD probe** — common privacy paths (`/privacy`, `/privacy-policy`, `/legal/privacy`, etc.)
3. **AI reasoning** — asks the LLM to infer the most likely domain
4. **Homepage scrape** — fetches homepage and follows policy links
5. **Manual flag** — logs to `~/.bandit/manual-review.json` if all stages fail

Discovered domain → URL mappings are cached in `~/.bandit/domain-cache.json`. SSRF is prevented by `_is_safe_url()` in `core/tools/discover.py`, which blocks requests to loopback addresses, RFC-1918 private ranges, and cloud metadata endpoints.

Full URL input bypasses all discovery stages. Bare domain input skips DDG search.

### Phase 2 — Extraction

Bandit sends the policy text (and any uploaded documents) to the LLM with a structured extraction prompt. The prompt asks the LLM to return a JSON object with boolean signals for each of the 8 dimensions.

**What the LLM does:**
- Reads the full policy text
- Returns boolean signals per dimension (e.g. `breach_notification_timeline_stated: true`)
- Does NOT score anything
- Does NOT interpret vague language — that's the rubric's job

**Document pipeline** (when `--docs` or `--drive` is used):
1. Files are classified by type (PDF, DOCX, JSON, etc.)
2. Text is extracted (pdfplumber for PDF, python-docx for DOCX)
3. Each document gets a type-specific extraction prompt (DPA → Art. 28 checklist, BAA → HIPAA provisions, SOC 2 → trust service criteria)
4. Signals are merged across documents — the stronger commitment wins when there's a conflict

**Vendor intake context** (when a vendor profile exists):
- An integration context paragraph is prepended to the extraction prompt
- Example: *"This vendor integrates with Salesforce CRM and Snowflake. They have admin access to your production environment."*
- This helps the LLM weight its signal extraction toward the most relevant provisions

### Phase 3 — Scoring

The rubric engine (`core/scoring/rubric.py`) converts extracted signals to scores deterministically:

1. **Per-dimension scoring** — each dimension has 1–5 score criteria. The presence or absence of specific signals determines the score. No LLM involved.
2. **Red flag detection** — specific phrases in the policy text trigger red flags that can lower a score or escalate the tier
3. **Weight application** — dimension scores are multiplied by their weights (default 1.0, D6 and D8 default 1.5×, modified by org profile and vendor intake)
4. **Weighted average** — produces a single score from 1.0–5.0
5. **Risk tier assignment** — HIGH (<2.5), MEDIUM (2.5–3.5), LOW (>3.5)

---

## The 8 dimensions

| ID | Dimension | What it measures |
|----|-----------|-----------------|
| D1 | Data minimization | Whether the vendor collects only what's necessary |
| D2 | Sub-processor management | Disclosure, approval, and contractual controls on third parties |
| D3 | Data subject rights | Access, deletion, portability, objection mechanisms |
| D4 | Transfer mechanisms | SCCs, adequacy decisions, BCRs for cross-border transfers |
| D5 | Breach notification | Timeline commitments and scope of notification obligations |
| D6 | AI/ML data usage | Whether your data trains models; opt-out availability |
| D7 | Retention & deletion | Specific retention periods and deletion timelines |
| D8 | DPA completeness | Whether the DPA covers all GDPR Art. 28(3) provisions |

D6 and D8 are weighted 1.5× by default. D8 can only be fully scored when a DPA is available; without one, it shows "Requires DPA" and is excluded from the weighted average.

---

## Weight modifiers

The base weights from `bandit setup` are adjusted in two ways:

**Org profile modifiers** (from `bandit setup`):
- Healthcare orgs → D5 higher, D8 higher
- EU orgs → D4 higher
- Strict risk approach → all weights increase slightly

**Vendor intake modifiers** (from `bandit vendor add`):
- Health data → D5 +0.3, D8 +0.2
- Admin access → D2 +0.3
- AI trains on your data → D6 +0.3

Intake modifiers only apply where the org profile hasn't already maximised a weight. This prevents double-counting when both the org and the vendor signal the same risk.

---

## Signal merging

When multiple documents are provided, Bandit merges signals with this rule: **the stronger commitment wins**.

Example: The public privacy policy says "we may retain data indefinitely" (weak D7 signal). A DPA clause says "data deleted within 30 days of contract termination" (strong D7 signal). The DPA signal wins.

Source attribution is preserved in the HTML report — each signal shows which document it came from.

---

## Vendor profiles and history

After each assessment, Bandit:

1. Writes the result (date, tier, score, scope, report path, next due) to the vendor profile
2. Keeps the last 10 assessment entries
3. Updates `current_risk_tier`, `last_assessed`, and `next_due`
4. Syncs the updated profile to Google Drive (if configured)

Profiles are stored at `~/.bandit/vendor-profiles.json` using atomic writes (write-to-temp then `os.replace()`).

---

## Legal Bandit

When DPA or MSA documents are present, Bandit automatically runs the Legal Bandit agent after the main assessment.

Legal Bandit:
- Checks each GDPR Art. 28(3)(a)–(h) provision against the DPA
- Detects vague language ("appropriate measures", "commercially reasonable efforts")
- Detects conflicts between the policy and the DPA
- Checks SCC version and completeness (flags pre-2021 SCCs)
- Produces a standalone legal redline brief (HTML) with specific replacement language per gap
- Updates D2, D5, D7, D8 scores based on contract findings

The legal brief is saved alongside the main report. Score changes are shown in the terminal: `D5 1→4 ↑ Contract`.

---

## Provider agnosticism

Bandit works with any LLM via provider adapters in `core/llm/`:

| Provider | Notes |
|----------|-------|
| Anthropic (default) | Claude Haiku 4.5 by default; Opus for highest quality |
| OpenAI | GPT-4o |
| Google | Gemini 1.5 Pro |
| Ollama | Fully local, no API key required |

Because scoring is deterministic and separate from extraction, the same policy produces the same score regardless of which provider you use. The LLM only affects the quality of signal extraction — a better model catches more nuanced signals.

---

## Config and state files

| File | Purpose |
|------|---------|
| `bandit.config.yml` | Org profile, weights, frameworks, reassessment config |
| `~/.bandit/vendor-profiles.json` | All vendor profiles and assessment history |
| `~/.bandit/domain-cache.json` | Cached domain → privacy URL mappings |
| `~/.bandit/vendor-history.json` | Legacy assessment history (superseded by vendor profiles) |
| `~/.bandit/manual-review.json` | Vendors where policy discovery failed |
| `~/.bandit/.intake_progress.json` | In-progress intake wizard state |
| `~/.bandit/google-token.json` | Google OAuth token |

All JSON files use atomic writes. History and cache reads catch `OSError` and `json.JSONDecodeError` — a corrupt file never crashes an assessment.
