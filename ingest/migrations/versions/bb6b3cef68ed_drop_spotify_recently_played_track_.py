"""drop spotify recently_played track detail columns

Revision ID: bb6b3cef68ed
Revises: 2e47476e4a92
Create Date: 2026-07-17 09:27:33.280718

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb6b3cef68ed'
down_revision: Union[str, Sequence[str], None] = '2e47476e4a92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('recently_played', 'track_name', schema='spotify')
    op.drop_column('recently_played', 'track_duration_ms', schema='spotify')
    op.drop_column('recently_played', 'track_explicit', schema='spotify')
    op.drop_column('recently_played', 'track_popularity', schema='spotify')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('recently_played', sa.Column('track_popularity', sa.Integer(), nullable=True), schema='spotify')
    op.add_column('recently_played', sa.Column('track_explicit', sa.Boolean(), nullable=True), schema='spotify')
    op.add_column('recently_played', sa.Column('track_duration_ms', sa.Integer(), nullable=True), schema='spotify')
    op.add_column('recently_played', sa.Column('track_name', sa.String(), nullable=True), schema='spotify')
