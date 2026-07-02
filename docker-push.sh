#!/usr/bin/env bash
set -euo pipefail

DOCKERHUB_USER="rikkijames"
IMAGE="all"
TAG="latest"

usage() {
  echo "Usage: $0 [--image dbt|airflow|ingest|all] [--tag <tag>]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) IMAGE="$2"; shift 2 ;;
    --tag)   TAG="$2";   shift 2 ;;
    *) usage ;;
  esac
done

# entries are "context:dockerfile:name" — dbt and ingest build from the repo
# root since their Dockerfiles need the shared root pyproject.toml/uv.lock
ALL_IMAGES=(
  "airflow:airflow/Dockerfile:airflow"
  ".:dbt/Dockerfile:dbt"
  ".:ingest/Dockerfile:ingest"
)

SELECTED=()
for entry in "${ALL_IMAGES[@]}"; do
  name="${entry##*:}"
  if [[ "$IMAGE" == "all" || "$IMAGE" == "$name" ]]; then
    SELECTED+=("$entry")
  fi
done

if [[ ${#SELECTED[@]} -eq 0 ]]; then
  echo "Error: unknown image '$IMAGE'. Must be dbt, airflow, ingest, or all."
  exit 1
fi

docker login

for entry in "${SELECTED[@]}"; do
  IFS=':' read -r context dockerfile name <<< "$entry"
  full_image="$DOCKERHUB_USER/api-warehouse-$name:$TAG"

  echo "==> Building $full_image from $context (Dockerfile: $dockerfile)"
  docker build -t "$full_image" -f "$dockerfile" "$context"

  echo "==> Pushing $full_image"
  docker push "$full_image"
done

echo "Done. Images pushed:"
for entry in "${SELECTED[@]}"; do
  name="${entry##*:}"
  echo "  docker.io/$DOCKERHUB_USER/api-warehouse-$name:$TAG"
done
