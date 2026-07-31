#!/usr/bin/env bash
#
# Creates the 15 labels and the 25 user-story issues.
#
# Safe to re-run: labels are upserted, issues are skipped if the title exists.
# Called by bootstrap-github.sh, but works standalone too.

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=stories.sh
source "$HERE/stories.sh"

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
echo "Repository: $REPO"

# ---------------------------------------------------------------- labels

upsert_label() {
  gh label create "$1" --color "$2" --description "$3" --force >/dev/null
  printf '  label  %s\n' "$1"
}

echo
echo "Labels"
upsert_label "epic:accounts"  "5B6BFF" "Sign-up, sign-in, session, isolation"
upsert_label "epic:monitors"  "3FD69C" "Creating and viewing monitors"
upsert_label "epic:engine"    "F0B429" "Probe worker and incident detection"
upsert_label "epic:status"    "C77DFF" "Public status page"
upsert_label "epic:alerting"  "FF8A3D" "Email, Slack, summaries"
upsert_label "epic:ops"       "7B8CA8" "Docker, CI, deployment"
upsert_label "must-have"      "D2405A" "MoSCoW: Must"
upsert_label "should-have"    "E8A33D" "MoSCoW: Should"
upsert_label "could-have"     "6BAED6" "MoSCoW: Could"
upsert_label "wont-have"      "C3C9D2" "MoSCoW: Won't (this release)"
upsert_label "backend"        "0F6B4A" "FastAPI / SQLAlchemy"
upsert_label "frontend"       "1F4FA8" "Next.js / React"
upsert_label "devops"         "444C58" "Containers and infrastructure"
upsert_label "security"       "8B0000" "Authentication and authorisation"
upsert_label "ci"             "555555" "GitHub Actions"

# ---------------------------------------------------------------- issues

echo
echo "Issues"
existing="$(gh issue list --limit 200 --state all --json title -q '.[].title')"
created=0
skipped=0

for record in "${STORIES[@]}"; do
  IFS='|' read -r id title labels points story criteria <<<"$record"
  full_title="$id · $title"

  if grep -Fxq "$full_title" <<<"$existing"; then
    printf '  skip   %s\n' "$full_title"
    skipped=$((skipped + 1))
    continue
  fi

  body="## User story

$story

## Acceptance criteria

$(echo "$criteria" | sed 's/ ;; /\n/g' | sed 's/^/- [ ] /')

## Estimate

\`$points\` story points

---
<sub>Seeded from \`docs/user-stories.md\` by \`scripts/seed-issues.sh\`.</sub>"

  gh issue create --title "$full_title" --body "$body" --label "$labels" >/dev/null
  printf '  issue  %s\n' "$full_title"
  created=$((created + 1))
done

echo
echo "Done. $created created, $skipped already existed."
