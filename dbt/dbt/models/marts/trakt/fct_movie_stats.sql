with watch_events as (
    select
        trakt_movie_id,
        watched_at,
        runtime_mins
    from {{ ref('stg_watched_movies') }}
    where trakt_movie_id is not null
)

select
    trakt_movie_id,
    count(*)                                                        as watch_count,
    min(watched_at)                                                 as first_watched_at,
    max(watched_at)                                                 as last_watched_at,
    sum(coalesce(runtime_mins, 0))                                  as total_runtime_mins,
    round(sum(coalesce(runtime_mins, 0))::numeric / 60, 1)          as total_runtime_hours,
    count(*) filter (where watched_at >= now() - interval '7 days') as watches_last_7_days,
    count(*) filter (where watched_at >= now() - interval '30 days') as watches_last_30_days
from watch_events
group by trakt_movie_id
