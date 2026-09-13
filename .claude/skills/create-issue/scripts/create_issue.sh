#!/usr/bin/env bash
# Create a GitHub Issue for kozy0810/aituber and register it on the
# "AI Tuber" Kanban board (kozy0810/projects/3) with initial field values.
#
# Field/option IDs below are specific to that project board. If the board
# is ever recreated, re-fetch them with:
#   gh project field-list 3 --owner kozy0810 --format json
#   gh project view 3 --owner kozy0810 --format json --jq '.id'
set -euo pipefail

REPO="kozy0810/aituber"
PROJECT_NUMBER=3
PROJECT_OWNER="kozy0810"
PROJECT_ID="PVT_kwHOAcJc1M4BjV1O"

STATUS_FIELD_ID="PVTSSF_lAHOAcJc1M4BjV1OzhiKftE"
STATUS_BACKLOG_OPTION_ID="f75ad846"

PRIORITY_FIELD_ID="PVTSSF_lAHOAcJc1M4BjV1OzhiKfyM"
SIZE_FIELD_ID="PVTSSF_lAHOAcJc1M4BjV1OzhiKfyQ"

usage() {
  cat <<'EOF'
Usage: create_issue.sh --title "<title>" --body-file <path> --priority P0|P1|P2 --size XS|S|M|L|XL

  --title       Issue title (required)
  --body-file   Path to a file containing the issue body markdown (required)
  --priority    P0, P1, or P2 (required)
  --size        XS, S, M, L, or XL (required)

Status is always set to "Backlog" on creation.
EOF
}

TITLE=""
BODY_FILE=""
PRIORITY=""
SIZE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --title) TITLE="$2"; shift 2 ;;
    --body-file) BODY_FILE="$2"; shift 2 ;;
    --priority) PRIORITY="$2"; shift 2 ;;
    --size) SIZE="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$TITLE" || -z "$BODY_FILE" || -z "$PRIORITY" || -z "$SIZE" ]]; then
  usage
  exit 1
fi

if [[ ! -f "$BODY_FILE" ]]; then
  echo "Body file not found: $BODY_FILE" >&2
  exit 1
fi

case "$PRIORITY" in
  P0) PRIORITY_OPTION_ID="79628723" ;;
  P1) PRIORITY_OPTION_ID="0a877460" ;;
  P2) PRIORITY_OPTION_ID="da944a9c" ;;
  *) echo "Invalid --priority: $PRIORITY (expected P0, P1, or P2)" >&2; exit 1 ;;
esac

case "$SIZE" in
  XS) SIZE_OPTION_ID="6c6483d2" ;;
  S)  SIZE_OPTION_ID="f784b110" ;;
  M)  SIZE_OPTION_ID="7515a9f1" ;;
  L)  SIZE_OPTION_ID="817d0097" ;;
  XL) SIZE_OPTION_ID="db339eb2" ;;
  *) echo "Invalid --size: $SIZE (expected XS, S, M, L, or XL)" >&2; exit 1 ;;
esac

echo "Creating issue on $REPO..." >&2
ISSUE_URL=$(gh issue create --repo "$REPO" --title "$TITLE" --body-file "$BODY_FILE")
echo "Created: $ISSUE_URL" >&2

echo "Adding to project #$PROJECT_NUMBER..." >&2
ITEM_ID=$(gh project item-add "$PROJECT_NUMBER" --owner "$PROJECT_OWNER" --url "$ISSUE_URL" --format json | jq -r '.id')

gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
  --field-id "$STATUS_FIELD_ID" --single-select-option-id "$STATUS_BACKLOG_OPTION_ID" >/dev/null

gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
  --field-id "$PRIORITY_FIELD_ID" --single-select-option-id "$PRIORITY_OPTION_ID" >/dev/null

gh project item-edit --id "$ITEM_ID" --project-id "$PROJECT_ID" \
  --field-id "$SIZE_FIELD_ID" --single-select-option-id "$SIZE_OPTION_ID" >/dev/null

echo "Status=Backlog, Priority=$PRIORITY, Size=$SIZE set." >&2
echo "$ISSUE_URL"
