#!/usr/bin/env bash
set -euo pipefail

# One-time setup that terraform apply can't do itself:
#   1. push real secret values from .env into the Secret Manager containers
#   2. create the Cloud Build <-> GitHub connection (interactive OAuth)
# Run this after `terraform apply -target=google_project.this -target=google_project_service.apis`
# and before the final `terraform apply`.

PROJECT_ID="${PROJECT_ID:-home-repository}"
REGION="${REGION:-europe-west2}"
CONNECTION_NAME="${CONNECTION_NAME:-github-connection}"
GITHUB_OWNER="${GITHUB_OWNER:-rikkijames}"
GITHUB_REPO="${GITHUB_REPO:-api_warehouse}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/../.env}"

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
  SPORTS_API_KEY
  SPOTIFY_CLIENT_ID SPOTIFY_CLIENT_SECRET SPOTIFY_REFRESH_TOKEN SPOTIFY_REDIRECT_URL
  HARDCOVER_API_TOKEN
  TRAKT_CLIENT_ID TRAKT_CLIENT_SECRET TRAKT_REFRESH_TOKEN TRAKT_REDIRECT_URL
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
