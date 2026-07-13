"""add spotify album artist images

Revision ID: cc5908153b87
Revises: 98585a3269e1
Create Date: 2026-07-13 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'cc5908153b87'
down_revision: Union[str, Sequence[str], None] = '98585a3269e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('album', sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='spotify')
    op.add_column('artist', sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='spotify')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('artist', 'images', schema='spotify')
    op.drop_column('album', 'images', schema='spotify')
