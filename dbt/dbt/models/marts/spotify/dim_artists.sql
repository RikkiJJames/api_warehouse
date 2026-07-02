select
    artist_id,
    spotify_artist_id,
    artist_name,
    artist_uri
from {{ ref('artist') }}
