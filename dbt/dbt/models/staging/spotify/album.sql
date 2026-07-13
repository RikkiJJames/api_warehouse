with source as (
    select * from {{ source('spotify', 'album') }}
)

select
    id as album_id,
    album_id as spotify_album_id,
    name as album_name,
    uri as album_uri,
    release_date as release_date,
    total_tracks,
    -- Spotify orders images largest-first; index 0 is the biggest available.
    images -> 0 ->> 'url' as album_image_url
from source
where name is not null
