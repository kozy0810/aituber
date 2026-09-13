#!/usr/bin/env bash
# Start implementation work on an existing GitHub Issue in kozy0810/aituber:
# create a branch from main and flip the Issue's Kanban Status to "In progress".
#
# Field/option IDs below are specific to the "AI Tuber" project board
# (kozy0810/projects/3). If the board is ever recreated, re-fetch them with:
#   gh project field-list 3 --owner kozy0810 --format json
#   gh project view 3 --owner kozy0810 --format json --jq '.id'
set -euo pipefail

REPO="kozy0810/aituber"
PROJECT_NUMBER=3
PROJECT_OWNER="kozy0810"
PROJECT_ID="PVT_kwHOAcJc1M4BjV1O"

STATUS_FIELD_ID="PVTSSF_lAHOAcJc1M4BjV1OzhiKftE"
STATUS_IN_PROGRESS_OPTION_ID="47fc9ee4"

usage() {
  cat <<'EOF'
Usage: start_implementation.sh --issue <number> --slug <kebab-case-slug>

  --issue   Issue number in kozy0810/aituber (required)
  --slug    Short English kebab-case slug describing the issue, used in the
            branch name (required)

Creates branch "issue-<number>-<slug>" from up-to-date main, and sets the
issue's Status to "In progress" on the AI Tuber project board.
EOF
}

ISSUE=""
SLUG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --issue) ISSUE="$2"; shift 2 ;;
    --slug) SLUG="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$ISSUE" || -z "$SLUG" ]]; then
  usage
  exit 1
fi

ISSUE_URL="https://github.com/${REPO}/issues/${ISSUE}"
BRANCH="issue-${ISSUE}-${SLUG}"

echo "Fetching issue #$ISSUE..." >&2
gh issue view "$ISSUE" --repo "$REPO" >/dev/null

echo "Fetching latest main and creating branch $BRANCH..." >&2
# Branch straight off origin/main via fetch, rather than "git checkout main;
# git pull" — this repo is routinely worked on from git worktrees (including
# this skill's own agent sessions), and "main" is often already checked out
# in another worktree, which makes "git checkout main" fail with
# "fatal: 'main' is already used by worktree at ...". Fetching and branching
# from origin/main works regardless of what the local checkout is on.
git fetch origin main
git checkout -b "$BRANCH" origin/main

echo "Registering issue on project #$PROJECT_NUMBER and setting Status=In progress..." >&2
ITEM_ID=$(gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --url "$ISSUE_URL" --format json | jq -r '.id')

gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" --single-select-option-id "$STATUS_IN_PROGRESS_OPTION_ID" >/dev/null

mkdir -p docs/specs

echo "Branch: $BRANCH"
echo "Issue: $ISSUE_URL"
echo "Status set to: In progress"
