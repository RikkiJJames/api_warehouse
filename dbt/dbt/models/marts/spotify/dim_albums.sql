select
    album_id,
    spotify_album_id,
    album_name,
    album_uri,
    release_date,
    total_tracks,
    album_image_url
from {{ ref('album') }}
