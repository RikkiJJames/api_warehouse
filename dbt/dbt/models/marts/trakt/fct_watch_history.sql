with movie_watches as (
    select
        history_id,
        watched_at,
        'movie'::text                                   as media_type,
        title,
        year,
        trakt_movie_id                                  as trakt_id,
        tmdb_id,
        imdb_id,
        coalesce(runtime_mins, 0)                       as runtime_mins,
        null::text                                      as show_title,
        null::int                                       as season,
        null::int                                       as episode_number,
        null::text                                      as network,
        genres,
        poster_url
    from {{ ref('stg_watched_movies') }}
),

episode_watches as (
    select
        history_id,
        watched_at,
        case
            when genres @> '["anime"]'::jsonb then 'anime'
            else 'episode'
        end                                             as media_type,
        episode_title                                   as title,
        show_year                                       as year,
        trakt_show_id                                   as trakt_id,
        show_tmdb_id                                    as tmdb_id,
        show_imdb_id                                    as imdb_id,
        coalesce(episode_runtime_mins, show_runtime_mins, 0) as runtime_mins,
        show_title,
        season,
        episode_number,
        network,
        genres,
        poster_url
    from {{ ref('stg_watched_episodes') }}
)

select * from movie_watches
union all
select * from episode_watches
order by watched_at desc
