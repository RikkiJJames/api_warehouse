with source as (
    select * from {{ source('health', 'total_calories') }}
)

select
    date,
    "totalCalories_kcalSum" as total_calories
from source
where date is not null
