with source as (
    select * from {{ source('trakt', 'watchlist_shows') }}
)

select
    id,
    watchlist_id,
    rank,
    listed_at,
    notes,
    (show_ids->>'trakt')::int      as trakt_show_id,
    (show_ids->>'tmdb')::int       as tmdb_id,
    show_ids->>'imdb'              as imdb_id,
    show_ids->>'slug'              as slug,
    show_title                     as title,
    show_year                      as year
from source
where show_title is not null
