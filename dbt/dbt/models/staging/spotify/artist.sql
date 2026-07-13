with source as (
    select * from {{ source('spotify', 'artist') }}
)

select
    id as artist_id,
    artist_id as spotify_artist_id,
    name as artist_name,
    uri as artist_uri,
    -- Spotify orders images largest-first; index 0 is the biggest available.
    images -> 0 ->> 'url' as artist_image_url
from source
where name is not null

