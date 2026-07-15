with source as (
    select * from {{ source('trakt', 'show_details') }}
)

select
    ids_trakt as trakt_show_id,
    -- Trakt returns poster paths without a scheme (see docs.trakt.tv/docs/images).
    -- Prefer poster; fall back to clearart, then thumb, if a poster isn't set.
    'https://' || coalesce(
        images_poster ->> 0,
        images_clearart ->> 0,
        images_thumb ->> 0
    ) as poster_url
from source
where ids_trakt is not null
