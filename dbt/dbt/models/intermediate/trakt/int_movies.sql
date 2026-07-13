with movies as (
    select * from {{ ref('stg_watched_movies') }}
),

movie_details as (
    select * from {{ ref('stg_movie_details') }}
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

select
    unique_movies.*,
    movie_details.poster_url
from unique_movies
left join movie_details on unique_movies.trakt_movie_id = movie_details.trakt_movie_id
