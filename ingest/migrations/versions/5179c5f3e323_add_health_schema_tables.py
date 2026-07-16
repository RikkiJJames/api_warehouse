"""add health schema tables for google health api ingestion

Revision ID: 5179c5f3e323
Revises: 2aadebd00fb7
Create Date: 2026-07-16 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '5179c5f3e323'
down_revision: Union[str, Sequence[str], None] = '2aadebd00fb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS health")

    op.create_table(
        'steps',
        sa.Column('id', sa.Integer(), sa.Identity(start=1), primary_key=True),
        sa.Column('api_id', sa.Integer(), sa.ForeignKey('config.api.id'), nullable=True),
        sa.Column('civilStartTime_year', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_month', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_day', sa.Integer(), nullable=True),
        sa.Column(
            'date', sa.Date(),
            sa.Computed(
                '(make_date("civilStartTime_year", "civilStartTime_month", "civilStartTime_day"))',
                persisted=True,
            ),
            nullable=True,
        ),
        sa.Column('steps_countSum', sa.Integer(), nullable=True),
        sa.UniqueConstraint('date', name='uq_health_steps_date'),
        schema='health',
    )

    op.create_table(
        'distance',
        sa.Column('id', sa.Integer(), sa.Identity(start=1), primary_key=True),
        sa.Column('api_id', sa.Integer(), sa.ForeignKey('config.api.id'), nullable=True),
        sa.Column('civilStartTime_year', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_month', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_day', sa.Integer(), nullable=True),
        sa.Column(
            'date', sa.Date(),
            sa.Computed(
                '(make_date("civilStartTime_year", "civilStartTime_month", "civilStartTime_day"))',
                persisted=True,
            ),
            nullable=True,
        ),
        sa.Column('distance_metersSum', sa.Integer(), nullable=True),
        sa.UniqueConstraint('date', name='uq_health_distance_date'),
        schema='health',
    )

    op.create_table(
        'total_calories',
        sa.Column('id', sa.Integer(), sa.Identity(start=1), primary_key=True),
        sa.Column('api_id', sa.Integer(), sa.ForeignKey('config.api.id'), nullable=True),
        sa.Column('civilStartTime_year', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_month', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_day', sa.Integer(), nullable=True),
        sa.Column(
            'date', sa.Date(),
            sa.Computed(
                '(make_date("civilStartTime_year", "civilStartTime_month", "civilStartTime_day"))',
                persisted=True,
            ),
            nullable=True,
        ),
        sa.Column('totalCalories_kcalSum', sa.Float(), nullable=True),
        sa.UniqueConstraint('date', name='uq_health_total_calories_date'),
        schema='health',
    )

    op.create_table(
        'active_minutes',
        sa.Column('id', sa.Integer(), sa.Identity(start=1), primary_key=True),
        sa.Column('api_id', sa.Integer(), sa.ForeignKey('config.api.id'), nullable=True),
        sa.Column('civilStartTime_year', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_month', sa.Integer(), nullable=True),
        sa.Column('civilStartTime_day', sa.Integer(), nullable=True),
        sa.Column(
            'date', sa.Date(),
            sa.Computed(
                '(make_date("civilStartTime_year", "civilStartTime_month", "civilStartTime_day"))',
                persisted=True,
            ),
            nullable=True,
        ),
        sa.Column('activeMinutes_activeMinutesRollupByActivityLevel', postgresql.JSONB(), nullable=True),
        sa.UniqueConstraint('date', name='uq_health_active_minutes_date'),
        schema='health',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('active_minutes', schema='health')
    op.drop_table('total_calories', schema='health')
    op.drop_table('distance', schema='health')
    op.drop_table('steps', schema='health')
    op.execute("DROP SCHEMA IF EXISTS health")
