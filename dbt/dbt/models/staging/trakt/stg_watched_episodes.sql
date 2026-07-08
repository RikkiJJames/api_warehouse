with source as (
    select * from {{ source('trakt', 'watched_episodes') }}
)

select
    id,
    coalesce(history_id, id) as history_id,
    coalesce(watched_at, timestamp '1970-01-01') as watched_at,
    (show_ids->>'trakt')::int      as trakt_show_id,
    (show_ids->>'tmdb')::int       as show_tmdb_id,
    show_ids->>'imdb'              as show_imdb_id,
    show_ids->>'slug'              as show_slug,
    show_title,
    show_year,
    show_network                   as network,
    show_status,
    show_rating,
    show_overview,
    show_genres                    as genres,
    show_country                   as country,
    show_runtime                   as show_runtime_mins,
    show_homepage,
    show_certification,
    show_first_aired,
    show_aired_episodes,
    show_airs,
    (episode_ids->>'trakt')::int   as trakt_episode_id,
    episode_season                 as season,
    episode_number,
    episode_number_abs,
    episode_title,
    episode_runtime                as episode_runtime_mins,
    episode_rating,
    episode_overview,
    episode_first_aired
from source
where show_title is not null
