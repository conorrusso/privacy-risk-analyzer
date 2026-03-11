#!/bin/bash

# deploy-docs.sh
# Usage: ./deploy-docs.sh "your commit message here"
# Copies updated files from ~/Downloads into the repo, shows a diff, and commits + pushes.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
DOWNLOADS=~/Downloads

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m'

if [ -z "$1" ]; then
  echo -e "${RED}Error: Please provide a commit message.${NC}"
  echo -e "Usage: ${CYAN}./deploy-docs.sh \"your commit message here\"${NC}"
  exit 1
fi

COMMIT_MSG="$1"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  The Privacy Lens — Deploy Docs${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

declare -A FILES=(
  ["README.md"]="README.md"
  ["index.html"]="docs/index.html"
  ["n8n-setup.md"]="integrations/n8n-setup.md"
  ["google-drive-setup.md"]="integrations/google-drive-setup.md"
  ["docker-compose.yml"]="docker-compose.yml"
  ["privacy-policy-analyzer.json"]="workflows/privacy-policy-analyzer.json"
  ["dpa-gap-checker.json"]="workflows/dpa-gap-checker.json"
  ["ai-vendor-assessment.json"]="workflows/ai-vendor-assessment.json"
  ["PT-1-privacy-policy-analysis.md"]="prompts/PT-1-privacy-policy-analysis.md"
  ["privacy-risk-scoring-rubric.md"]="frameworks/privacy-risk-scoring-rubric.md"
)

COPIED=0
echo ""
echo -e "${YELLOW}Checking Downloads for updated files...${NC}"

for FILENAME in "${!FILES[@]}"; do
  SRC="$DOWNLOADS/$FILENAME"
  DEST="$REPO_DIR/${FILES[$FILENAME]}"
  if [ -f "$SRC" ]; then
    cp "$SRC" "$DEST"
    echo -e "  ${GREEN}✓${NC} Copied $FILENAME → ${FILES[$FILENAME]}"
    COPIED=$((COPIED + 1))
  fi
done

if [ "$COPIED" -eq 0 ]; then
  echo -e "${YELLOW}No matching files found in ~/Downloads. Nothing to copy.${NC}"
  exit 0
fi

echo ""
echo -e "${YELLOW}$COPIED file(s) copied.${NC}"

cd "$REPO_DIR"

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Git diff (changes to be committed):${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

git diff --stat

echo ""
echo -e "${YELLOW}Commit message:${NC} $COMMIT_MSG"
echo ""
read -p "$(echo -e ${CYAN}"Proceed with commit and push? (y/n): "${NC})" CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo -e "${YELLOW}Aborted. Files were copied but not committed.${NC}"
  exit 0
fi

echo ""
git add .
git commit -m "$COMMIT_MSG"
git push

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✓ Done! Last 3 commits:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
git log --oneline -3
