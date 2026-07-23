---
title: Spotify
---

# Spotify

```sql spotify_range
select min(played_at) as since, max(played_at) as until
from warehouse.fct_play_history
```

<Tabs>
<Tab label="Tracks">

## Top Tracks

Rank every track you've played, ranked by whichever window matters to you right now.

<Dropdown name=metric title="Ranking metric" defaultValue="weekly_plays">
    <DropdownOption value="weekly_plays" valueLabel="Weekly Plays"/>
    <DropdownOption value="monthly_plays" valueLabel="Monthly Plays"/>
    <DropdownOption value="annual_plays" valueLabel="Annual Plays"/>
    <DropdownOption value="times_played" valueLabel="All Time"/>
</Dropdown>

<Slider name=top_n title="Top N" min=1 max=50 defaultValue=10 step=1/>

```sql top_tracks
select track_name, artist_name, album_name, popularity, weekly_plays, monthly_plays, annual_plays, times_played
from warehouse.int_track_enriched
order by ${inputs.metric.value} desc
limit ${inputs.top_n.value}
```

<DataTable data={top_tracks} rows={inputs.top_n.value}/>

## Your Listening, by Mainstream-ness

How your total plays break down across Spotify's popularity scale — every
track here has at least 1 play by definition, so this shows whether your
listening skews toward deep cuts or mainstream hits, rather than plays vs.
popularity directly.

```sql popularity_buckets
select
    case
        when popularity < 20 then '0–19 (deep cuts)'
        when popularity < 40 then '20–39'
        when popularity < 60 then '40–59'
        when popularity < 80 then '60–79'
        else '80–100 (mainstream)'
    end as popularity_bucket,
    min(popularity) as bucket_order,
    sum(times_played) as total_plays,
    count(distinct track_name) as track_count
from warehouse.int_track_enriched
group by 1
order by bucket_order
```

<BarChart data={popularity_buckets} x=popularity_bucket y=total_plays title="Your Listening, by Mainstream-ness"/>

## Plays by Track Duration

Total plays bucketed by track length, so you can see whether you gravitate
towards short, medium, or long cuts.

```sql duration_buckets
select
    case
        when duration_ms < 180000 then 'Short (<3 min)'
        when duration_ms < 300000 then 'Medium (3–5 min)'
        else 'Long (>5 min)'
    end as duration_bin,
    min(duration_ms) as bucket_order,
    sum(times_played) as total_plays,
    count(distinct track_name) as track_count
from warehouse.int_track_enriched
group by 1
order by bucket_order
```

<BarChart data={duration_buckets} x=duration_bin y=total_plays title="Plays by Track Duration"/>

## Tracks by Decade

Filter your library down to one or more release decades and see which
tracks from those eras get the most plays.

```sql track_decades
select distinct (try_cast(substr(release_date, 1, 4) as int) / 10) * 10 as decade
from warehouse.int_track_enriched
where release_date is not null
order by decade desc
```

<Dropdown data={track_decades} name=decade value=decade multiple=true>
    <DropdownOption value="%" valueLabel="All Decades"/>
</Dropdown>

```sql decade_tracks
select track_name, artist_name, (try_cast(substr(release_date, 1, 4) as int) / 10) * 10 as decade, times_played, popularity
from warehouse.int_track_enriched
where release_date is not null
and (
    '%' in ${inputs.decade.value}
    or (try_cast(substr(release_date, 1, 4) as int) / 10) * 10 in ${inputs.decade.value}
)
order by decade, times_played desc
```

<DataTable data={decade_tracks}/>

## Listening Time Selector

Drag the slider to set a lookback window and see total listening time logged within it.

<Slider name=lookback_days title="Number of Days" min=0 max=365 defaultValue=0 step=1/>

```sql listening_window
select round(coalesce(sum(track_duration_ms) filter (
    where played_at >= now() - interval '${inputs.lookback_days.value} days'
), 0)::numeric / 3600000, 1) as total_hours
from warehouse.fct_play_history
```

<BigValue data={listening_window} value=total_hours fmt=num1 title="Listening time in window (hrs)"/>

</Tab>
<Tab label="Artists">

## Top Artists

Every artist you've listened to, ranked by total plays, with unique track
count and average popularity.

```sql top_artists
select
    artist_name,
    sum(times_played) as times_played,
    count(distinct track_name) as unique_tracks,
    round(avg(popularity), 1) as avg_popularity
from warehouse.int_track_enriched
group by artist_name
order by times_played desc
limit 20
```

<DataTable data={top_artists}/>

## Artist Deep Dive

Pick an artist below to see every track of theirs you've played and your
total listening time with them.

```sql artist_options
select distinct artist_name from warehouse.int_track_enriched order by artist_name
```

<Dropdown data={artist_options} name=artist_selector value=artist_name title="Select artist"/>

```sql artist_detail
select track_name, album_name, popularity, times_played, weekly_plays, monthly_plays,
    round(sum(duration_ms * times_played) over ()::numeric / 3600000, 1) as artist_total_hours
from warehouse.int_track_enriched
where artist_name = '${inputs.artist_selector.value}'
order by times_played desc
```

**Total listening time:** {artist_detail[0] ? artist_detail[0].artist_total_hours + ' hrs' : '—'}

<DataTable data={artist_detail}>
    <Column id=track_name/>
    <Column id=album_name/>
    <Column id=popularity/>
    <Column id=times_played/>
    <Column id=weekly_plays/>
    <Column id=monthly_plays/>
</DataTable>

</Tab>
<Tab label="Albums">

## Album Leaderboard

Albums ranked by total plays across their tracks, alongside how much of each
album you've actually explored.

```sql top_albums
select
    album_name,
    artist_name,
    sum(times_played) as times_played,
    count(distinct track_name) as unique_tracks,
    max(total_tracks) as total_tracks
from warehouse.int_track_enriched
group by album_name, artist_name
order by times_played desc
limit 30
```

<DataTable data={top_albums}/>

## Explicit vs Clean

Share of your total plays that come from explicit vs. clean tracks.

```sql explicit_split
select
    case when explicit then 'Explicit' else 'Clean' end as label,
    sum(times_played) as times_played
from warehouse.int_track_enriched
group by explicit
```

<BarChart data={explicit_split} x=label y=times_played title="Explicit vs Clean — Play Count"/>

</Tab>
</Tabs>
