with tracks as (
    select * from {{ ref('track') }}
),

artists as (
    select * from {{ ref('artist') }}
),

albums as (
    select * from {{ ref('album') }}
),

play_counts as (
    select
        track_id as spotify_track_id,
        count(*) as times_played,
        max(played_at) as most_recent_play,
        -- weekly
        count(*) filter (
            where played_at >= now() - interval '7 days'
        ) as plays_last_7_days,

        -- monthly
        count(*) filter (
            where played_at >= now() - interval '30 days'
        ) as plays_last_30_days,

        -- yearly
        count(*) filter (
            where played_at >= now() - interval '365 days'
        ) as plays_last_365_days
    from {{ ref('recently_played') }}
    group by track_id
)

select
    t.track_id,
    t.spotify_track_id,
    t.track_name,
    t.track_uri,
    t.duration_ms,
    t.explicit,
    t.popularity,

    ar.artist_id,
    ar.spotify_artist_id,
    ar.artist_name,
    ar.artist_uri,
    ar.artist_image_url,

    al.album_id,
    al.spotify_album_id,
    al.album_name,
    al.album_uri,
    al.release_date,
    al.total_tracks,
    al.album_image_url,

    coalesce(pc.times_played, 0) as times_played,
    coalesce(pc.plays_last_7_days, 0) as weekly_plays,
    coalesce(pc.plays_last_30_days, 0) as monthly_plays,
    coalesce(pc.plays_last_365_days, 0) as annual_plays,
    most_recent_play
from tracks t
left join artists ar on t.artist_id = ar.spotify_artist_id
left join albums al on t.album_id = al.spotify_album_id
left join play_counts pc on t.spotify_track_id = pc.spotify_track_id
