class StorageAdapter:
    # Trakt's sync/ratings endpoints carry personal ratings/rated_at timestamps
    # that can change after the fact — these are applied as updates onto rows
    # already written by the corresponding watched_* endpoint, not inserted.
    RATING_HANDLERS = {
        "movie_ratings": "update_movie_ratings",
        "show_ratings": "update_show_ratings",
    }

    # Re-running history endpoints must be able to correct a watched_at that
    # was edited in Trakt after the original event was ingested, so these
    # upsert on the endpoint's unique id instead of ON CONFLICT DO NOTHING.
    UPSERT_CONFIG = {
        "watched_movies": ("history_id", ["watched_at"]),
        "watched_episodes": ("history_id", ["watched_at"]),
        # Hardcover ratings/finish dates can change after a book is first
        # synced (e.g. correcting a rating, or finishing a re-read), so
        # re-ingesting the same user_book_id must update these in place.
        # book_image is included for the same backfill reason as below.
        "read_books": ("user_book_id", ["my_rating", "read_started_at", "read_finished_at", "book_image"]),
        # album/artist/currently_reading/want_to_read/movie_details/show_details
        # otherwise fall through to plain ON CONFLICT DO NOTHING (see
        # save_records below), which would never backfill the images column
        # onto a row inserted before it existed — these are upserted purely
        # so that backfill (via refetch_if_null) can happen, nothing else
        # about them needs correcting.
        "album": ("album_id", ["images"]),
        "artist": ("artist_id", ["images"]),
        "currently_reading": ("user_book_id", ["book_image"]),
        "want_to_read": ("user_book_id", ["book_image"]),
        "movie_details": ("ids_trakt", ["images"]),
        "show_details": ("ids_trakt", ["images"]),
    }

    def __init__(self, registry, api_id=None):
        self.registry = registry
        self.api_id = api_id

    def save(self, endpoint: dict, logical_name: str, records: list, extra: dict | None = None):
        db_target = endpoint.get("db_target")

        if not db_target:
            return None

        # Copy rather than mutate the caller's dict — execution_engine.py's
        # non-paginated-param branch passes the same object as both `params`
        # and `extra`, so mutating in place here leaked "api_id" into the
        # variables of a GraphQL endpoint's next paginated request, which
        # Hasura then rejected as an undeclared variable.
        extra = dict(extra or {})
        if self.api_id:
            extra["api_id"] = self.api_id

        db_source_field = endpoint.get("db_source_field")
        db_target_column = endpoint.get("db_target_column")

        if db_source_field and db_target_column:
            values = [
                r.get(db_source_field)
                for r in records
                if isinstance(r, dict) and db_source_field in r
            ]

            self.registry.save_to_table(
                db_target,
                db_target_column,
                values,
                extra_fields=extra or None,
            )
        elif logical_name in self.RATING_HANDLERS:
            getattr(self.registry, self.RATING_HANDLERS[logical_name])(db_target, records)
        elif logical_name in self.UPSERT_CONFIG:
            conflict_column, update_columns = self.UPSERT_CONFIG[logical_name]
            enriched = [
                {**r, **extra} if isinstance(r, dict) else r
                for r in records
            ]
            self.registry.upsert_records(db_target, enriched, conflict_column, update_columns)
        else:
            enriched = [
                {**r, **extra} if isinstance(r, dict) else r
                for r in records
            ]
            self.registry.save_records(db_target, enriched)