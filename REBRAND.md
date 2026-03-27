# Rebrand Task — Apply to Repo

This file tells Claude Code exactly what to do to apply the full Bandit rebrand.
Run this once, then delete this file.

---

## What Changed

Every file in the repo has been updated from "The Privacy Lens / Privacy Risk Analyzer"
naming to the new Bandit brand. Here's the full mapping:

| Old | New |
|-----|-----|
| `The Privacy Lens` | `Bandit` |
| `Privacy Risk Analyzer` | `Bandit — Vendor Risk Intelligence Suite` |
| `privacy-risk-analyzer` (repo/dir) | `bandit` |
| `PT-1` (prompt template ID) | `PB-1` |
| `Privacy Risk Score (PRS)` | `Bandit Risk Score (BRS)` |
| `privacy-policy-analyzer.json` | `bandit-privacy.json` |
| `Jira - Privacy Lens` | `Jira - Bandit` |
| `Slack - Privacy Lens` | `Slack - Bandit` |
| `Google Drive - Privacy Lens` | `Google Drive - Bandit` |
| `TOKEN=privacy-lens` | `TOKEN=bandit` |

---

## Steps for Claude Code

### 1. Copy all updated files into the repo

The updated files are provided alongside this task file. Copy them all into the
repo, overwriting the originals:

```bash
# From wherever these files were dropped:
cp -r . ~/projects/bandit/
```

### 2. Handle the two renamed files

Two files have been renamed. Delete the old names and keep the new ones:

```bash
cd ~/projects/bandit

# Prompt template renamed
git rm prompts/PT-1-privacy-policy-analysis.md
git add prompts/PB-1-privacy-policy-analysis.md

# Workflow renamed
git rm workflows/privacy-policy-analyzer.json
git add workflows/bandit-privacy.json
```

### 3. Stage and commit everything

```bash
cd ~/projects/bandit
git add -A
git commit -m "rebrand: rename project to Bandit across all docs and workflows"
git push origin main
```

### 4. Delete this file

```bash
rm ~/projects/bandit/REBRAND.md
git add -A
git commit -m "chore: remove rebrand task file"
git push origin main
```

### 5. Verify

Check that none of these strings remain anywhere in the repo:

```bash
grep -r "Privacy Lens\|privacy-risk-analyzer\|PT-1\b\|Privacy Risk Analyzer" \
  ~/projects/bandit \
  --include="*.md" --include="*.json" --include="*.sh" --include="*.html" \
  | grep -v ".git/"
```

Should return nothing.

---

## Note on Docker token

The Browserless token in `docker-compose.yml` has been updated from
`privacy-lens` to `bandit`. If you have a running Docker Compose stack,
restart it after pulling:

```bash
docker compose down
docker compose up -d
```
