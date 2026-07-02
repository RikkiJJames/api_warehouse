select
    track_id                                                                        as spotify_track_id,
    count(*)                                                                        as times_played,
    min(played_at)                                                                  as first_played_at,
    max(played_at)                                                                  as last_played_at,
    sum(coalesce(track_duration_ms, 0))                                             as total_listening_ms,
    round(sum(coalesce(track_duration_ms, 0))::numeric / 3600000, 1)               as total_listening_hours,
    count(*) filter (where played_at >= now() - interval '7 days')                 as plays_last_7_days,
    count(*) filter (where played_at >= now() - interval '30 days')                as plays_last_30_days,
    count(*) filter (where played_at >= now() - interval '365 days')               as plays_last_365_days
from {{ ref('recently_played') }}
group by track_id
