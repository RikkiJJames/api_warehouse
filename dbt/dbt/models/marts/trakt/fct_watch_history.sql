with movie_watches as (
    select
        w.history_id,
        w.watched_at,
        'movie'::text                                   as media_type,
        w.title,
        w.year,
        w.trakt_movie_id                                as trakt_id,
        w.tmdb_id,
        w.imdb_id,
        coalesce(w.runtime_mins, 0)                     as runtime_mins,
        null::text                                      as show_title,
        null::int                                       as season,
        null::int                                       as episode_number,
        null::text                                      as network,
        w.genres,
        d.poster_url
    from {{ ref('stg_watched_movies') }} w
    left join {{ ref('stg_movie_details') }} d on w.trakt_movie_id = d.trakt_movie_id
),

episode_watches as (
    select
        e.history_id,
        e.watched_at,
        case
            when e.genres @> '["anime"]'::jsonb then 'anime'
            else 'episode'
        end                                             as media_type,
        e.episode_title                                 as title,
        e.show_year                                     as year,
        e.trakt_show_id                                 as trakt_id,
        e.show_tmdb_id                                   as tmdb_id,
        e.show_imdb_id                                   as imdb_id,
        coalesce(e.episode_runtime_mins, e.show_runtime_mins, 0) as runtime_mins,
        e.show_title,
        e.season,
        e.episode_number,
        e.network,
        e.genres,
        d.poster_url
    from {{ ref('stg_watched_episodes') }} e
    left join {{ ref('stg_show_details') }} d on e.trakt_show_id = d.trakt_show_id
)

select * from movie_watches
union all
select * from episode_watches
order by watched_at desc
