from unittest.mock import MagicMock

from src.api.storage_adapter import StorageAdapter


def make_endpoint(logical_name, db_target="trakt.watched_movies", db_source_field=None, db_target_column=None):
    return {
        "logical_name": logical_name,
        "db_target": db_target,
        "db_source_field": db_source_field,
        "db_target_column": db_target_column,
    }


def test_movie_ratings_routes_to_update_movie_ratings():
    registry = MagicMock()
    adapter = StorageAdapter(registry)
    records = [{"rating": 8, "movie": {"ids": {"trakt": 1}}}]

    adapter.save(make_endpoint("movie_ratings"), "movie_ratings", records)

    registry.update_movie_ratings.assert_called_once_with("trakt.watched_movies", records)
    registry.save_records.assert_not_called()


def test_watched_movies_routes_to_upsert_records():
    registry = MagicMock()
    adapter = StorageAdapter(registry)
    records = [{"history_id": 1, "watched_at": "2024-01-01T00:00:00Z"}]

    adapter.save(make_endpoint("watched_movies"), "watched_movies", records)

    registry.upsert_records.assert_called_once_with(
        "trakt.watched_movies", records, "history_id", ["watched_at"]
    )
    registry.save_records.assert_not_called()


def test_read_books_routes_to_upsert_records():
    registry = MagicMock()
    adapter = StorageAdapter(registry)
    records = [{"user_book_id": 1, "my_rating": 4.5}]

    adapter.save(
        make_endpoint("read_books", db_target="hardcover.read_books"),
        "read_books",
        records,
    )

    registry.upsert_records.assert_called_once_with(
        "hardcover.read_books",
        records,
        "user_book_id",
        ["my_rating", "read_started_at", "read_finished_at"],
    )
    registry.save_records.assert_not_called()


def test_other_endpoints_still_use_save_records():
    registry = MagicMock()
    adapter = StorageAdapter(registry)
    records = [{"id": 1, "name": "foo"}]

    adapter.save(make_endpoint("watchlist_movies", db_target="trakt.watchlist_movies"), "watchlist_movies", records)

    registry.save_records.assert_called_once_with("trakt.watchlist_movies", records)
    registry.update_movie_ratings.assert_not_called()
    registry.upsert_records.assert_not_called()
