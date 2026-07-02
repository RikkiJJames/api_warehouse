with source as (
    select * from {{ source('spotify', 'track') }}
)

select
    id as track_id,
    track_id as spotify_track_id,
    name as track_name,
    uri as track_uri,
    duration_ms,
    explicit,
    popularity,
    album_id,
    artist_id
from source
where name is not null

