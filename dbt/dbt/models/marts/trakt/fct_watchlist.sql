with watchlist_movies as (
    select
        watchlist_id,
        listed_at,
        rank,
        notes,
        'movie'         as media_type,
        trakt_movie_id  as trakt_id,
        tmdb_id,
        imdb_id,
        slug,
        title,
        year
    from {{ ref('stg_watchlist_movies') }}
),

watchlist_shows as (
    select
        watchlist_id,
        listed_at,
        rank,
        notes,
        'show'          as media_type,
        trakt_show_id   as trakt_id,
        tmdb_id,
        imdb_id,
        slug,
        title,
        year
    from {{ ref('stg_watchlist_shows') }}
)

select * from watchlist_movies
union all
select * from watchlist_shows
order by rank
