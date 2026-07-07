FROM python:3.12-slim

WORKDIR /usr/app

# install uv
RUN pip install uv

COPY pyproject.toml uv.lock ./

# Force uv to use the container Python
RUN uv sync --frozen

COPY . .

ENV PATH="/usr/app/.venv/bin:$PATH"

WORKDIR /usr/app/dbt/dbt

CMD ["dbt", "build"]