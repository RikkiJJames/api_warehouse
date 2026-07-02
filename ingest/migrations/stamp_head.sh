#!/bin/bash
# Mark the database as being at the latest revision without running any migrations.
# Use this after create_all has already built the tables.
cd "$(dirname "$0")/.." && uv run alembic stamp head
