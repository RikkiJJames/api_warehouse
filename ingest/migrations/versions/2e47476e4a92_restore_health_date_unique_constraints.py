"""restore missing unique constraints on health tables' date column

Revision ID: 2e47476e4a92
Revises: 940ef246adfe
Create Date: 2026-07-16 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '2e47476e4a92'
down_revision: Union[str, Sequence[str], None] = '940ef246adfe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("steps", "distance", "total_calories", "active_minutes")


def upgrade() -> None:
    """Upgrade schema."""
    # 940ef246adfe dropped each table's `date` column to rebuild it against
    # the corrected civilStartTime_date shape — Postgres auto-drops a
    # column-scoped UNIQUE constraint along with its column, and that
    # migration never re-added it. Without it, upsert_records' "ON CONFLICT
    # (date)" has no matching constraint to target and every insert fails
    # with InvalidColumnReference.
    for table in TABLES:
        op.create_unique_constraint(f"uq_health_{table}_date", table, ["date"], schema="health")


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.drop_constraint(f"uq_health_{table}_date", table, schema="health", type_="unique")
