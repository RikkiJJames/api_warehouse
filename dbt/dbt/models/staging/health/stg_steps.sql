with source as (
    select * from {{ source('health', 'steps') }}
)

select
    date,
    "steps_countSum" as steps
from source
where date is not null
