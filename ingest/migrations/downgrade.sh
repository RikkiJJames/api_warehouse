#!/bin/bash
# Roll back migrations.
# Usage: ./downgrade.sh        (rolls back one step)
#        ./downgrade.sh -2     (rolls back two steps)
#        ./downgrade.sh base   (rolls back everything)
TARGET="${1:--1}"
cd "$(dirname "$0")/.." && uv run alembic downgrade "$TARGET"
