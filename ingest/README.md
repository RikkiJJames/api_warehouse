# data_warehouse

Python application that fetches raw data from the Spotify, Football, and MMA APIs and writes it into PostgreSQL. Also exposes a FastAPI REST API over the dbt-transformed tables.

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
| `football` | API key | `countries`, `leagues`, `teams`, `venues`, `seasons` |
| `mma` | API key | `fighters`, `categories`, `fighter_records` |

API config (base URLs, endpoints, parameters, field mappings) is declared in YAML files under `src/config/api/<source>/` and loaded at runtime via `ConfigLoader`.

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
uv sync
```

Create a `.env` with PostgreSQL credentials:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
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
