#!/bin/bash

# deploy-docs.sh
# Usage: ./deploy-docs.sh "your commit message here"
# Reviews uncommitted changes in the repo, then commits and pushes.
# Edit or place files directly in the repo before running this script.

set -e

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"

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

cd "$REPO_DIR"

echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Bandit — Deploy${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

echo ""
echo -e "${YELLOW}Changed files:${NC}"
git status --short

if [ -z "$(git status --short)" ]; then
  echo -e "${YELLOW}Nothing to commit. Working tree is clean.${NC}"
  exit 0
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${CYAN}  Diff summary:${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
git diff --stat

echo ""
echo -e "${YELLOW}Commit message:${NC} $COMMIT_MSG"
echo ""
read -p "$(echo -e ${CYAN}"Proceed with commit and push? (y/n): "${NC})" CONFIRM

if [[ "$CONFIRM" != "y" && "$CONFIRM" != "Y" ]]; then
  echo -e "${YELLOW}Aborted. No changes committed.${NC}"
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
