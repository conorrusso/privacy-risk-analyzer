# Contributing to Bandit

Thank you for your interest in contributing. Bandit welcomes contributions from privacy professionals, compliance engineers, and developers.

---

## Ways to contribute

### Rubric improvements (`core/scoring/rubric.py`)

The most impactful contributions — no AI expertise needed. Areas of interest:

- Additional regulatory coverage (LGPD, PIPL, POPIA, PIPEDA, UK GDPR)
- New red-flag phrases backed by enforcement actions or regulatory guidance
- Signal calibration improvements based on real-world assessments
- New scoring levels or adjusted weights with documented rationale

### Provider adapters (`core/llm/`)

Add a new LLM provider:

1. Subclass `BaseLLMProvider` in `core/llm/base.py`
2. Implement `complete_json(prompt, max_tokens) -> dict`
3. Add the provider to the `--provider` option in `cli/main.py`

All providers must return a JSON object matching the extraction schema. Test with both a high-risk and low-risk example before submitting.

### New agent implementations (`core/agents/`)

The crew is modular — each Bandit is a subclass of `BaseBandit`. To implement a new agent:

1. Subclass `BaseBandit` in `core/agents/`
2. Implement `assess(vendor) -> PrivacyAssessment` (or a compatible return type)
3. Add a CLI command in `cli/main.py`

Planned agents: Legal Bandit (MSA/DPA), AI Bandit (EU AI Act), Audit Bandit (SOC 2 / ISO 27001), Data Bandit (flow mapping).

### Discovery improvements (`core/tools/discover.py`)

- Improve the DDG search query construction
- Add new common privacy path patterns to `_PRIVACY_PATHS`
- Improve the AI-reasoning fallback prompt
- Improve homepage link scraping logic

### Bug reports

Open an issue for:

- Inaccurate regulatory citations
- Scoring logic errors
- Incorrect signal extraction
- Discovery failures for specific vendors (include the vendor name and what URL was found)
- HTML report rendering issues

---

## Contribution process

1. **Fork** the repository
2. **Create a branch:** `git checkout -b feature/your-feature-name`
3. **Make your changes** following the style guide below
4. **Test** with at least one live vendor assessment
5. **Submit a Pull Request** with a clear description

PR title format: `type: short description` where type is one of `feat`, `fix`, `rubric`, `docs`, `refactor`.

Examples:
- `rubric: add PIPL signals for D3 and D4`
- `feat: add Gemini provider adapter`
- `fix: handle JS-rendered pages in discover fallback`

---

## Style guide

### Python

- Match the existing code style (no formatter enforced — just be consistent)
- Type annotations on all public functions and methods
- Docstrings on public classes and methods
- No external dependencies without discussion — the CLI should stay lightweight

### Rubric signals

- Signal keys follow the pattern `d{N}_{slug}` (e.g., `d1_purpose_limitation`)
- Each signal maps to exactly one dimension
- Required signals for a level must be verifiable from policy text alone
- Add enforcement citations where available

### Regulatory citations

- GDPR: `GDPR Art. X` or `GDPR Art. X(Y)(z)`
- CCPA/CPRA: `CCPA §1798.XXX`
- EU AI Act: `EU AI Act 2024 Art. X`
- Include the article's short title where helpful

### Documentation

- Use sentence case for headings
- Include a Prerequisites section in setup guides
- Do not include screenshots (they go stale; use text instructions)

---

## Rubric versioning

The scoring rubric follows semantic versioning:

- **Patch** (1.0.x): Clarifications, wording improvements, no scoring changes
- **Minor** (1.x.0): New signals or sub-criteria added
- **Major** (x.0.0): Scale changes, dimension additions/removals, weight changes

Breaking changes must be documented in `CHANGELOG.md`.

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold these standards.

---

## Legal

By contributing, you agree that your contributions will be licensed under the MIT License. Do not contribute content you do not have the right to license.

Example files should use fictional vendor names — do not include real privacy policy text from real companies.
