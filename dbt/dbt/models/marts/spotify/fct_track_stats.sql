select
    rp.track_id                                                                     as spotify_track_id,
    count(*)                                                                        as times_played,
    min(rp.played_at)                                                               as first_played_at,
    max(rp.played_at)                                                               as last_played_at,
    sum(coalesce(t.duration_ms, 0))                                                 as total_listening_ms,
    round(sum(coalesce(t.duration_ms, 0))::numeric / 3600000, 1)                    as total_listening_hours,
    count(*) filter (where rp.played_at >= now() - interval '7 days')               as plays_last_7_days,
    count(*) filter (where rp.played_at >= now() - interval '30 days')              as plays_last_30_days,
    count(*) filter (where rp.played_at >= now() - interval '365 days')             as plays_last_365_days
from {{ ref('recently_played') }} rp
left join {{ ref('track') }} t on rp.track_id = t.spotify_track_id
group by rp.track_id
