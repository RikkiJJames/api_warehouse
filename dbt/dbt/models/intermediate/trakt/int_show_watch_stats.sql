with episodes as (
    select * from {{ ref('stg_watched_episodes') }}
)

select
    trakt_show_id,
    show_title,
    count(*)                                                                as episodes_watched,
    count(distinct season)                                                  as seasons_watched,
    sum(coalesce(episode_runtime_mins, show_runtime_mins, 0))               as total_runtime_mins,
    min(watched_at)                                                         as first_watched_at,
    max(watched_at)                                                         as last_watched_at,
    count(*) filter (where watched_at >= now() - interval '7 days')         as episodes_last_7_days,
    count(*) filter (where watched_at >= now() - interval '30 days')        as episodes_last_30_days
from episodes
where trakt_show_id is not null
group by trakt_show_id, show_title
