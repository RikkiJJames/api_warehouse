#!/usr/bin/env bash
set -euo pipefail

# One-time setup that terraform apply can't do itself:
#   1. push real secret values from .env into the Secret Manager containers
#   2. create the Cloud Build <-> GitHub connection (interactive OAuth)
# Run this after `terraform apply -target=google_project.this -target=google_project_service.apis`
# and before the final `terraform apply`.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TFVARS_FILE="$SCRIPT_DIR/terraform.tfvars"

# Pulls `key = "value"` out of terraform.tfvars so these don't have to be
# duplicated here. Falls back to the given default if the file or key is
# missing (e.g. optional vars like github_connection_name).
tfvars_value() {
  local key="$1" default="$2" val=""
  if [[ -f "$TFVARS_FILE" ]]; then
    val="$(sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*\"([^\"]*)\".*/\1/p" "$TFVARS_FILE" | tail -n1)"
  fi
  printf '%s' "${val:-$default}"
}

PROJECT_ID="$(tfvars_value project_id "")"
REGION="$(tfvars_value region "europe-west2")"
CONNECTION_NAME="$(tfvars_value github_connection_name "github-connection")"
GITHUB_OWNER="$(tfvars_value github_owner "")"
GITHUB_REPO="$(tfvars_value github_repo "api_warehouse")"
ENV_FILE="$SCRIPT_DIR/../.env"

usage() {
  echo "Usage: $0 [--project <id>] [--region <region>] [--connection-name <name>] \\"
  echo "          [--github-owner <owner>] [--github-repo <repo>] [--env-file <path>]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)         PROJECT_ID="$2"; shift 2 ;;
    --region)          REGION="$2"; shift 2 ;;
    --connection-name) CONNECTION_NAME="$2"; shift 2 ;;
    --github-owner)    GITHUB_OWNER="$2"; shift 2 ;;
    --github-repo)     GITHUB_REPO="$2"; shift 2 ;;
    --env-file)        ENV_FILE="$2"; shift 2 ;;
    *) usage ;;
  esac
done

if [[ -z "$PROJECT_ID" || -z "$GITHUB_OWNER" ]]; then
  echo "Error: could not resolve project_id/github_owner from $TFVARS_FILE." >&2
  echo "        Set them there, or pass --project/--github-owner explicitly." >&2
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: env file not found at $ENV_FILE (override with ENV_FILE=...)" >&2
  exit 1
fi

echo "==> Pushing secret values from $ENV_FILE to project $PROJECT_ID"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a

SECRET_NAMES=(
  DB_HOST DB_PORT DB_NAME DB_USER DB_PASSWORD
)

for name in "${SECRET_NAMES[@]}"; do
  value="${!name:-}"
  if [[ -z "$value" ]]; then
    echo "  skip $name (empty/unset in $ENV_FILE)" >&2
    continue
  fi
  printf '%s' "$value" | gcloud secrets versions add "$name" \
    --project="$PROJECT_ID" --data-file=-
  echo "  added version for $name"
done

echo "==> Creating Cloud Build <-> GitHub connection '$CONNECTION_NAME'"
echo "    (this opens a browser for GitHub App install + OAuth — no PAT needed)"
gcloud builds connections create github "$CONNECTION_NAME" \
  --region="$REGION" --project="$PROJECT_ID"

echo "==> Connection status:"
gcloud builds connections describe "$CONNECTION_NAME" \
  --region="$REGION" --project="$PROJECT_ID"

echo
echo "Done. If the GitHub App was scoped to specific repos, make sure it covers"
echo "$GITHUB_OWNER/$GITHUB_REPO, then run: terraform apply"
