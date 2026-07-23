"""fix health distance column name to match Google Health API

Revision ID: a0c76360d096
Revises: bb6b3cef68ed
Create Date: 2026-07-23 14:33:03.681673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0c76360d096'
down_revision: Union[str, Sequence[str], None] = 'bb6b3cef68ed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # staging.stg_distance is a dbt `select *`-shaped view bound to the old
    # column name — recreated correctly by the next `dbt run`, so it's safe
    # to let the rename cascade to it here (same as the recently_played
    # column-drop migration).
    op.execute("DROP VIEW IF EXISTS staging.stg_distance CASCADE")
    op.alter_column(
        "distance",
        "distance_metersSum",
        new_column_name="distance_millimetersSum",
        schema="health",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        "distance",
        "distance_millimetersSum",
        new_column_name="distance_metersSum",
        schema="health",
    )
