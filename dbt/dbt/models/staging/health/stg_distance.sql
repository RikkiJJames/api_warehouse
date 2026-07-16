with source as (
    select * from {{ source('health', 'distance') }}
)

select
    date,
    "distance_metersSum" as distance_meters
from source
where date is not null
