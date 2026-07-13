from pydantic import BaseModel
from datetime import datetime

class Track(BaseModel):
    track_id: int
    spotify_track_id: str | None
    track_name: str | None
    track_uri: str | None
    duration_ms: int | None
    explicit: bool | None
    popularity: int | None
    album_id: str | None
    artist_id: str | None

    model_config = {"from_attributes": True}


class Artist(BaseModel):
    artist_id: int
    spotify_artist_id: str | None
    artist_name: str | None
    artist_uri: str | None
    artist_image_url: str | None

    model_config = {"from_attributes": True}


class Album(BaseModel):
    album_id: int
    spotify_album_id: str | None
    album_name: str | None
    album_uri: str | None
    release_date: str | None
    total_tracks: int | None
    album_image_url: str | None

    model_config = {"from_attributes": True}


class TrackEnriched(BaseModel):
    track_id: int
    spotify_track_id: str | None
    track_name: str | None
    track_uri: str | None
    duration_ms: int | None
    explicit: bool | None
    popularity: int | None
    artist_id: int | None
    spotify_artist_id: str | None
    artist_name: str | None
    artist_uri: str | None
    artist_image_url: str | None
    album_id: int | None
    spotify_album_id: str | None
    album_name: str | None
    album_uri: str | None
    release_date: str | None
    total_tracks: int | None
    album_image_url: str | None
    times_played: int
    most_recent_play: datetime

    model_config = {"from_attributes": True}
