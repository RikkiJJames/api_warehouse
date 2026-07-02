#!/usr/bin/env bash
set -euo pipefail

DOCKERHUB_USER="rikkijames"
IMAGE="airflow"
TAG="latest"
COMPOSE_DIR="$(dirname "$0")/airflow"

usage() {
  echo "Usage: $0 [--image <image-name>] [--tag <tag>]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) IMAGE="$2"; shift 2 ;;
    --tag)   TAG="$2";   shift 2 ;;
    *) usage ;;
  esac
done

FULL_IMAGE="$DOCKERHUB_USER/api-warehouse-$IMAGE:$TAG"

echo "==> Pulling $FULL_IMAGE"
docker pull "$FULL_IMAGE"

echo "==> Bringing down existing services"
AIRFLOW_IMAGE_NAME="$FULL_IMAGE" docker compose -f "$COMPOSE_DIR/docker-compose.yaml" down

echo "==> Starting services"
AIRFLOW_IMAGE_NAME="$FULL_IMAGE" docker compose -f "$COMPOSE_DIR/docker-compose.yaml" up --no-build -d

echo "Done. Stack is up using $FULL_IMAGE"
