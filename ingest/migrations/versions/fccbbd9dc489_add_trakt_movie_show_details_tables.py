"""add trakt movie/show details tables

Revision ID: fccbbd9dc489
Revises: dbddaa16a92b
Create Date: 2026-07-13 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fccbbd9dc489'
down_revision: Union[str, Sequence[str], None] = 'dbddaa16a92b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('endpoint_params', sa.Column('target_column', sa.String(), nullable=True), schema='config')

    op.create_table(
        'movie_details',
        sa.Column('id', sa.Integer(), sa.Identity(always=False, start=1), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.Column('ids_trakt', sa.Integer(), nullable=True),
        sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['api_id'], ['config.api.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ids_trakt', name='uq_trakt_movie_details_ids_trakt'),
        schema='trakt',
    )
    op.create_table(
        'show_details',
        sa.Column('id', sa.Integer(), sa.Identity(always=False, start=1), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.Column('ids_trakt', sa.Integer(), nullable=True),
        sa.Column('images', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['api_id'], ['config.api.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ids_trakt', name='uq_trakt_show_details_ids_trakt'),
        schema='trakt',
    )

    # Trakt's watch-history endpoints turned out to never include image data
    # (confirmed empty for every existing row) regardless of extended=full or
    # how many times they're re-fetched — these columns never had a real
    # chance of being populated. Superseded by movie_details/show_details.
    op.drop_column('watched_movies', 'movie_images', schema='trakt')
    op.drop_column('watched_episodes', 'show_images', schema='trakt')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('watched_episodes', sa.Column('show_images', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='trakt')
    op.add_column('watched_movies', sa.Column('movie_images', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='trakt')
    op.drop_table('show_details', schema='trakt')
    op.drop_table('movie_details', schema='trakt')
    op.drop_column('endpoint_params', 'target_column', schema='config')
