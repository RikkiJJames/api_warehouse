"""endpoint method and query

Revision ID: 8f4afc1e1630
Revises: 8f2ae381154c
Create Date: 2026-07-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8f4afc1e1630'
down_revision: Union[str, Sequence[str], None] = '8f2ae381154c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'endpoints',
        sa.Column('method', sa.String(), nullable=False, server_default='GET'),
        schema='config',
    )
    op.add_column('endpoints', sa.Column('query', sa.Text(), nullable=True), schema='config')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('endpoints', 'query', schema='config')
    op.drop_column('endpoints', 'method', schema='config')
