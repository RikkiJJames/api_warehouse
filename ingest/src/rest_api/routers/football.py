from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.rest_api.dependencies import get_db
from src.rest_api.schemas.football import Team

router = APIRouter(prefix="/football", tags=["football"])

STAGING = "sports_warehouse_staging"

Db = Annotated[Session, Depends(get_db)]


@router.get("/teams", response_model=list[Team])
def list_teams(db: Db, limit: int = 50, offset: int = 0, country: str | None = None):
    query = f"SELECT * FROM {STAGING}.stg_football_teams"
    params: dict = {"limit": limit, "offset": offset}
    if country:
        query += " WHERE team_country ILIKE :country"
        params["country"] = f"%{country}%"
    query += " ORDER BY team_id LIMIT :limit OFFSET :offset"
    rows = db.execute(text(query), params).mappings().all()
    return rows


@router.get("/teams/{team_id}", response_model=Team)
def get_team(team_id: int, db: Db):
    row = db.execute(
        text(f"SELECT * FROM {STAGING}.stg_football_teams WHERE team_id = :team_id"),
        {"team_id": team_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Team not found")
    return row
