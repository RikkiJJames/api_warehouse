"""add spotify track album artist drop top artists top tracks

Revision ID: a3977bc0591e
Revises: 94b45ca7bead
Create Date: 2026-06-26 10:34:17.477563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a3977bc0591e'
down_revision: Union[str, Sequence[str], None] = '94b45ca7bead'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_table('top_artists', schema='spotify')
    op.drop_table('top_tracks', schema='spotify')


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table('top_tracks',
    sa.Column('id', sa.INTEGER(), sa.Identity(always=False, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('api_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('track_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('popularity', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('duration_ms', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('explicit', sa.BOOLEAN(), autoincrement=False, nullable=True),
    sa.Column('uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('album_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('album_name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('time_range', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('date_added', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['api_id'], ['config.api.id'], name=op.f('top_tracks_api_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('top_tracks_pkey')),
    sa.UniqueConstraint('track_id', 'time_range', 'date_added', name=op.f('uq_spotify_top_track_snapshot'), postgresql_include=[], postgresql_nulls_not_distinct=False),
    schema='spotify'
    )
    op.create_table('top_artists',
    sa.Column('id', sa.INTEGER(), sa.Identity(always=False, start=1, increment=1, minvalue=1, maxvalue=2147483647, cycle=False, cache=1), autoincrement=True, nullable=False),
    sa.Column('api_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('artist_id', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('popularity', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('followers_total', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('uri', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('time_range', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('date_added', postgresql.TIMESTAMP(timezone=True), server_default=sa.text('now()'), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['api_id'], ['config.api.id'], name=op.f('top_artists_api_id_fkey')),
    sa.PrimaryKeyConstraint('id', name=op.f('top_artists_pkey')),
    sa.UniqueConstraint('artist_id', 'time_range', 'date_added', name=op.f('uq_spotify_top_artist_snapshot'), postgresql_include=[], postgresql_nulls_not_distinct=False),
    schema='spotify'
    )
    # ### end Alembic commands ###
