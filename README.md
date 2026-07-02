# api_warehouse

A personal data warehouse that ingests API data (Spotify, football, MMA), transforms it with dbt, and surfaces analytics through interactive Marimo notebooks.

## Architecture

```
data_warehouse/ ─── fetches from APIs ──▶ PostgreSQL (raw)
                                               │
                          data_ingestion/ ─────┤ (Airflow orchestrates ingestion + dbt)
                                               │
                          warehouse_dbt/ ───────▶ transformed views/tables
                                               │
                          api_notebooks/ ───────▶ Marimo notebooks
                          data_warehouse/ REST API ▶ FastAPI
```

The repo contains four sub-projects:

| Sub-project | Purpose |
|---|---|
| `data_warehouse/` | Python ingestion app — fetches Spotify, Football, and MMA data into PostgreSQL; exposes a FastAPI REST API |
| `data_ingestion/` | Airflow DAGs and Docker setup — schedules `data_warehouse` ingestion then dbt runs |
| `warehouse_dbt/` | dbt project — staging, intermediate, and mart models over PostgreSQL |
| `api_notebooks/` | Marimo interactive notebooks for exploring the transformed data |

## data_warehouse

Python application that fetches raw data from the Spotify, Football, and MMA APIs and writes it into PostgreSQL. Also exposes a FastAPI REST API over the dbt-transformed tables.

**Pipelines:**

| Pipeline | Auth | Notes |
|---|---|---|
| `spotify` | OAuth 2.0 (refresh token) | Recently played, tracks, albums, artists |
| `football` | API key | Countries, leagues, teams, venues, seasons |
| `mma` | API key | Fighters, categories, fight records |

API config (base URLs, endpoints, params) is declared in YAML files under `src/config/api/<source>/`.

**REST API** (`src/rest_api/`) — FastAPI served via uvicorn:

| Prefix | Routes |
|---|---|
| `/spotify` | `GET /tracks`, `/tracks/enriched`, `/tracks/{id}`, `/artists`, `/artists/{id}`, `/albums`, `/albums/{id}` |
| `/football` | `GET /teams`, `/teams/{id}` |
| `/mma` | `GET /fighters`, `/fighters/{id}` |

**DB schema** managed with Alembic. Migration helpers in `migrations/`:

```bash
./migrations/upgrade.sh        # apply all pending migrations
./migrations/upgrade.sh +1     # one step forward
./migrations/downgrade.sh      # roll back one step
./migrations/generate.sh "msg" # generate a new migration
./migrations/status.sh         # show current revision
```

### Setup

```bash
cd data_warehouse
uv sync
```

Configure a `.env` with your PostgreSQL connection:

```
DB_HOST=
DB_PORT=
DB_NAME=
DB_USER=
DB_PASSWORD=
```

Run migrations then the ingestion:

```bash
./migrations/upgrade.sh
uv run python main.py
```

### Running the REST API

```bash
uv run uvicorn src.rest_api.app:app --reload
```

API docs available at `http://localhost:8000/docs`.

### Tests

```bash
uv run pytest -m "not integration"   # unit tests only
uv run pytest                        # includes integration (requires live DB)
```

---

## data_ingestion

Apache Airflow setup (CeleryExecutor) that orchestrates ingestion and transformation on a schedule.

**DAGs:**

- `dags/spotify_ingestion.py` — runs every 90 minutes: pulls from the Spotify API via a Docker container (`rikkijames/ingestion-app:latest`), then triggers a dbt build (`rikkijames/api_warehouse:latest`). Both tasks use a `neondb` Airflow connection for database credentials.

**Structure:**

```
dags/     → Airflow DAG definitions
config/   → airflow.cfg
```

### Setup

Requires Docker and a configured Airflow `neondb` connection with your PostgreSQL credentials.

```bash
cd data_ingestion
docker compose up -d
```

The Airflow UI is available at `http://localhost:8080` (default credentials: `airflow` / `airflow`).

---

## warehouse_dbt

dbt project targeting PostgreSQL with a three-layer model structure:

```
staging/     → views  — clean raw API data (renamed columns, filtered nulls)
intermediate/ → views  — enriched, joined models
marts/        → tables — final analytics-ready tables
```

**Current models:**

- `staging/spotify/` — `album`, `artist`, `track`, `recently_played`
- `intermediate/spotify/` — `int_track_enriched` (joins tracks, artists, albums, and play counts with weekly/monthly/annual aggregates)

**Sources:** `spotify` (recently played, tracks, albums, artists), `football`, `mma`

### Setup

```bash
cd warehouse_dbt
uv sync
```

Configure a `profiles.yml` pointing at your PostgreSQL instance with profile name `api_warehouse`.

```bash
# Run via dbt directly
dbt build

# Or via Docker
docker build -t api-dbt .
docker run --env-file .env api-dbt
```

## api_notebooks

[Marimo](https://marimo.io) notebooks for interactive data exploration, backed by the dbt-transformed tables.

**Current notebooks:**

- `src/notebooks/spotify.py` — top tracks by play count, top artists, tracks by decade, listening duration

### Setup

```bash
cd api_notebooks
uv sync
cp .env.example .env  # fill in DB credentials
```

**Required `.env` variables:**

```
DB_HOST=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_PORT=
```

### Running a notebook

```bash
marimo edit src/notebooks/spotify.py
```

## Requirements

- Python 3.12+
- PostgreSQL
- [uv](https://docs.astral.sh/uv/) for dependency management
