with stats as (
    select * from {{ ref('int_show_watch_stats') }}
),

shows as (
    select trakt_show_id, show_aired_episodes
    from {{ ref('dim_shows') }}
)

select
    s.trakt_show_id,
    st.episodes_watched,
    st.seasons_watched,
    st.total_runtime_mins,
    round(st.total_runtime_mins::numeric / 60, 1)                           as total_runtime_hours,
    st.first_watched_at,
    st.last_watched_at,
    st.episodes_last_7_days,
    st.episodes_last_30_days,
    round(
        100.0 * st.episodes_watched / nullif(s.show_aired_episodes, 0),
        1
    )                                                                       as completion_pct
from stats st
left join shows s on st.trakt_show_id = s.trakt_show_id
