"""split trakt movie/show images column into per-type columns

Revision ID: 2aadebd00fb7
Revises: a623fe237597
Create Date: 2026-07-15 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2aadebd00fb7'
down_revision: Union[str, Sequence[str], None] = 'a623fe237597'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # flatten_record flattens one level of every dict it finds, including the
    # response's top-level "images" object, so it never arrives as a single
    # "images" key — it's pre-split into images_poster/images_clearart/etc.
    # The old single "images" JSONB column therefore never got populated.
    op.execute("DROP VIEW IF EXISTS staging.stg_movie_details CASCADE")
    op.execute("DROP VIEW IF EXISTS staging.stg_show_details CASCADE")
    for table in ("movie_details", "show_details"):
        op.drop_column(table, "images", schema="trakt")
        op.add_column(table, sa.Column("images_poster", postgresql.JSONB(), nullable=True), schema="trakt")
        op.add_column(table, sa.Column("images_clearart", postgresql.JSONB(), nullable=True), schema="trakt")
        op.add_column(table, sa.Column("images_thumb", postgresql.JSONB(), nullable=True), schema="trakt")


def downgrade() -> None:
    """Downgrade schema."""
    for table in ("movie_details", "show_details"):
        op.drop_column(table, "images_thumb", schema="trakt")
        op.drop_column(table, "images_clearart", schema="trakt")
        op.drop_column(table, "images_poster", schema="trakt")
        op.add_column(table, sa.Column("images", postgresql.JSONB(), nullable=True), schema="trakt")
