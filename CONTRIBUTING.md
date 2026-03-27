# Contributing to Bandit

Thank you for your interest in contributing. This project welcomes contributions from privacy professionals, compliance engineers, and developers.

---

## Ways to Contribute

### Prompt Improvements (`/prompts/`)
The most impactful contributions are improvements to the scoring prompt (PB-1). Areas of interest:
- Additional regulatory coverage (LGPD, PIPL, POPIA, PIPEDA)
- Improved scoring rubric calibration based on real-world assessments
- New prompt templates (PB-2, PB-3) for specific contexts (healthcare, fintech, HR tech)

### New Workflows (`/workflows/`)
Workflow contributions for new use cases:
- Cookie notice analyzer
- Privacy notice change detector (diff workflow)
- Vendor re-assessment on policy update (triggered by web scraper)
- RoPA (Record of Processing Activities) builder

### Framework Updates (`/frameworks/`)
- Rubric versioning and calibration improvements
- New regulatory frameworks (add as separate files, e.g., `lgpd-scoring-rubric.md`)

### Integration Guides (`/integrations/`)
Setup guides for additional integrations:
- Notion
- Monday.com
- ServiceNow
- Microsoft Teams
- Confluence

### Bug Reports & Feedback
Open an issue for:
- Inaccurate regulatory citations
- Scoring logic errors
- Workflow JSON import failures
- Documentation gaps

---

## Contribution Process

1. **Fork** the repository
2. **Create a branch:** `git checkout -b feature/your-feature-name`
3. **Make your changes** following the style guides below
4. **Test your changes** (for workflows: test import and execution in n8n)
5. **Submit a Pull Request** with a clear description

---

## Style Guide

### Prompt Templates
- Use the `PT-N` naming convention (PB-2, PB-3, etc.)
- Include metadata header (version, models tested, regulatory coverage)
- All prompts must work with at least 2 different AI providers
- JSON output format must be documented in the prompt file itself
- Test with both high-risk and low-risk examples before submitting

### Workflow JSON Files
- Include a `_meta` block with `name`, `description`, `version`, `status`
- Include `_setup_instructions` array
- Node IDs should be descriptive strings (not UUIDs)
- Add a `notes` field to every node explaining its purpose
- Mark all credential-dependent nodes clearly

### Documentation
- Use sentence case for headings
- Include a Prerequisites section in all setup guides
- Include a Troubleshooting table with common errors and solutions
- Link to relevant regulatory articles when citing compliance requirements
- Do not include screenshots (they become outdated; use text instructions instead)

### Regulatory Citations
- GDPR: cite as `GDPR Art. X` or `GDPR Art. X(Y)(z)`
- CCPA: cite as `CCPA §1798.XXX`
- EU AI Act: cite as `EU AI Act 2024 Art. X` or `EU AI Act Annex X`
- Include the short title of the article where helpful (e.g., "GDPR Art. 17 (right to erasure)")

---

## Rubric Versioning

The scoring rubric follows semantic versioning:
- **Patch** (1.0.x): Clarifications, wording improvements, no scoring changes
- **Minor** (1.x.0): New sub-criteria or evidence questions added
- **Major** (x.0.0): Scoring scale changes, dimension additions/removals, weight changes

Breaking changes to scoring criteria must be documented in a `CHANGELOG.md` entry.

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold these standards.

---

## Legal

By contributing, you agree that your contributions will be licensed under the MIT License. Do not contribute content you do not have the right to license.

Contributions should not include real vendor names or actual privacy policy text from real companies in example files. Use fictional vendor names (as in the `/examples/` folder).
