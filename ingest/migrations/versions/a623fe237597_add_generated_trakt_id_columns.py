"""add generated trakt_movie_id/trakt_show_id columns

Revision ID: a623fe237597
Revises: fccbbd9dc489
Create Date: 2026-07-14 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a623fe237597'
down_revision: Union[str, Sequence[str], None] = 'fccbbd9dc489'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # The movie_details/show_details endpoints' path_id param queries these
    # columns directly against the raw table (not the dbt staging layer,
    # where trakt_movie_id/trakt_show_id already exist as JSON-extracted
    # aliases) — same pattern as music.recent_tracks.listened_at.
    op.add_column(
        'watched_movies',
        sa.Column('trakt_movie_id', sa.Integer(), sa.Computed("(movie_ids->>'trakt')::integer", persisted=True), nullable=True),
        schema='trakt',
    )
    op.add_column(
        'watched_episodes',
        sa.Column('trakt_show_id', sa.Integer(), sa.Computed("(show_ids->>'trakt')::integer", persisted=True), nullable=True),
        schema='trakt',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('watched_episodes', 'trakt_show_id', schema='trakt')
    op.drop_column('watched_movies', 'trakt_movie_id', schema='trakt')
