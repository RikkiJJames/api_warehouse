with steps as (
    select * from {{ ref('stg_steps') }}
),

distance as (
    select * from {{ ref('stg_distance') }}
),

total_calories as (
    select * from {{ ref('stg_total_calories') }}
),

active_minutes as (
    select * from {{ ref('stg_active_minutes') }}
),

-- Each metric is fetched independently, so a day can be present in one and
-- missing from another (e.g. mid-backfill) — union the dates seen across
-- all four instead of picking one as the anchor.
dates as (
    select date from steps
    union
    select date from distance
    union
    select date from total_calories
    union
    select date from active_minutes
)

select
    dates.date,
    steps.steps,
    distance.distance_meters,
    total_calories.total_calories,
    active_minutes.active_minutes
from dates
left join steps on steps.date = dates.date
left join distance on distance.date = dates.date
left join total_calories on total_calories.date = dates.date
left join active_minutes on active_minutes.date = dates.date
order by dates.date
