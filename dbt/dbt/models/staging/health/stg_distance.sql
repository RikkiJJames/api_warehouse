with source as (
    select * from {{ source('health', 'distance') }}
)

select
    date,
    round("distance_millimetersSum" / 1000.0, 1) as distance_meters
from source
where date is not null
