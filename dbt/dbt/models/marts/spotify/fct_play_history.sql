select
    rp.played_at,
    rp.track_id   as spotify_track_id,
    t.duration_ms as track_duration_ms
from {{ ref('recently_played') }} rp
left join {{ ref('track') }} t on rp.track_id = t.spotify_track_id
