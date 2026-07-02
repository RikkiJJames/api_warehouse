"""partial index for now playing tracks

Revision ID: 94b45ca7bead
Revises: ac162c1bec24
Create Date: 2026-06-23 17:46:43.002443

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94b45ca7bead'
down_revision: Union[str, Sequence[str], None] = 'ac162c1bec24'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # One now-playing slot per artist+track: prevents duplicate NULL date_uts rows
    op.create_index(
        "uq_recent_track_now_playing",
        "recent_tracks",
        ["artist_name", "name"],
        unique=True,
        schema="music",
        postgresql_where=sa.text("date_uts IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_recent_track_now_playing",
        table_name="recent_tracks",
        schema="music",
    )
