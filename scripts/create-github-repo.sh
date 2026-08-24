#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required. Install with: sudo apt install git"
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required. Install with: sudo apt install gh"
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "Log in to GitHub first: gh auth login"
  exit 1
fi

if [[ ! -d .git ]]; then
  git init
  git branch -M main
fi

git add .
git commit -m "$(cat <<'EOF'
Initial Rasputinfy release.

Retro now-playing display for Raspotify with demo mode, synthwave UI, and Pi kiosk support.
EOF
)" || true

gh repo create rasputinfy --private --source=. --remote=origin --push

echo
echo "Private repo created and pushed:"
gh repo view --web 2>/dev/null || gh repo view
