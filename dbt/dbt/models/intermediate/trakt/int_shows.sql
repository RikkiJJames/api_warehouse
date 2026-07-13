with episodes as (
    select * from {{ ref('stg_watched_episodes') }}
),

show_details as (
    select * from {{ ref('stg_show_details') }}
),

unique_shows as (
    select distinct on (trakt_show_id)
        trakt_show_id,
        show_tmdb_id,
        show_imdb_id,
        show_slug,
        show_title,
        show_year,
        network,
        show_status,
        show_rating,
        show_overview,
        genres,
        country,
        show_runtime_mins,
        show_homepage,
        show_certification,
        show_first_aired,
        show_aired_episodes,
        show_airs,
        case
            when genres @> '["anime"]'::jsonb     then 'anime'
            when genres @> '["animation"]'::jsonb  then 'animation'
            when genres @> '["documentary"]'::jsonb then 'documentary'
            else 'show'
        end as content_type
    from episodes
    where trakt_show_id is not null
    order by trakt_show_id, show_first_aired
)

select
    unique_shows.*,
    show_details.poster_url
from unique_shows
left join show_details on unique_shows.trakt_show_id = show_details.trakt_show_id
