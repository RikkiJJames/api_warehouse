"""fix health tables' civil_start_time shape (CivilDateTime nests under date)

Revision ID: 940ef246adfe
Revises: 5179c5f3e323
Create Date: 2026-07-16 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '940ef246adfe'
down_revision: Union[str, Sequence[str], None] = '5179c5f3e323'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = ("steps", "distance", "total_calories", "active_minutes")

DATE_COMPUTED_SQL = (
    "(make_date("
    "(\"civilStartTime_date\"->>'year')::int, "
    "(\"civilStartTime_date\"->>'month')::int, "
    "(\"civilStartTime_date\"->>'day')::int"
    "))"
)


def upgrade() -> None:
    """Upgrade schema."""
    # civilStartTime is a CivilDateTime ({date: {year,month,day}, time:
    # <optional>}), not a bare {year,month,day} — every dailyRollUp request
    # 400'd because get_extra_params() built the wrong shape for range.start/
    # end too. These tables were never successfully populated, so this is a
    # pure schema fix, not a backfill.
    for table in TABLES:
        op.execute(f"DROP VIEW IF EXISTS staging.stg_{table} CASCADE")
        op.drop_column(table, 'date', schema='health')
        op.drop_column(table, 'civilStartTime_day', schema='health')
        op.drop_column(table, 'civilStartTime_month', schema='health')
        op.drop_column(table, 'civilStartTime_year', schema='health')
        op.add_column(table, sa.Column('civilStartTime_date', postgresql.JSONB(), nullable=True), schema='health')
        op.add_column(
            table,
            sa.Column('date', sa.Date(), sa.Computed(DATE_COMPUTED_SQL, persisted=True), nullable=True),
            schema='health',
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.drop_column(table, 'date', schema='health')
        op.drop_column(table, 'civilStartTime_date', schema='health')
        op.add_column(table, sa.Column('civilStartTime_year', sa.Integer(), nullable=True), schema='health')
        op.add_column(table, sa.Column('civilStartTime_month', sa.Integer(), nullable=True), schema='health')
        op.add_column(table, sa.Column('civilStartTime_day', sa.Integer(), nullable=True), schema='health')
        op.add_column(
            table,
            sa.Column(
                'date', sa.Date(),
                sa.Computed(
                    '(make_date("civilStartTime_year", "civilStartTime_month", "civilStartTime_day"))',
                    persisted=True,
                ),
                nullable=True,
            ),
            schema='health',
        )
