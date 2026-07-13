"""add hardcover book and trakt movie/show images

Revision ID: 42bb4c839eb1
Revises: cc5908153b87
Create Date: 2026-07-13 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '42bb4c839eb1'
down_revision: Union[str, Sequence[str], None] = 'cc5908153b87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('read_books', sa.Column('book_image', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='hardcover')
    op.add_column('currently_reading', sa.Column('book_image', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='hardcover')
    op.add_column('want_to_read', sa.Column('book_image', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='hardcover')
    op.add_column('watched_movies', sa.Column('movie_images', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='trakt')
    op.add_column('watched_episodes', sa.Column('show_images', postgresql.JSONB(astext_type=sa.Text()), nullable=True), schema='trakt')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('watched_episodes', 'show_images', schema='trakt')
    op.drop_column('watched_movies', 'movie_images', schema='trakt')
    op.drop_column('want_to_read', 'book_image', schema='hardcover')
    op.drop_column('currently_reading', 'book_image', schema='hardcover')
    op.drop_column('read_books', 'book_image', schema='hardcover')
