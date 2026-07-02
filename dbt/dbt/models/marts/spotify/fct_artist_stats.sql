with track_stats as (
    select * from {{ ref('fct_track_stats') }}
),

track_artists as (
    select
        spotify_track_id,
        spotify_artist_id
    from {{ ref('dim_tracks') }}
)

select
    ta.spotify_artist_id,
    count(distinct ta.spotify_track_id)                         as unique_tracks_played,
    sum(ts.times_played)                                        as times_played,
    sum(ts.total_listening_ms)                                  as total_listening_ms,
    round(sum(ts.total_listening_ms)::numeric / 3600000, 1)    as total_listening_hours,
    min(ts.first_played_at)                                     as first_played_at,
    max(ts.last_played_at)                                      as last_played_at,
    sum(ts.plays_last_7_days)                                   as plays_last_7_days,
    sum(ts.plays_last_30_days)                                  as plays_last_30_days,
    sum(ts.plays_last_365_days)                                 as plays_last_365_days
from track_stats ts
inner join track_artists ta on ts.spotify_track_id = ta.spotify_track_id
group by ta.spotify_artist_id
