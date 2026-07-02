with source as (
    select * from {{ source('spotify', 'artist') }}
)

select
    id as artist_id,
    artist_id as spotify_artist_id,
    name as artist_name,
    uri as artist_uri
from source
where name is not null

