"""add hardcover schema

Revision ID: 98585a3269e1
Revises: 8f4afc1e1630
Create Date: 2026-07-08 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98585a3269e1'
down_revision: Union[str, Sequence[str], None] = '8f4afc1e1630'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE SCHEMA IF NOT EXISTS hardcover")

    op.create_table(
        'read_books',
        sa.Column('id', sa.Integer(), sa.Identity(always=False, start=1), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.Column('user_book_id', sa.BigInteger(), nullable=True),
        sa.Column('my_rating', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('book_id', sa.BigInteger(), nullable=True),
        sa.Column('book_title', sa.String(), nullable=True),
        sa.Column('book_pages', sa.Integer(), nullable=True),
        sa.Column('book_release_date', sa.String(), nullable=True),
        sa.Column('read_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['api_id'], ['config.api.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_book_id', name='uq_hardcover_read_books_user_book_id'),
        schema='hardcover',
    )
    op.create_table(
        'currently_reading',
        sa.Column('id', sa.Integer(), sa.Identity(always=False, start=1), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.Column('user_book_id', sa.BigInteger(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('book_id', sa.BigInteger(), nullable=True),
        sa.Column('book_title', sa.String(), nullable=True),
        sa.Column('book_pages', sa.Integer(), nullable=True),
        sa.Column('book_release_date', sa.String(), nullable=True),
        sa.Column('read_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['api_id'], ['config.api.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_book_id', name='uq_hardcover_currently_reading_user_book_id'),
        schema='hardcover',
    )
    op.create_table(
        'want_to_read',
        sa.Column('id', sa.Integer(), sa.Identity(always=False, start=1), nullable=False),
        sa.Column('api_id', sa.Integer(), nullable=True),
        sa.Column('user_book_id', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('book_id', sa.BigInteger(), nullable=True),
        sa.Column('book_title', sa.String(), nullable=True),
        sa.Column('book_pages', sa.Integer(), nullable=True),
        sa.Column('book_release_date', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['api_id'], ['config.api.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_book_id', name='uq_hardcover_want_to_read_user_book_id'),
        schema='hardcover',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('want_to_read', schema='hardcover')
    op.drop_table('currently_reading', schema='hardcover')
    op.drop_table('read_books', schema='hardcover')
    op.execute("DROP SCHEMA IF EXISTS hardcover")
