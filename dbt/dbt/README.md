# dbt (api_warehouse)

dbt project (`profile: api_warehouse`) that transforms the raw tables written by [`ingest/`](../../ingest/README.md) into analytics-ready models in PostgreSQL. Part of the [api_warehouse](../../README.md) monorepo — no `pyproject.toml` of its own, uses the repo root's environment.

## Model structure

Three layers, same pattern per source:

```
staging/<source>/       ← views  — 1:1 with a raw table, renamed columns, light filtering, no joins
intermediate/<source>/  ← views  — joins across staging models, reusable building blocks
marts/<source>/         ← tables — dim_*/fct_* — final, consumption-ready models
```

**Sources with models:**

| Source | Staging | Intermediate | Marts |
|---|---|---|---|
| `spotify` | `track`, `artist`, `album`, `recently_played` | `int_track_enriched` | `dim_tracks`, `dim_artists`, `dim_albums`, `fct_track_stats`, `fct_artist_stats`, `fct_play_history` |
| `trakt` | `stg_watched_movies`, `stg_watched_episodes`, `stg_watchlist_movies`, `stg_watchlist_shows` | `int_movies`, `int_shows`, `int_show_watch_stats` | `dim_movies`, `dim_shows`, `dim_anime`, `dim_genre_map`, `fct_watch_history`, `fct_movie_stats`, `fct_show_stats`, `fct_watchlist`, `fct_genre_stats` |
| `football`, `mma` | sources declared only (no transform models yet) | — | — |

For querying, prefer the **marts** layer — `dim_*` for attributes, `fct_*` for aggregated stats/history. Staging and intermediate models are internal building blocks. See the `spotify.py`/`trakt.py` notebooks in [`analysis/`](../../analysis) for worked examples of joining `dim_*` + `fct_*`.

## Setup

Uses the repo root's `pyproject.toml`/`uv.lock` — see the root [README](../../README.md) for `uv sync`.

`profiles.yml` (already in this directory) reads connection details from env vars:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

Run via the helper script (`dbt run`, reads `.env` from the repo root):

```bash
./run.sh
```

Or directly (e.g. for `dbt build`, which also runs tests):

```bash
uv run --env-file ../../.env dbt build --profiles-dir .
```

Or via Docker (see the root [README](../../README.md) for the full `docker-push.sh`/`docker-deploy.sh` workflow):

```bash
docker build -t api-warehouse-dbt -f ../Dockerfile ../..   # context is the repo root
docker run --env-file ../../.env api-warehouse-dbt
```
