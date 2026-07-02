from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.rest_api.dependencies import get_db
from src.rest_api.schemas.mma import Fighter

router = APIRouter(prefix="/mma", tags=["mma"])

Db = Annotated[Session, Depends(get_db)]


@router.get("/fighters", response_model=list[Fighter])
def list_fighters(db: Db, limit: int = 50, offset: int = 0, category: str | None = None):
    query = "SELECT * FROM mma.fighters"
    params: dict = {"limit": limit, "offset": offset}
    if category:
        query += " WHERE category ILIKE :category"
        params["category"] = f"%{category}%"
    query += " ORDER BY fighter_id LIMIT :limit OFFSET :offset"
    rows = db.execute(text(query), params).mappings().all()
    return rows


@router.get("/fighters/{fighter_id}", response_model=Fighter)
def get_fighter(fighter_id: int, db: Db):
    row = db.execute(
        text("SELECT * FROM mma.fighters WHERE fighter_id = :fighter_id"),
        {"fighter_id": fighter_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Fighter not found")
    return row
