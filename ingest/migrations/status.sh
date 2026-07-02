#!/bin/bash
# Show current revision and any pending migrations.
cd "$(dirname "$0")/.." && uv run alembic current && echo "" && uv run alembic history --verbose
