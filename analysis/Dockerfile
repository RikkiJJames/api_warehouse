# Build context is the repo ROOT, not analysis/ — unlike ingest/Dockerfile and
# dbt/Dockerfile, this notebook's DataLoader imports `ingest.src.db`, and both
# packages are only resolvable together via the root pyproject.toml
# (packages.find: analysis*, ingest*). Build with:
#   docker build -f analysis/Dockerfile -t api-warehouse-analysis .
FROM python:3.12-slim

WORKDIR /usr/app

RUN pip install uv

COPY pyproject.toml uv.lock ./
COPY analysis ./analysis
COPY ingest ./ingest

RUN uv sync --frozen

ENV PATH="/usr/app/.venv/bin:$PATH"

EXPOSE 8080

# Cloud Run sets $PORT at runtime; default to 8080 for local `docker run`.
CMD ["sh", "-c", "marimo run analysis/src/notebooks/overview.py --headless --host 0.0.0.0 --port ${PORT:-8080}"]
