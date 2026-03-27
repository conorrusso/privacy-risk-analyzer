# Bandit — Landing Page Setup for Claude Code

This file tells Claude Code exactly what to do to get the Bandit landing page
live on GitHub Pages. Follow these steps in order.

---

## Context

- **Repo**: `~/projects/privacy-risk-analyzer/` (rename target: `bandit`)
- **Deploy script**: `~/projects/privacy-risk-analyzer/deploy-docs.sh`
- **GitHub Pages source**: the `/docs` folder on the `main` branch
- **Landing page file**: `index.html` (in this same directory)

---

## Tasks

### 1. Rename the repo (optional but recommended)

On GitHub, go to Settings → rename `privacy-risk-analyzer` → `bandit`.
GitHub will auto-redirect the old URL. Update the two placeholder URLs in
`index.html` once the rename is done (search for `privacy-risk-analyzer`).

### 2. Create the docs folder and copy the landing page

```bash
cd ~/projects/privacy-risk-analyzer
mkdir -p docs
cp /path/to/this/index.html docs/index.html
```

Replace `/path/to/this/index.html` with wherever Claude Code saved this file.

### 3. Check or create deploy-docs.sh

If `deploy-docs.sh` doesn't exist yet, create it:

```bash
cat > ~/projects/privacy-risk-analyzer/deploy-docs.sh << 'EOF'
#!/usr/bin/env bash
set -e
REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_ROOT"
echo "→ Staging docs/"
git add docs/
git commit -m "docs: update landing page" || echo "Nothing to commit"
git push origin main
echo "✓ Pushed. GitHub Pages will update at:"
echo "  https://conorrusso.github.io/bandit/"
echo "  (or your custom domain if configured)"
EOF
chmod +x ~/projects/privacy-risk-analyzer/deploy-docs.sh
```

If `deploy-docs.sh` already exists, open it and make sure it at minimum runs:
```bash
git add docs/
git commit -m "docs: update landing page"
git push origin main
```

### 4. Enable GitHub Pages

In the GitHub repo → Settings → Pages:
- Source: **Deploy from a branch**
- Branch: `main`
- Folder: `/docs`
- Save

### 5. Deploy

```bash
cd ~/projects/privacy-risk-analyzer
bash deploy-docs.sh
```

### 6. Update placeholder URLs in index.html

Search `index.html` for these two strings and update them after the repo rename:

| Find | Replace with |
|------|-------------|
| `conorrusso/privacy-risk-analyzer` | `conorrusso/bandit` |
| `github.com/conorrusso/bandit` | confirmed final URL |

Then re-run `deploy-docs.sh`.

### 7. Verify

Visit `https://conorrusso.github.io/bandit/` — allow ~60 seconds for
GitHub Pages to build after the first push.

---

## Future crew pages

When Legal Bandit, AI Bandit etc. are ready, add sub-pages:

```
docs/
  index.html          ← main landing (this file)
  privacy/index.html  ← Privacy Bandit detail page
  legal/index.html    ← Legal Bandit detail page
  ai/index.html       ← AI Bandit detail page
  audit/index.html    ← Audit Bandit detail page
  data/index.html     ← Data Bandit detail page
```

Update the crew card links in `index.html` to point to these sub-pages
once they exist.

---

## Custom domain (optional)

To use `bandit.tools` or similar:
1. Add a `CNAME` file to `docs/` containing just the domain: `bandit.tools`
2. Point your DNS A records to GitHub Pages IPs (185.199.108-111.153)
3. Enable "Enforce HTTPS" in GitHub Pages settings once DNS propagates

---

## Design notes for future edits

The landing page is a single self-contained HTML file — no build step, no
dependencies, no npm. Everything is inline CSS and inline SVG.

Key design tokens (all in the `<style>` block):
- `--cream: #F4EFE4` — primary background
- `--brown: #8B5A2B` — accent / live badge / collar
- `--ink: #1A1510` — headings and nav bar
- Dot grid hero: `radial-gradient(circle, #B8AA90 1.2px, transparent 1.2px)`
  with `background-size: 22px 22px`

The cave footer scene and rooftop hero are pure SVG pixel art — edit the
`<rect>` elements directly to adjust colours, positions or add new elements.
