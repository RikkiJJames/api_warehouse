with source as (
    select * from {{ source('health', 'active_minutes') }}
),

-- activeMinutesRollupByActivityLevel is a list of per-activity-level entries
-- (e.g. LIGHT/MODERATE/VIGOROUS) rather than one scalar — sum across them
-- for a single daily total. Field names here are a best-effort guess,
-- unverified against a live payload (see active_minutes.py) — check this
-- once real ingestion is running.
levels as (
    select
        source.date,
        (level_entry ->> 'activeMinutesSum')::int as active_minutes_sum
    from source,
        jsonb_array_elements(coalesce("activeMinutes_activeMinutesRollupByActivityLevel", '[]'::jsonb)) as level_entry
)

select
    date,
    sum(active_minutes_sum) as active_minutes
from levels
where date is not null
group by date
