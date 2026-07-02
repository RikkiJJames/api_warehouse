#!/bin/bash
# Apply all pending migrations.
# Usage: ./upgrade.sh          (runs to head)
#        ./upgrade.sh +1       (runs one step forward)
TARGET="${1:-head}"
cd "$(dirname "$0")/.." && uv run alembic upgrade "$TARGET"
