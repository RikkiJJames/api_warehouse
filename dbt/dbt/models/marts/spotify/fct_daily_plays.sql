-- Daily rollup of fct_play_history for the overview notebook, which only
-- needs per-day counts/durations — pulling every play event into pandas on
-- each dashboard load was the slowest part of its startup.
select
    played_at::date                     as date,
    count(*)                            as plays,
    coalesce(sum(track_duration_ms), 0) as duration_ms
from {{ ref('fct_play_history') }}
group by 1
