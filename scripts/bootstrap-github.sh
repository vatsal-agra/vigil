#!/usr/bin/env bash
#
#   Vigil — one-shot GitHub setup
#
# Pushes the code, creates the labels, the 25 issues, the project board with
# MoSCoW / Epic / Points fields, and a feature branch.
#
# Prerequisites:
#   gh auth login                              # once
#   gh auth refresh -s project,read:project    # Projects v2 needs this scope
#   jq installed
#
# Run from the repo root:
#   ./scripts/bootstrap-github.sh

set -euo pipefail

REMOTE="https://github.com/vatsal-agra/vigil.git"
FEATURE_BRANCH="feat/us-16-public-status-page"

bold() { printf '\n\033[1m%s\033[0m\n' "$1"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }

# ---------------------------------------------------------------- preflight

bold "Preflight"

command -v git >/dev/null || { echo "git not found"; exit 1; }
ok "git"

command -v gh >/dev/null || {
  echo "GitHub CLI not found. Install it: https://cli.github.com"; exit 1; }
ok "gh"

command -v jq >/dev/null || {
  echo "jq not found. macOS: brew install jq · Ubuntu: sudo apt install jq"; exit 1; }
ok "jq"

gh auth status >/dev/null 2>&1 || { echo "Not signed in. Run: gh auth login"; exit 1; }
ok "gh authenticated as $(gh api user -q .login)"

if ! gh auth status 2>&1 | grep -q "project"; then
  warn "The 'project' scope is missing — the board step will fail."
  warn "Fix with: gh auth refresh -s project,read:project"
  read -rp "  Continue anyway? [y/N] " reply
  [[ "$reply" == [yY] ]] || exit 1
fi

git config user.name  >/dev/null || { echo "Set: git config --global user.name  \"Your Name\""; exit 1; }
git config user.email >/dev/null || { echo "Set: git config --global user.email \"you@example.com\""; exit 1; }
ok "git identity: $(git config user.name) <$(git config user.email)>"

# ---------------------------------------------------------------- push

bold "Pushing code"

if [[ ! -d .git ]]; then
  git init -q
  ok "initialised repository"
fi

git symbolic-ref HEAD refs/heads/main 2>/dev/null || git branch -M main
git remote get-url origin >/dev/null 2>&1 || git remote add origin "$REMOTE"
ok "remote: $(git remote get-url origin)"

if git rev-parse HEAD >/dev/null 2>&1; then
  ok "commits already exist, skipping initial commit"
else
  git add -A
  git commit -q -m "feat: initial commit — Vigil monitoring platform

Vision document, 25-story backlog, six wireframes, architecture diagram,
and a working five-container stack (Next.js, FastAPI, probe worker,
PostgreSQL, Redis) that runs with a single docker compose up."
  ok "initial commit created"
fi

git push -u origin main
ok "pushed main"

# ---------------------------------------------------------------- backlog

bold "Labels and issues"
./scripts/seed-issues.sh

bold "Project board"
./scripts/setup-project-board.sh || warn "Board step failed — check the 'project' scope."

# ---------------------------------------------------------------- branch

bold "Feature branch"

if git show-ref --verify --quiet "refs/heads/$FEATURE_BRANCH"; then
  ok "$FEATURE_BRANCH already exists locally"
else
  git switch -c "$FEATURE_BRANCH" -q
  ok "created $FEATURE_BRANCH"
fi

git push -u origin "$FEATURE_BRANCH"
ok "pushed $FEATURE_BRANCH"
git switch main -q

# ---------------------------------------------------------------- protection

bold "Branch protection (optional)"

if gh api -X PUT "repos/$(gh repo view --json nameWithOwner -q .nameWithOwner)/branches/main/protection" \
     -H "Accept: application/vnd.github+json" \
     -F "required_status_checks[strict]=true" \
     -f "required_status_checks[contexts][]=Backend — tests" \
     -f "required_status_checks[contexts][]=Frontend — build" \
     -F "enforce_admins=false" \
     -F "required_pull_request_reviews[required_approving_review_count]=0" \
     -F "restrictions=" >/dev/null 2>&1; then
  ok "main protected — PRs must pass CI"
else
  warn "Could not set branch protection (needs a public repo or GitHub Pro)."
  warn "Not required for the assignment — mention GitHub Flow in the README instead."
fi

# ---------------------------------------------------------------- done

REPO_URL="https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)"

bold "Done"
cat <<EOF

  Repo       $REPO_URL
  Branches   $REPO_URL/branches
  Issues     $REPO_URL/issues
  Actions    $REPO_URL/actions
  Projects   $(gh api user -q '"https://github.com/users/" + .login + "/projects"')

Next:

  1. docker compose up --build
  2. Work through docs/screenshots/README.md
  3. Open a PR from $FEATURE_BRANCH so you have one with CI green

EOF
