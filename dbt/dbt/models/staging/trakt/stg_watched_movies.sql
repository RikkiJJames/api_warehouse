with source as (
    select * from {{ source('trakt', 'watched_movies') }}
)

select
    id,
    coalesce(history_id, id) as history_id,
    coalesce(watched_at, timestamp '1970-01-01') as watched_at,
    (movie_ids->>'trakt')::int     as trakt_movie_id,
    (movie_ids->>'tmdb')::int      as tmdb_id,
    movie_ids->>'imdb'             as imdb_id,
    movie_ids->>'slug'             as slug,
    movie_title                    as title,
    movie_year                     as year,
    movie_runtime                  as runtime_mins,
    movie_rating                   as rating,
    movie_votes                    as votes,
    movie_overview                 as overview,
    movie_tagline                  as tagline,
    movie_released                 as released_date,
    movie_genres                   as genres,
    movie_country                  as country,
    movie_language                 as language,
    movie_homepage                 as homepage,
    movie_trailer                  as trailer,
    movie_status                   as status,
    movie_certification            as certification
from source
where movie_title is not null
