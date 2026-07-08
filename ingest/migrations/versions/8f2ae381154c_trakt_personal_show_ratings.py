"""trakt personal show ratings

Revision ID: 8f2ae381154c
Revises: 9f829f0ec0f9
Create Date: 2026-07-08 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f2ae381154c'
down_revision: Union[str, Sequence[str], None] = '9f829f0ec0f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('watched_episodes', sa.Column('show_my_rating', sa.Float(), nullable=True), schema='trakt')
    op.add_column('watched_episodes', sa.Column('show_my_rated_at', sa.DateTime(timezone=True), nullable=True), schema='trakt')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('watched_episodes', 'show_my_rated_at', schema='trakt')
    op.drop_column('watched_episodes', 'show_my_rating', schema='trakt')
