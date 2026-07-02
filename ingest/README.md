# ingest

Python application that fetches raw data from the Spotify, Trakt, Football, and MMA APIs and writes it into PostgreSQL. Also exposes a FastAPI REST API over the dbt-transformed tables.

Has no `pyproject.toml` of its own — it shares the repo root's `pyproject.toml`/`uv.lock` (see the root [README](../README.md)).

## Architecture

```
src/config/api/<source>/<source>.yml   ← YAML endpoint/param config
        │
src/pipelines/<source>/pipeline.py    ← per-source pipeline (auth, fetch, paginate)
        │
src/api/                               ← generic execution engine + response handling
        │
src/db/                                ← SQLAlchemy models + Alembic migrations
        │
PostgreSQL
        │
src/rest_api/                          ← FastAPI serving dbt-transformed views
```

## Pipelines

| Source | Auth | Tables written |
|---|---|---|
| `spotify` | OAuth 2.0 (refresh token flow) | `recently_played`, `track`, `album`, `artist` |
| `trakt` | OAuth 2.0 (refresh token flow) | `watched_movies`, `watched_episodes`, `watchlist_movies`, `watchlist_shows` |
| `football` | API key | `countries`, `leagues`, `teams`, `venues`, `seasons` |
| `mma` | API key | `fighters`, `categories`, `fighter_records` |

API config (base URLs, endpoints, parameters, field mappings) is declared in YAML files under `src/config/api/<source>/` and loaded at runtime via `ConfigLoader`.

### Credentials & DB-backed config

Every credential field (`client_id`, `client_secret`, `redirect_url`, `refresh_token`, `api_key`) is `!env_optional` in the YAML — resolved from `.env` if present, but not required. On each run, `ApiBootstrapper` seeds `config.api_config` from whatever env vars *are* set (skipping ones that aren't), except `refresh_token`, which is insert-only: once a value exists in the DB it's never overwritten by `.env` again.

For Spotify and Trakt, OAuth refresh tokens rotate on use — `TokenManager`/`TraktTokenManager` call back into the pipeline whenever the provider issues a new one, and the pipeline persists it straight to `config.api_config`. Net effect: run once locally with real `.env` credentials to bootstrap each API, and every run after that (including scheduled runs via Airflow) only needs DB connection details — no API credentials required in the environment at all.

### Reducing API calls (Spotify)

Spotify's `/tracks`, `/albums`, `/artists` accept a comma-separated batch of ids instead of one per request — `ExecutionEngine` batches these (20 ids/request) and additionally skips any id already present in the destination table, so only genuinely new tracks/albums/artists get fetched. `recently_played` uses a watermark (`recently_played_watermark` in `config.api_config`, driven by Spotify's `after` cursor) so each run only pulls plays since the last run instead of re-fetching history. On a `429`, requests retry with backoff up to a 60s `Retry-After` cap — beyond that (or once retries are exhausted) a `RateLimitExceeded` is raised and the engine skips the rest of that endpoint's batches rather than hammering an already-limited API.

## REST API

FastAPI app (`src/rest_api/app.py`) served with uvicorn. Reads from dbt-transformed staging/intermediate schemas.

| Prefix | Endpoints |
|---|---|
| `/spotify` | `GET /tracks`, `/tracks/enriched`, `/tracks/{id}`, `/artists`, `/artists/{id}`, `/albums`, `/albums/{id}` |
| `/football` | `GET /teams`, `/teams/{id}` |
| `/mma` | `GET /fighters`, `/fighters/{id}` |
| `/health` | `GET /health` |

Interactive docs: `http://localhost:8000/docs`

## Setup

```bash
cd ..            # repo root — this package has no pyproject.toml of its own
uv sync
cd ingest
```

Create a `.env` (at the repo root) with PostgreSQL credentials plus whichever pipelines' credentials you're bootstrapping for the first time:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=

SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
SPOTIFY_REDIRECT_URL=
SPOTIFY_REFRESH_TOKEN=      # optional — omit to go through the browser auth flow on first run

TRAKT_CLIENT_ID=
TRAKT_CLIENT_SECRET=
TRAKT_REDIRECT_URL=
TRAKT_REFRESH_TOKEN=        # optional — same as above

SPORTS_API_KEY=
```

Apply migrations then run ingestion:

```bash
./migrations/upgrade.sh
uv run python main.py
```

## Migrations

Alembic manages the schema. Helper scripts in `migrations/`:

```bash
./migrations/upgrade.sh            # apply all pending migrations (default: head)
./migrations/upgrade.sh +1         # one step forward
./migrations/downgrade.sh          # roll back one step
./migrations/generate.sh "message" # generate a new migration file
./migrations/stamp_head.sh         # stamp current DB as head without running migrations
./migrations/status.sh             # show current revision
```

## Running the REST API

```bash
uv run uvicorn src.rest_api.app:app --reload
```

## Tests

```bash
uv run pytest -m "not integration"   # unit tests only (no DB required)
uv run pytest                        # all tests including integration (requires live DB)
```

## Requirements

- Python 3.12+
- PostgreSQL
- [uv](https://docs.astral.sh/uv/) for dependency management
