with movies as (
    select * from {{ ref('stg_watched_movies') }}
),

unique_movies as (
    select distinct on (trakt_movie_id)
        trakt_movie_id,
        tmdb_id,
        imdb_id,
        slug,
        title,
        year,
        runtime_mins,
        rating,
        votes,
        overview,
        tagline,
        released_date,
        genres,
        country,
        language,
        homepage,
        trailer,
        status,
        certification
    from movies
    where trakt_movie_id is not null
    order by trakt_movie_id, released_date
)

select * from unique_movies
