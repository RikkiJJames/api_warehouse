# Media Overview (Evidence)

An [Evidence.dev](https://evidence.dev) recreation of `analysis/src/notebooks/overview.py` —
Spotify, Trakt, Hardcover and Google Health data straight from the
`api_warehouse` Postgres marts, as SQL-in-markdown pages instead of a marimo
notebook.

Pages: `pages/index.md` (overview), `pages/spotify.md`, `pages/trakt.md`,
`pages/hardcover.md`, `pages/fitness.md`.

## Setup

```bash
npm install
cp .env.example .env   # fill in the Postgres user/password
npm run sources        # test the DB connection, cache query results
npm run dev             # http://localhost:3000
```

The DB connection is configured in `sources/warehouse/connection.yaml` (host/port/database
come from `.env`, not committed — see `.env.example`). For local dev, point
`EVIDENCE_SOURCE__WAREHOUSE__HOST`/`PORT` at a
[Cloud SQL Auth Proxy](https://cloud.google.com/sql/docs/postgres/sql-proxy)
tunnel rather than the instance directly, same as the `cloudsql-proxy`
sidecar the `ingest`/`dbt` Cloud Run jobs use (see `ingest/src/db/core/db.py`).

## Deploying

```bash
npm run build
```

Builds a static site to `./build`. See [the docs](https://docs.evidence.dev/deployment/self-host/)
for hosting options (Cloud Run + Cloud Build, matching the `home-app` site in
`terraform/website.tf`, works fine for a static build).

## Learning More

- [Docs](https://docs.evidence.dev/)
- [Component reference](https://docs.evidence.dev/components/all-components)
- [Github](https://github.com/evidence-dev/evidence)
