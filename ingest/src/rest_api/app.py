from fastapi import FastAPI

from src.rest_api.routers import football, mma, spotify

app = FastAPI(
    title="Sports Warehouse API",
    description="REST API for dbt-transformed sports and music data",
    version="1.0.0",
)

app.include_router(spotify.router)
app.include_router(football.router)
app.include_router(mma.router)


@app.get("/health")
def health():
    return {"status": "ok"}
