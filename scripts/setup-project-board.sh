#!/usr/bin/env bash
#
# Builds the GitHub Project (v2) board: creates it, adds MoSCoW / Points / Epic
# fields, adds all 25 issues, and sets every field value from the labels.
#
# Requires the 'project' scope:
#   gh auth refresh -s project,read:project
#
# Safe to re-run: an existing project with the same title is reused.

set -euo pipefail

command -v jq >/dev/null || { echo "jq is required. brew install jq / apt install jq"; exit 1; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=stories.sh
source "$HERE/stories.sh"

REPO="$(gh repo view --json nameWithOwner -q .nameWithOwner)"
OWNER="${REPO%%/*}"
TITLE="Vigil — Product Backlog"

echo "Repository: $REPO"
echo "Owner:      $OWNER"

# ---------------------------------------------------------------- project

number="$(gh project list --owner "$OWNER" --format json \
  | jq -r --arg t "$TITLE" '.projects[] | select(.title == $t) | .number' | head -1)"

if [[ -z "$number" ]]; then
  echo
  echo "Creating project…"
  number="$(gh project create --owner "$OWNER" --title "$TITLE" --format json | jq -r '.number')"
  echo "  created project #$number"
else
  echo "  reusing existing project #$number"
fi

project_id="$(gh project view "$number" --owner "$OWNER" --format json | jq -r '.id')"

# ---------------------------------------------------------------- fields

field_id() {
  gh project field-list "$number" --owner "$OWNER" --limit 50 --format json \
    | jq -r --arg n "$1" '.fields[] | select(.name == $n) | .id' | head -1
}

ensure_select_field() {
  local name="$1" opts="$2"
  if [[ -z "$(field_id "$name")" ]]; then
    gh project field-create "$number" --owner "$OWNER" --name "$name" \
      --data-type SINGLE_SELECT --single-select-options "$opts" >/dev/null
    printf '  field  %s\n' "$name"
  else
    printf '  field  %s (exists)\n' "$name"
  fi
}

echo
echo "Fields"
ensure_select_field "MoSCoW" "Must,Should,Could,Won't"
ensure_select_field "Epic" "Accounts,Monitors,Engine,Status,Alerting,Ops"

if [[ -z "$(field_id "Points")" ]]; then
  gh project field-create "$number" --owner "$OWNER" --name "Points" \
    --data-type NUMBER >/dev/null
  echo "  field  Points"
else
  echo "  field  Points (exists)"
fi

moscow_field="$(field_id "MoSCoW")"
epic_field="$(field_id "Epic")"
points_field="$(field_id "Points")"

fields_json="$(gh project field-list "$number" --owner "$OWNER" --limit 50 --format json)"

option_id() {  # option_id <field-name> <option-name>
  jq -r --arg f "$1" --arg o "$2" \
    '.fields[] | select(.name == $f) | .options[]? | select(.name == $o) | .id' \
    <<<"$fields_json" | head -1
}

# ---------------------------------------------------------------- map labels

moscow_for() {
  case "$1" in
    *must-have*)   echo "Must"   ;;
    *should-have*) echo "Should" ;;
    *could-have*)  echo "Could"  ;;
    *wont-have*)   echo "Won't"  ;;
  esac
}

epic_for() {
  case "$1" in
    *epic:accounts*) echo "Accounts" ;;
    *epic:monitors*) echo "Monitors" ;;
    *epic:engine*)   echo "Engine"   ;;
    *epic:status*)   echo "Status"   ;;
    *epic:alerting*) echo "Alerting" ;;
    *epic:ops*)      echo "Ops"      ;;
  esac
}

# ---------------------------------------------------------------- items

echo
echo "Adding issues to the board"

existing_items="$(gh project item-list "$number" --owner "$OWNER" --limit 200 --format json)"

for record in "${STORIES[@]}"; do
  IFS='|' read -r id title labels points _story _criteria <<<"$record"
  full_title="$id · $title"

  issue_num="$(gh issue list --limit 200 --state all --search "$id in:title" \
    --json number,title -q ".[] | select(.title == \"$full_title\") | .number" | head -1)"

  if [[ -z "$issue_num" ]]; then
    printf '  MISS   %s (no matching issue — run seed-issues.sh first)\n' "$full_title"
    continue
  fi

  item_id="$(jq -r --arg t "$full_title" \
    '.items[] | select(.content.title == $t) | .id' <<<"$existing_items" | head -1)"

  if [[ -z "$item_id" ]]; then
    item_id="$(gh project item-add "$number" --owner "$OWNER" \
      --url "https://github.com/$REPO/issues/$issue_num" --format json | jq -r '.id')"
  fi

  m="$(moscow_for "$labels")"
  e="$(epic_for "$labels")"

  gh project item-edit --id "$item_id" --project-id "$project_id" \
    --field-id "$moscow_field" --single-select-option-id "$(option_id "MoSCoW" "$m")" >/dev/null
  gh project item-edit --id "$item_id" --project-id "$project_id" \
    --field-id "$epic_field" --single-select-option-id "$(option_id "Epic" "$e")" >/dev/null
  gh project item-edit --id "$item_id" --project-id "$project_id" \
    --field-id "$points_field" --number "$points" >/dev/null

  printf '  set    %-46s  %-6s  %-8s  %s pts\n' "$full_title" "$m" "$e" "$points"
done

echo
echo "Board ready: https://github.com/users/$OWNER/projects/$number"
echo
echo "For the screenshot, open the board and set the view to Group by → MoSCoW."
