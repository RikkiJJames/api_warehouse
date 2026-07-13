"""add endpoint_param refetch_if_null

Revision ID: dbddaa16a92b
Revises: 42bb4c839eb1
Create Date: 2026-07-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'dbddaa16a92b'
down_revision: Union[str, Sequence[str], None] = '42bb4c839eb1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('endpoint_params', sa.Column('refetch_if_null', sa.String(), nullable=True), schema='config')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('endpoint_params', 'refetch_if_null', schema='config')
