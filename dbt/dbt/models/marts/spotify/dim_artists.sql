select
    artist_id,
    spotify_artist_id,
    artist_name,
    artist_uri,
    artist_image_url
from {{ ref('artist') }}
