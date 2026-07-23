---
title: Overview
---

# Media Overview

A single pane of glass over everything I've listened to, watched, and read —
pulled straight from my `api_warehouse` marts.

- **Spotify** — every track play, enriched with popularity, duration and
  per-track play counts across the last week, month, year and all-time.
- **Trakt** — movie and show watch history, ratings, watchlist and genre
  breakdown.
- **Hardcover** — books finished, currently reading, and want-to-read, with
  yearly reading stats.
- **Fitness** — daily steps, distance, calories and active minutes from
  Google Health.

Jump into [Spotify](/spotify), [Trakt](/trakt), [Hardcover](/hardcover), or
[Fitness](/fitness) for source-specific breakdowns, filters and leaderboards.

## At a Glance

A quick pulse check across all four sources — how much history has been
captured so far and how far back it goes.

```sql spotify_stats
select count(*) as plays, min(played_at) as since
from warehouse.fct_play_history
```

```sql trakt_stats
select count(*) as items, min(watched_at) as since
from warehouse.fct_watch_history
```

```sql hardcover_stats
select count(*) as books, min(read_finished_at) as since
from warehouse.fct_reading_history
where read_finished_at is not null
```

```sql fitness_overview_stats
select round(avg(steps)) as avg_steps, min(date) as since
from warehouse.fct_daily_activity
```

<Grid cols=4>
  <BigValue data={spotify_stats} value=plays title="Spotify plays logged" fmt=num0/>
  <BigValue data={trakt_stats} value=items title="Trakt items watched" fmt=num0/>
  <BigValue data={hardcover_stats} value=books title="Hardcover books read" fmt=num0/>
  <BigValue data={fitness_overview_stats} value=avg_steps title="Avg daily steps" fmt=num0/>
</Grid>

<small>
Spotify since {spotify_stats[0].since ? spotify_stats[0].since.toLocaleDateString() : 'no plays yet'} ·
Trakt since {trakt_stats[0].since ? trakt_stats[0].since.toLocaleDateString() : 'nothing watched yet'} ·
Hardcover since {hardcover_stats[0].since ? hardcover_stats[0].since.toLocaleDateString() : 'nothing finished yet'} ·
Fitness since {fitness_overview_stats[0].since ? fitness_overview_stats[0].since.toLocaleDateString() : 'nothing logged yet'}
</small>

## Highlights

### 🎧 Top Artists This Month

```sql top_artists_month
select
    artist_name,
    sum(monthly_plays) as monthly_plays,
    count(distinct case when monthly_plays > 0 then track_name end) as tracks_this_month,
    max(artist_image_url) as artist_image_url
from warehouse.int_track_enriched
group by artist_name
having sum(monthly_plays) > 0
order by monthly_plays desc
limit 5
```

<DataTable data={top_artists_month} rows=5>
    <Column id=artist_image_url contentType=image title=" "/>
    <Column id=artist_name title="Artist"/>
    <Column id=monthly_plays title="Plays this month"/>
    <Column id=tracks_this_month title="Tracks"/>
</DataTable>

### 🎬 Recently Watched

```sql recent_movies
select title, year, watched_at, poster_url
from warehouse.fct_watch_history
where media_type = 'movie' and watched_at is not null
order by watched_at desc
limit 5
```

<DataTable data={recent_movies} rows=5>
    <Column id=poster_url contentType=image title=" "/>
    <Column id=title/>
    <Column id=year/>
    <Column id=watched_at title="Watched"/>
</DataTable>

### 📚 Recently Finished

```sql recent_books
select title, read_finished_at, cover_image_url, my_rating
from warehouse.fct_reading_history
where read_finished_at is not null
order by read_finished_at desc
limit 5
```

<DataTable data={recent_books} rows=5>
    <Column id=cover_image_url contentType=image title=" "/>
    <Column id=title/>
    <Column id=read_finished_at title="Finished"/>
    <Column id=my_rating title="Rating"/>
</DataTable>

## Daily Activity Across Sources

Every logged Spotify play, Trakt watch, and finished Hardcover book, plotted
by day so I can spot binges, dry spells, and how the three habits overlap
over time.

```sql combined_daily_activity
select date_trunc('day', played_at)::date as date, count(*) as count, 'Spotify' as source
from warehouse.fct_play_history
group by 1

union all

select watched_at::date as date, count(*) as count, 'Trakt' as source
from warehouse.fct_watch_history
where watched_at is not null
group by 1

union all

select read_finished_at::date as date, count(*) as count, 'Hardcover' as source
from warehouse.fct_reading_history
where read_finished_at is not null
group by 1

order by date
```

<LineChart
    data={combined_daily_activity}
    x=date
    y=count
    series=source
    title="Daily Activity — Spotify Plays, Trakt Watches & Hardcover Finishes"
/>

<Alert status="info">
Hover any point for the exact count, or head to the Spotify, Trakt, Hardcover,
or Fitness pages for source-specific leaderboards and filters.
</Alert>
