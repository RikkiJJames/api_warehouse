# api_warehouse

A personal data warehouse that ingests API data (Spotify, Trakt, Football, MMA), transforms it with dbt, and surfaces analytics through interactive Marimo notebooks — orchestrated end-to-end by Airflow.

## Architecture

```
ingest/   ─── fetches from APIs ──▶ PostgreSQL (raw)
                                          │
airflow/  ─── orchestrates ingestion + dbt on a schedule
                                          │
dbt/      ───────────────────────────▶ transformed views/tables
                                          │
analysis/ ───────────────────────────▶ Marimo notebooks
ingest/ REST API ────────────────────▶ FastAPI
```

The repo contains four sub-projects, each sharing the single root `pyproject.toml` / `uv.lock`:

| Sub-project | Purpose |
|---|---|
| [`ingest/`](ingest/README.md) | Python ingestion app — fetches Spotify, Trakt, Football, and MMA data into PostgreSQL; exposes a FastAPI REST API |
| `airflow/` | Airflow DAGs and Docker Compose setup — schedules `ingest` then a `dbt build` |
| [`dbt/dbt/`](dbt/dbt/README.md) | dbt project — staging, intermediate, and mart models over PostgreSQL |
| `analysis/` | Marimo interactive notebooks for exploring the transformed data |

## Pipelines

| Pipeline | Auth | Notes |
|---|---|---|
| `spotify` | OAuth 2.0 | Recently played (incremental — only pulls plays since the last run), tracks/albums/artists (only ids not already stored are fetched) |
| `trakt` | OAuth 2.0 | Watched movies, watched episodes, watchlist movies, watchlist shows |
| `football` | API key | Countries, leagues, teams, venues, seasons |
| `mma` | API key | Fighters, categories, fight records |

OAuth refresh tokens rotate automatically and are persisted to the `config.api_config` table — no need to manually update `.env` after the first successful auth. All credentials (`client_id`/`client_secret`/`redirect_url`/`refresh_token`/`api_key`) are seeded from `.env` once and read from the DB afterwards, so scheduled runs (e.g. via Airflow) only need DB connection details, not the full credential set. See [`ingest/README.md`](ingest/README.md) for details.

## Docker images

`docker-push.sh` builds and pushes all three images to Docker Hub:

```bash
./docker-push.sh --image airflow|dbt|ingest|all [--tag <tag>]
```

Images are published as `rikkijames/api-warehouse-{airflow,dbt,ingest}:<tag>`. `dbt` and `ingest` build from the repo root (they need the shared root `pyproject.toml`/`uv.lock`); `airflow` builds from `airflow/`.

`docker-deploy.sh` pulls a pushed image and restarts the Airflow Compose stack with it:

```bash
./docker-deploy.sh --image airflow [--tag <tag>]
```

## Orchestration (Airflow)

`airflow/dags/api_ingestion.py` (`dag_id=api_ingestion_docker`) runs every 90 minutes: runs the `ingest` container, then a `dbt build` container, both via `DockerOperator` using the `neon_db` Airflow connection for database credentials.

```bash
cd airflow
docker compose up -d
```

Airflow UI: `http://localhost:8080` (default credentials: `airflow` / `airflow`).

## dbt

Three-layer model structure (staging → intermediate → marts) over the `spotify` and `trakt` sources. See [`dbt/dbt/README.md`](dbt/dbt/README.md).

## Notebooks

[Marimo](https://marimo.io) notebooks live in `analysis/src/notebooks/`:

| Notebook | Purpose |
|---|---|
| `spotify.py` | Spotify listening history — top tracks/artists/albums, popularity vs. plays, listening time |
| `trakt.py` | Trakt watch history — movies, shows, watchlist, genres |
| `overview.py` | Combined Spotify + Trakt dashboard — cross-source daily activity plus both notebooks' full content in tabs |

```bash
cd analysis/src
uv run marimo edit notebooks/overview.py
```

## Requirements

- Python 3.12+
- PostgreSQL
- Docker (for Airflow orchestration and image builds)
- [uv](https://docs.astral.sh/uv/) for dependency management

```bash
uv sync   # run from the repo root — all sub-projects share this environment
```
