---
title: Fitness
---

# Fitness

Google Health daily activity — steps, distance, calories and active minutes.

<Tabs>
<Tab label="Overview">

```sql fitness_summary
with s as (
    select date, steps, active_minutes from warehouse.fct_daily_activity
)
select
    max(steps) as max_steps,
    (select date from s order by steps desc nulls last limit 1) as max_steps_date,
    round(avg(steps)) as avg_steps,
    round(avg(active_minutes)) as avg_active_minutes,
    count(*) filter (where steps >= 10000) as days_10k,
    sum(steps) filter (where date >= date_trunc('year', now())) as total_steps_this_year
from s
```

```sql fitness_yoy
with s as (select date, steps from warehouse.fct_daily_activity),
this_ytd as (
    select avg(steps) as avg_steps from s where date >= date_trunc('year', now())
),
last_ytd as (
    select avg(steps) as avg_steps from s
    where date >= date_trunc('year', now()) - interval '1 year'
    and date < date_trunc('year', now()) - interval '1 year' + (now() - date_trunc('year', now()))
)
select
    case when last_ytd.avg_steps > 0
        then round(((this_ytd.avg_steps - last_ytd.avg_steps) / last_ytd.avg_steps * 100)::numeric, 1)
        else null
    end as yoy_pct
from this_ytd, last_ytd
```

## At a Glance

<Grid cols=3>
  <BigValue data={fitness_summary} value=max_steps title="Max Steps" fmt=num0/>
  <BigValue data={fitness_summary} value=avg_steps title="Avg Daily Steps" fmt=num0/>
  <BigValue data={fitness_yoy} value=yoy_pct title="Steps YoY" fmt=pct1/>
</Grid>
<Grid cols=3>
  <BigValue data={fitness_summary} value=total_steps_this_year title="Total Steps This Year" fmt=num0/>
  <BigValue data={fitness_summary} value=avg_active_minutes title="Avg Active Minutes" fmt=num0/>
  <BigValue data={fitness_summary} value=days_10k title="Days ≥ 10k Steps" fmt=num0/>
</Grid>

## Daily Trend

```sql fitness_daily
select date, steps, round(distance_meters / 1000, 2) as distance_km, total_calories, active_minutes
from warehouse.fct_daily_activity
order by date
```

<Dropdown name=fitness_metric title="Metric" defaultValue="steps">
    <DropdownOption value="steps" valueLabel="Steps"/>
    <DropdownOption value="distance_km" valueLabel="Distance (km)"/>
    <DropdownOption value="total_calories" valueLabel="Calories Burned"/>
    <DropdownOption value="active_minutes" valueLabel="Active Minutes"/>
</Dropdown>

<BarChart data={fitness_daily} x=date y={inputs.fitness_metric.value} title="Daily {inputs.fitness_metric.label}"/>

</Tab>
<Tab label="Trends">

## Average Steps by Day of Week

Which days I tend to move the most, averaged across all history.

```sql steps_by_weekday
select
    strftime(date, '%A') as weekday,
    (extract(dow from date)::int + 6) % 7 as weekday_order,
    round(avg(steps)) as avg_steps
from warehouse.fct_daily_activity
where steps is not null
group by 1, 2
order by weekday_order
```

<BarChart data={steps_by_weekday} x=weekday y=avg_steps title="Average Steps by Day of Week"/>

## Total Steps by Month

```sql steps_by_month
select date_trunc('month', date)::date as month, sum(steps) as total_steps
from warehouse.fct_daily_activity
where steps is not null
group by 1
order by 1
```

<BarChart data={steps_by_month} x=month y=total_steps title="Total Steps by Month"/>

</Tab>
<Tab label="Data">

## Recent Daily Activity

```sql fitness_recent
select date, steps, distance_meters, total_calories, active_minutes
from warehouse.fct_daily_activity
order by date desc
limit 30
```

<DataTable data={fitness_recent}/>

</Tab>
</Tabs>
