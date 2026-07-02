#!/usr/bin/env bash
set -euo pipefail

# Loads every key from the root .env into Airflow Variables, skipping DB_*
# (DB creds are supplied via the "neondb" Airflow Connection instead).

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${1:-$SCRIPT_DIR/../.env}"
SERVICE="${AIRFLOW_SERVICE:-airflow-apiserver}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Error: $ENV_FILE not found" >&2
  exit 1
fi

cd "$SCRIPT_DIR"

while IFS='=' read -r key value; do
  [[ -z "$key" || "$key" == \#* ]] && continue
  [[ "$key" == DB_* ]] && continue
  echo "Setting Airflow Variable: $key"
  docker compose exec -T "$SERVICE" airflow variables set "$key" "$value"
done < <(grep -E '^[A-Z_][A-Z0-9_]*=' "$ENV_FILE")

echo "Done."
