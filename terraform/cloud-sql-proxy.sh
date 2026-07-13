#!/usr/bin/env bash
set -euo pipefail

# Installs (if missing) and runs the Cloud SQL Auth Proxy against
# api-warehouse-db, so local tools (alembic, a local ingest/analysis run,
# psql) can reach it the same way the Cloud Run sidecar does — the instance
# has no authorized_networks, so this is the only way in from a laptop/VM.
#
# Usage: ./cloud-sql-proxy.sh [--project <id>] [--region <region>] \
#           [--instance <name>] [--port <port>] [--bin <path>]
#
# Leaves the proxy running in the foreground — Ctrl+C to stop. Point your
# .env at DB_HOST=127.0.0.1 / DB_PORT=<port> (5432 by default) while this is
# running.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TFVARS_FILE="$SCRIPT_DIR/terraform.tfvars"

# Same helper as bootstrap.sh — pulls `key = "value"` out of terraform.tfvars
# so these don't have to be duplicated here.
tfvars_value() {
  local key="$1" default="$2" val=""
  if [[ -f "$TFVARS_FILE" ]]; then
    val="$(sed -nE "s/^[[:space:]]*${key}[[:space:]]*=[[:space:]]*\"([^\"]*)\".*/\1/p" "$TFVARS_FILE" | tail -n1)"
  fi
  printf '%s' "${val:-$default}"
}

# Keep in sync with the image tag pinned in cloudrun.tf's cloudsql-proxy
# containers — same binary version the Cloud Run sidecars actually run.
PROXY_VERSION="2.23.0"

PROJECT_ID="$(tfvars_value project_id "")"
REGION="$(tfvars_value region "europe-west2")"
INSTANCE_NAME="api-warehouse-db"
PORT="5432"
BIN_PATH="$SCRIPT_DIR/.bin/cloud-sql-proxy"

usage() {
  echo "Usage: $0 [--project <id>] [--region <region>] [--instance <name>] [--port <port>] [--bin <path>]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project)  PROJECT_ID="$2"; shift 2 ;;
    --region)   REGION="$2"; shift 2 ;;
    --instance) INSTANCE_NAME="$2"; shift 2 ;;
    --port)     PORT="$2"; shift 2 ;;
    --bin)      BIN_PATH="$2"; shift 2 ;;
    *) usage ;;
  esac
done

if [[ -z "$PROJECT_ID" ]]; then
  echo "Error: could not resolve project_id from $TFVARS_FILE." >&2
  echo "        Set it there, or pass --project explicitly." >&2
  exit 1
fi

CONNECTION_NAME="${PROJECT_ID}:${REGION}:${INSTANCE_NAME}"

if command -v cloud-sql-proxy >/dev/null 2>&1; then
  BIN_PATH="$(command -v cloud-sql-proxy)"
  echo "==> Using cloud-sql-proxy already on PATH: $BIN_PATH"
elif [[ -x "$BIN_PATH" ]]; then
  echo "==> Using previously installed cloud-sql-proxy: $BIN_PATH"
else
  echo "==> Installing cloud-sql-proxy v${PROXY_VERSION} to $BIN_PATH"
  mkdir -p "$(dirname "$BIN_PATH")"

  case "$(uname -s)" in
    Darwin) OS="darwin" ;;
    Linux)  OS="linux" ;;
    *) echo "Error: unsupported OS $(uname -s) — install cloud-sql-proxy manually." >&2; exit 1 ;;
  esac
  case "$(uname -m)" in
    arm64|aarch64) ARCH="arm64" ;;
    x86_64|amd64)  ARCH="amd64" ;;
    *) echo "Error: unsupported arch $(uname -m) — install cloud-sql-proxy manually." >&2; exit 1 ;;
  esac

  DOWNLOAD_URL="https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v${PROXY_VERSION}/cloud-sql-proxy.${OS}.${ARCH}"
  curl -sSL -o "$BIN_PATH" "$DOWNLOAD_URL"
  chmod +x "$BIN_PATH"
fi

echo "==> Starting cloud-sql-proxy for $CONNECTION_NAME on 127.0.0.1:$PORT"
echo "    (Ctrl+C to stop; point DB_HOST=127.0.0.1 DB_PORT=$PORT at this while it runs)"
exec "$BIN_PATH" "$CONNECTION_NAME" --port="$PORT"
