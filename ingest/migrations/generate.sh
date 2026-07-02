#!/bin/bash
# Generate a new migration from model changes.
# Usage: ./generate.sh "your migration message"
if [ -z "$1" ]; then
  echo "Usage: ./generate.sh \"migration message\""
  exit 1
fi
cd "$(dirname "$0")/.." && uv run alembic revision --autogenerate -m "$1"
