select
    played_at,
    track_id   as spotify_track_id,
    track_duration_ms
from {{ ref('recently_played') }}
