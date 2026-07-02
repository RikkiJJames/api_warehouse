with source as (
    select * from {{ source('trakt', 'watchlist_movies') }}
)

select
    id,
    watchlist_id,
    rank,
    listed_at,
    notes,
    (movie_ids->>'trakt')::int     as trakt_movie_id,
    (movie_ids->>'tmdb')::int      as tmdb_id,
    movie_ids->>'imdb'             as imdb_id,
    movie_ids->>'slug'             as slug,
    movie_title                    as title,
    movie_year                     as year
from source
where movie_title is not null
