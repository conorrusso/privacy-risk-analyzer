# Bandit — Claude Code Deployment Guide

This file tells Claude Code how to deploy the Bandit landing page to GitHub Pages.

---

## Context

- **Repo**: `~/projects/bandit/`
- **Deploy script**: `~/projects/bandit/deploy-docs.sh`
- **GitHub Pages source**: `/docs` folder on `main` branch
- **Live URL**: `https://conorrusso.github.io/bandit/`

---

## Deploy the landing page

```bash
cd ~/projects/bandit
bash deploy-docs.sh "docs: update landing page"
```

The script will show a diff, ask for confirmation, then commit and push.

---

## Update landing page content

The landing page is a single self-contained file — no build step, no dependencies:

```
docs/index.html
```

Edit it directly, then run `deploy-docs.sh` to publish.

---

## Future crew pages

When Legal Bandit, AI Bandit etc. are ready, add sub-pages:

```
docs/
  index.html            ← main landing (current)
  privacy/index.html    ← Privacy Bandit detail page
  legal/index.html      ← Legal Bandit detail page
  ai/index.html         ← AI Bandit detail page
  audit/index.html      ← Audit Bandit detail page
  data/index.html       ← Data Bandit detail page
```

Update the crew card links in `index.html` to point to these sub-pages once they exist.

---

## Custom domain (optional)

To use a custom domain like `bandit.tools`:
1. Add a `CNAME` file to `docs/` containing just the domain: `bandit.tools`
2. Point your DNS A records to GitHub Pages IPs (185.199.108-111.153)
3. Enable "Enforce HTTPS" in GitHub Pages settings once DNS propagates

---

## Design tokens (for landing page edits)

Key CSS variables in `docs/index.html`:
- `--cream: #F4EFE4` — primary background
- `--brown: #8B5A2B` — accent colour, live badge, collar
- `--ink: #1A1510` — headings and nav bar
- Dot grid: `radial-gradient(circle, #B8AA90 1.2px, transparent 1.2px)` / `22px 22px`
- Cave-to-cream fade: `linear-gradient(#F4EFE4 0%, transparent 100%)` on `::before`
