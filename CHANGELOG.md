# Changelog

All notable changes to Bandit are documented here.

Format: `Added` new features · `Changed` behaviour or UX · `Fixed` bugs · `Removed` deleted code · `Security` vulnerability fixes

---

## [1.4.0] — 2026-04-09

### Architecture
- `core/data/resolver.py`: `VendorDataResolver` — unified data access layer for all commands. Knows whether vendor data lives locally or in Drive and fetches from the right place transparently. `drive_folder_id` stored in vendor profile — no search needed.
- All core/ modules return dataclasses, never print. CLI renders. Future UI calls core directly.
- `on_progress` callback pattern throughout for streaming-compatible progress reporting.
- `--json` flag on all new commands for UI API surface.

### Added

**Dashboard**
- `bandit dashboard show` — portfolio risk overview. Risk distribution, due vendors, open findings, intake completion rate, Drive vs local breakdown
- `bandit dashboard schedule` — reassessment schedule sorted by urgency, shows days overdue, recommended depth per vendor, data source (Drive/local)
- `bandit dashboard register` — TPRM register export. CSV, JSON, or HTML output with all vendor data
- `bandit dashboard notify` — send IT notifications

**Top-level aliases (convenience)**
- `bandit schedule`
- `bandit register [--format csv|json|html] [--out FILE]`
- `bandit notify [vendor] [--all]`

**Data resolver**
- `VendorDataResolver` used by `bandit assess` — replaces direct Drive/local document loading
- Deduplicates documents across sources (Drive wins over local)
- Sync failures never block assessment

**Notifications**
- Slack webhook support (Incoming Webhooks)
- Email support via SMTP
- `bandit setup --notify` extended: now collects Slack webhook URL in addition to email and channel name
- Notifications marked sent in vendor profile after successful send
- `bandit notify --all` sends all pending

---

## [1.3.0] — 2026-04-01

### Added

**Vendor Intelligence**
- `bandit vendor add` — 12-question intake wizard
- `bandit vendor show` — view vendor profile
- `bandit vendor edit` — update intake answers
- `bandit vendor list` — list all vendors with risk tier, score, next due, intake status
- `bandit vendor list --due` — vendors due for reassessment only
- `bandit vendor list --risk HIGH/MEDIUM/LOW`

**Tech Stack**
- `bandit setup --stack` — collect your actual internal tools by category
- Industry-specific categories based on org profile
- Used in vendor intake Q6 to show real system names

**IT Notification Queue**
- `bandit setup --notify` — configure IT contact
- Notifications queued after vendor intake
- IT actions generated per integration category
- Sending enabled in v1.4

**Assessment History**
- Every `bandit assess` writes result to vendor profile
- Stores date, risk tier, score, scope, report path, next due date
- Last 10 assessments retained per vendor
- Foundation for v1.4 dashboard and schedule

**Intake Context in Assessments**
- Vendor profile loaded at start of every assess
- Integration context paragraph injected into extraction prompts
- Weight modifiers applied from intake data types and integrations
- Double-counting prevention vs org profile weights
- Admin access triggers D2 weight increase

**Google Drive Profile Sync**
- Vendor profiles sync to Drive when configured
- `bandit vendor add` checks for existing folder before offering to create one
- Fuzzy folder matching with user confirmation
- Profile stored as `.vendor-profiles.json` in root
- Local cache always maintained as fallback
- Sync failures never block assessment

---

## [1.2.0] — 2026-04-02

### Added

**Legal Bandit — Contract Gap Analysis**
- New agent: `core/agents/legal_bandit.py`
- Full GDPR Art. 28(3)(a)-(h) checklist against DPA
- Verbatim quote extraction per provision
- Vague language detection ("appropriate measures" etc)
- Policy/contract conflict detection
- Contract-based score updates for D2, D5, D7, D8
- MSA commercial data protection term assessment
- SCC version and completeness check
- Outdated SCC detection (pre-2021)

**Legal Redline Brief**
- New report: `core/reports/legal_report.py`
- Standalone HTML brief for legal team
- Required / Recommended / Acceptable sections
- Current contract language verbatim per provision
- Specific redline replacement language
- Enforcement precedents per gap
- Policy/contract conflict section
- MSA commercial terms summary
- Disclaimer (not legal advice)

**CLI**
- `bandit assess` now runs Legal Bandit automatically when DPA or MSA documents are available
- `bandit legal` command for standalone legal assessment
- `--no-legal-brief` flag to skip brief generation
- Terminal shows contract findings and score changes after assessment
- Score changes shown: `D5 1→4 ↑ Contract`

**Reports**
- Main report enriched with contract language per dimension
- Score source shown (Policy / Contract) in dimension headers
- Conflict banner when policy/DPA conflicts detected
- For Legal panel updated with brief summary

## [Unreleased]

---

## [1.1.0] — 2026-03-30

### Added

**Document Sources**
- Local folder support — `bandit assess --docs <path>`
- Google Drive integration — `bandit assess --drive`
- `bandit setup --drive` wizard for Drive configuration
- `--docs-root` flag for batch mode auto-matching
- `--drive` flag for batch mode Drive documents

**Document Pipeline**
- PDF text extraction via pdfplumber
- Word document extraction via python-docx (paragraphs and tables)
- JSON flattening for model cards
- Scanned PDF detection with clear error message

**Document Classification**
- 47 document types with DocumentType enum
- 3-pass classification: filename → content keywords → AI
- Confidence scoring per classification

**Type-specific Extraction**
- Dedicated extraction prompts for all document types
- DPA: full GDPR Art. 28(3)(a)-(h) checklist
- BAA: HIPAA §164.504 provisions
- SOC 2: trust service criteria, exceptions, attestations
- AI Policy: training data, opt-out, EU AI Act
- Model Card: training sources, personal data usage
- And more for all 47 document types

**Multi-document Assessment**
- Signal merging across public policy and documents
- Source attribution per signal in HTML report
- Stronger commitment wins when documents conflict
- Assessment scope updated (public_policy_only → policy_and_documents)

**D8 Now Fully Assessable**
- DPA upload enables full Art. 28 scoring
- D2/D4/D5 upgraded from partial to complete scoring when DPA is provided

**Google Drive**
- OAuth 2.0 authentication with token refresh
- Vendor folder auto-discovery by name
- File download with MIME type filtering
- Google Docs exported as DOCX automatically
- Reports saved back to Drive vendor folder
- `auto_save_reports` config option

**HTML Report**
- Documents assessed section in report header
- Signal source attribution per dimension
- Required documents flagged when missing
- Assessment scope label updated

**Dependencies**
- pdfplumber>=0.10.0 (core)
- python-docx>=1.0.0 (core)
- pyyaml>=6.0.0 (core)
- google-auth family (optional `[drive]` extra)

### Fixed
- Assessment no longer penalises D8 as Absent when no DPA exists — correctly shows Requires DPA

---

## 2026-03-29 (latest)

### Added — `(this session)`

#### Setup wizard — inference-based, 5+3 questions
- `bandit setup` completely rewritten: 5 core questions + up to 3 conditional (was 26 questions across 6 sections).
- **Inference engine** — `_infer_frameworks()`, `_infer_weights()`, `_infer_reassessment()`, `_infer_escalation()` derive frameworks, weights, cadence, and escalation triggers automatically from answers.
- **New question flow**: Q1 org type → Q2 locations → Q3 sensitive data → Q4 certifications → Q5 risk approach → [Q6 infra location if EU] → [Q7 BAA if PHI] → [Q8 PCI level if payment card].
- **Review screen** shows inferred profile (frameworks, weights, schedule, escalation) with Y/n/edit choice before writing config.
- **`bandit setup --advanced`** — prints "coming soon" message for future direct weight/cadence editing.

#### New config YAML format
- Config now uses structured sections: `company`, `data_types`, `frameworks`, `risk_appetite`, `reassessment`, `document_requirements`, `dimension_weights`, `auto_escalate`.
- `core/config.py` `get_weights()` and `get_profile_label()` updated to support both new and legacy formats.

#### Vendor function profiling system (`core/profiles/`)
- `core/profiles/vendor_functions.py` — `VendorFunction` enum (14 categories) + `FUNCTION_MODIFIERS` dict with weight deltas and document expectations per function.
- `core/profiles/auto_detect.py` — `VendorAutoDetector` with 4-stage detection: known vendor library → domain match → keyword inference → unknown fallback.
- `core/profiles/vendor_cache.py` — `VendorProfileCache` for persistent profiles in `~/.bandit/vendor-profiles.json` (atomic writes).
- `core/profiles/__init__.py` — package init.

#### BanditConfig class
- `core/config.py`: `BanditConfig` class — structured accessor with `get_weights(vendor_functions=...)`, `get_auto_escalate_triggers()`, `get_reassessment(tier)`, `is_auto_escalate(result)`, `get_frameworks()`, `get_required_documents()`, `get_certifications_required()`.

#### `bandit profile` command
- New `bandit profile <vendor>` command — shows vendor function detection result, confidence, weight modifiers, and document requirements.
- `bandit profile --show` — lists all cached vendor profiles.
- `bandit profile --unknown` — filters for vendors without a confirmed function classification.

#### Evidence confidence scoring
- `PrivacyBandit._calculate_evidence_confidence()` — 0.0–1.0 score based on text length and presence of privacy policy content indicators.
- Auto-detection wired into `bandit assess` — vendor function profiles cached after each assessment.

### Changed — `(this session)`
- `cli/main.py` `setup` command updated to pass `--advanced` flag to `run_wizard()`.
- `cli/welcome.py` — added `bandit profile` to COMMANDS panel.
- README.md, docs/setup-guide.md, docs/cli-reference.md updated to reflect new wizard and profile system.

---

## 2026-03-29 (evening)

### Changed — `3f93763`
- **First-run setup prompt**: `bandit assess` with no config now prompts before starting — `s) Run setup now (recommended)` · `a) Assess anyway` · `q) Quit`. Default is `s`. Choosing setup runs the wizard inline, then continues into the assessment. Previously the tip appeared after the assessment had already run with default weights.
- **Welcome screen**: `bandit setup` added as the first entry in the COMMANDS panel with the label `Configure your profile (run this first)`. Cursor prompt updated to `New? Run bandit setup · Then bandit assess <vendor>`.

### Changed — `0ac0f43`
- `docs/cli-reference.md`: added quick-reference table at the top; added `--force` flag to `bandit assess`; updated setup question count 18 → 26; updated section 6 description; added `vendor-history.json` and `.setup_progress.json` to cache/config files table.

### Docs — `(this commit)`
- `docs/setup-guide.md`: fully rewritten to reflect the current 26-question wizard. Section 6 now documents Q17a/b/c (HIGH), Q18a/b/c (MEDIUM), Q19a/b/c (LOW), and Q26 (maturity). Config YAML example updated to current schema with `reassessment:` block. Valid values table corrected (removed obsolete `reassess_days`, added `reassessment[tier].depth/days/triggers`).
- `README.md`: updated setup description from "2 minutes / 18 questions / shows a tip after" to "5 minutes / prompts before assess starts / inline setup option".

---

## 2026-03-29

### Security — `53e54e6`
- **Atomic file writes** — history, cache, and setup progress files now write to a `.tmp` then atomically rename via `os.replace()`. Previously a crash or concurrent run mid-write could leave a truncated or empty JSON file, silently corrupting vendor history, the domain cache, or setup progress.
- **SSRF prevention** — added `_is_safe_url()` in `core/tools/discover.py` that blocks requests to loopback addresses (`127.x`, `localhost`), RFC-1918 private ranges (`10.x`, `192.168.x`, `172.x`), and cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`). Applied at `head_request()` and `_tiny_get()`, which all network fetches flow through.
- **Exception narrowing** — `_load_history()` and `_load_cache()` changed from bare `except Exception` to `except (OSError, json.JSONDecodeError)`. `_save_cache()` gained a missing `try/except OSError` — previously an unhandled `OSError` (e.g. disk full) would crash an in-progress assessment.

### Removed — `8c0610c`
- Deleted `legacy/` directory (11 files, 2,418 lines) — the original n8n workflow prototype. Superseded entirely by the Bandit CLI. Local backup retained.

### Fixed — `a307d8e`
- `LICENSE`: copyright holder updated from `The Privacy Lens Contributors` to `Bandit Contributors`.
- `legacy/n8n/bandit-privacy.json`: CSS header string `◄ THE PRIVACY LENS ►` updated to `◄ BANDIT ►`.

### Changed — `3b2b3db`
- `bandit setup` section 6 fully rewritten to match spec:
  - `_ask_cadence()` — shows preset options per tier (HIGH: 6 months–2 years, MEDIUM: 1–5 years, LOW: 1 year–never) plus free-text custom day input. Defaults: HIGH=1 year, MEDIUM=2 years, LOW=one-time.
  - `_ask_triggers()` — shows all trigger options with `◉`/`◯` indicating per-tier defaults (HIGH: policy + breach + regulatory; MEDIUM: policy + breach; LOW: breach only). Enter accepts defaults; entering numbers replaces selection entirely; "Manual trigger only" returns empty list.
  - `_days_label()` — converts day counts to human-readable strings (`365` → `Every year`, `912` → `Every ~2 years`, `0` → `One time / on change`).
  - Confirmation screen now shows a reassessment schedule table with human-readable cadence and grouped trigger display.
  - `bandit setup --show` updated with same depth labels and cadence display.

### Added — `4db4088`
- Per-tier reassessment cadence replacing the single `reassess_cycle` setting. For each of HIGH, MEDIUM, LOW: configurable depth (`full` / `lightweight` / `scan` / `none`), cadence in days, and out-of-cycle triggers.
- `core/config.py`: `get_reassessment_config()` returns per-tier config with defaults. `write_config()` accepts `reassessment=` param and writes a top-level `reassessment:` YAML block. `_load_yaml_simple()` extended to handle 3-level nesting.
- `cli/report.py`: GRC section now reads config-driven cadence, shows assessment depth, re-assess date with cadence annotation, and active out-of-cycle triggers.
- `cli/main.py`: `--force` flag. Vendor history persisted to `~/.bandit/vendor-history.json` after each assessment. Cadence check warns and exits early if reassessment is not due; skips entirely for `depth: none`; bypassed with `--force`.

### Added — `ac42d6e`
- Setup wizard progress saved after every question to `~/.bandit/.setup_progress.json`. On next run, wizard offers to resume from last completed question or start over.
- `Ctrl+C` during setup prints `Setup paused at Q{n}/26. Run bandit setup to resume.` instead of crashing.
- `--reset` clears saved progress alongside the config file.

### Fixed — `6665672`
- Setup wizard crash on Q17 when user selected "Annual" or "On-change only" — `int("Annual")` raised `ValueError`. Fixed with index-based option map instead of string parsing. Same pattern applied to `risk_appetite` and `maturity` questions.

### Added — `2f905ca`
- Assessment scope honesty: D8 (DPA Completeness) excluded from the weighted average when only the public privacy policy is available. D2, D4, D5 flagged as partially assessed. Scope bar shown in HTML report header. `--dpa` placeholder flag added to `bandit assess`.

### Added — `f62a335`
- `bandit setup` — 26-question wizard that calculates dimension weights based on regulatory environment and data risk profile. Saves to `bandit.config.yml`. Supports `--reset` and `--show`. Profile label and modified weights displayed in terminal and HTML report header.
- `core/config.py` — `load_config()`, `get_weights()`, `calculate_weights()`, `is_auto_escalate()`, `get_profile_label()`, `write_config()`.

---

## 2026-03-29 (earlier)

### Added — `fcad860`
- v1.0 CLI: `bandit assess`, `bandit rubric`, `bandit batch`. HTML reports saved to `./reports/`. Input auto-detection (company name / domain / URL). `--json`, `--verbose`, `--no-report` flags. Batch mode with `--out` directory and progress bar.

### Added — `6bd00d0`
- Rich welcome screen (`bandit` with no args). `bandit rubric` command with per-dimension detail view (`--dim D5`). Terminal renderer with colour-coded scores, scope indicators, and escalation banners.

### Added — `f8849cb`
- HTML report: sources footer, matched signals per dimension, per-dimension detail sections with evidence, gaps, red flags, contract recommendations, team summary panels (GRC / Legal / Security), vendor email template.

---

## 2026-03-28

### Added — `d860d5ef`
- Privacy Bandit agent — full LLM → extract → score pipeline. Anthropic Claude integration via `AnthropicProvider`. 8-dimension rubric scoring engine with red flags, signal matching, and weighted average.

### Added — `4243769`
- Auto-load `config.env` for `ANTHROPIC_API_KEY` — no export required.

### Fixed — `3e3e7ab`
- JS-rendered page fallback via Jina Reader when direct fetch returns insufficient content.

---

## 2026-03-27

### Added — `a46e5dc`
- v1.0 architecture: Python agent core, staged discovery engine (DuckDuckGo → HEAD probe → AI fallback → homepage scrape), rubric engine, Click CLI scaffold, Rich terminal output.

---

## 2026-03-26

### Changed — `b6d84ab`
- Project renamed from **The Privacy Lens** to **Bandit** across all files, docs, and workflows.

### Added — `10640aa`
- Landing page (`docs/index.html`) deployed to GitHub Pages. `CLAUDE.md` deploy instructions.
