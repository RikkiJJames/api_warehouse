#!/usr/bin/env bash
set -euo pipefail

DOCKERHUB_USER="rikkijames"
IMAGE="all"
TAG="latest"

usage() {
  echo "Usage: $0 [--image dbt|airflow|all] [--tag <tag>]"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image) IMAGE="$2"; shift 2 ;;
    --tag)   TAG="$2";   shift 2 ;;
    *) usage ;;
  esac
done

ALL_IMAGES=(
  "dbt:dbt"
  "airflow:airflow"
)

SELECTED=()
for entry in "${ALL_IMAGES[@]}"; do
  name="${entry##*:}"
  if [[ "$IMAGE" == "all" || "$IMAGE" == "$name" ]]; then
    SELECTED+=("$entry")
  fi
done

if [[ ${#SELECTED[@]} -eq 0 ]]; then
  echo "Error: unknown image '$IMAGE'. Must be dbt, airflow, or all."
  exit 1
fi

docker login

for entry in "${SELECTED[@]}"; do
  context="${entry%%:*}"
  name="${entry##*:}"
  full_image="$DOCKERHUB_USER/api-warehouse-$name:$TAG"

  echo "==> Building $full_image from ./$context"
  docker build -t "$full_image" "./$context"

  echo "==> Pushing $full_image"
  docker push "$full_image"
done

echo "Done. Images pushed:"
for entry in "${SELECTED[@]}"; do
  name="${entry##*:}"
  echo "  docker.io/$DOCKERHUB_USER/api-warehouse-$name:$TAG"
done
