with source as (
    select * from {{ source('spotify', 'recently_played') }}
)

select * from source