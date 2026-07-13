from sqlalchemy import Identity, ForeignKey, UniqueConstraint
from src.db.core.db import Base
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column


class Endpoint(Base):
    __tablename__ = "endpoints"
    __table_args__ = (
        UniqueConstraint("api_id", "logical_name", name="uq_endpoint_api_logical_name"),
        {"schema": "config"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    api_id: Mapped[int] = mapped_column(ForeignKey("config.api.id"), nullable=False)
    logical_name: Mapped[str] = mapped_column(nullable=False)
    path_template: Mapped[str] = mapped_column(nullable=False)
    exec_order: Mapped[int] = mapped_column(default=999)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))
    db_target: Mapped[str | None] = mapped_column(
        nullable=True
    )  # e.g. "mma.categories"
    db_target_column: Mapped[str | None] = mapped_column(
        nullable=True
    )  # DB column to write to
    db_source_field: Mapped[str | None] = mapped_column(nullable=True)
    response_path: Mapped[str | None] = mapped_column(nullable=True)
    method: Mapped[str] = mapped_column(default="GET", server_default="GET")
    query: Mapped[str | None] = mapped_column(nullable=True)


class EndpointParam(Base):
    __tablename__ = "endpoint_params"
    __table_args__ = (
        UniqueConstraint(
            "endpoint_id", "param_name", name="uq_endpoint_param_endpoint_param"
        ),
        {"schema": "config"},
    )

    id: Mapped[int] = mapped_column(Identity(start=1), primary_key=True)
    endpoint_id: Mapped[int] = mapped_column(ForeignKey("config.endpoints.id"))
    param_name: Mapped[str] = mapped_column(nullable=False)
    required: Mapped[bool] = mapped_column(default=False)
    default_value: Mapped[str] = mapped_column(nullable=True)
    value_type: Mapped[str] = mapped_column(default="string")
    source_table: Mapped[str | None] = mapped_column(nullable=True)
    source_column: Mapped[str | None] = mapped_column(nullable=True)
    is_distinct: Mapped[bool] = mapped_column(default=False)
    # For "ids"-batch params only: an id is normally treated as permanently
    # fetched once its row exists in db_target (metadata like this rarely
    # changes) — but if a column gets added to that endpoint later, existing
    # rows would never pick it up since they're never re-requested. Naming a
    # column here re-includes an id in the next fetch as long as that column
    # is still null on its row, self-healing exactly that gap without
    # re-fetching everything else.
    refetch_if_null: Mapped[str | None] = mapped_column(nullable=True)
    # For "path_id" params (single-item detail endpoints like Trakt's
    # /movies/{id}), the id column in db_target usually isn't literally named
    # the same as source_column (e.g. flatten_record turns a bare "ids"
    # object into "ids_trakt", not "trakt_movie_id") — set this when they
    # differ. Falls back to source_column when unset, so existing "ids"-batch
    # params (where source and target happen to share a name) are unaffected.
    target_column: Mapped[str | None] = mapped_column(nullable=True)
