from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.rest_api.dependencies import get_db
from src.rest_api.schemas.spotify import Album, Artist, Track, TrackEnriched

router = APIRouter(prefix="/spotify", tags=["spotify"])

STAGING = "staging"
INTERMEDIATE = "intermediate"

Db = Annotated[Session, Depends(get_db)]


@router.get("/tracks", response_model=list[Track])
def list_tracks(db: Db, limit: int = 50, offset: int = 0):
    rows = db.execute(
        text(f"SELECT * FROM {STAGING}.track ORDER BY track_id LIMIT :limit OFFSET :offset"),
        {"limit": limit, "offset": offset},
    ).mappings().all()
    return rows

@router.get("/tracks/enriched", response_model=list[TrackEnriched])
def list_tracks_enriched(db: Db, limit: int = 50, offset: int = 0):
    rows = db.execute(
        text(
            f"SELECT * FROM {INTERMEDIATE}.int_track_enriched"
            " ORDER BY track_id LIMIT :limit OFFSET :offset"
        ),
        {"limit": limit, "offset": offset},
    ).mappings().all()
    return rows


@router.get("/tracks/{track_id}", response_model=Track)
def get_track(track_id: int, db: Db):
    row = db.execute(
        text(f"SELECT * FROM {STAGING}.track WHERE track_id = :track_id"),
        {"track_id": track_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Track not found")
    return row


@router.get("/artists", response_model=list[Artist])
def list_artists(db: Db, limit: int = 50, offset: int = 0):
    rows = db.execute(
        text(f"SELECT * FROM {STAGING}.artist ORDER BY artist_id LIMIT :limit OFFSET :offset"),
        {"limit": limit, "offset": offset},
    ).mappings().all()
    return rows


@router.get("/artists/{artist_id}", response_model=Artist)
def get_artist(artist_id: int, db: Db):
    row = db.execute(
        text(f"SELECT * FROM {STAGING}.artist WHERE artist_id = :artist_id"),
        {"artist_id": artist_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Artist not found")
    return row


@router.get("/albums", response_model=list[Album])
def list_albums(db: Db, limit: int = 50, offset: int = 0):
    rows = db.execute(
        text(f"SELECT * FROM {STAGING}.album ORDER BY album_id LIMIT :limit OFFSET :offset"),
        {"limit": limit, "offset": offset},
    ).mappings().all()
    return rows


@router.get("/albums/{album_id}", response_model=Album)
def get_album(album_id: int, db: Db):
    row = db.execute(
        text(f"SELECT * FROM {STAGING}.album WHERE album_id = :album_id"),
        {"album_id": album_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Album not found")
    return row
