with movie_genres as (
    select
        trakt_movie_id      as trakt_id,
        tmdb_id,
        imdb_id,
        title,
        year,
        'movie'             as media_type,
        'movie'             as content_type,
        rating,
        jsonb_array_elements_text(genres) as genre
    from {{ ref('dim_movies') }}
    where genres is not null
),

show_genres as (
    select
        trakt_show_id       as trakt_id,
        show_tmdb_id        as tmdb_id,
        show_imdb_id        as imdb_id,
        show_title          as title,
        show_year           as year,
        'show'              as media_type,
        content_type,
        show_rating         as rating,
        jsonb_array_elements_text(genres) as genre
    from {{ ref('dim_shows') }}
    where genres is not null
)

select * from movie_genres
union all
select * from show_genres
