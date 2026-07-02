select
    album_id,
    spotify_album_id,
    album_name,
    album_uri,
    release_date,
    total_tracks
from {{ ref('album') }}
