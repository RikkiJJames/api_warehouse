with movie_genres as (
    select
        jsonb_array_elements_text(genres)   as genre,
        'movie'::text                       as media_type,
        trakt_movie_id                      as trakt_id,
        title,
        runtime_mins
    from {{ ref('stg_watched_movies') }}
    where genres is not null
),

show_genres as (
    select
        jsonb_array_elements_text(genres)   as genre,
        content_type                        as media_type,
        trakt_show_id                       as trakt_id,
        show_title                          as title,
        show_runtime_mins                   as runtime_mins
    from {{ ref('int_shows') }}
    where genres is not null
),

all_genres as (
    select * from movie_genres
    union all
    select * from show_genres
)

select
    genre,
    media_type,
    count(distinct trakt_id)                    as title_count,
    sum(coalesce(runtime_mins, 0))              as total_runtime_mins
from all_genres
group by genre, media_type
order by title_count desc
