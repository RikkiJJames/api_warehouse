---
title: Trakt
---

# Trakt

<Tabs>
<Tab label="Watch History">

## Activity

Number of movies and episodes watched per day — a quick way to spot binge sessions.

```sql watch_daily
select watched_at::date as date, count(*) as count
from warehouse.fct_watch_history
where watched_at is not null
group by 1
order by 1
```

<BarChart data={watch_daily} x=date y=count title="Daily Watch Activity"/>

## Timeline

The full watch log, filterable by media type, most recent first.

```sql media_types
select distinct media_type from warehouse.fct_watch_history
```

<Dropdown data={media_types} name=media_type_filter value=media_type multiple=true defaultValue={media_types.map(d => d.media_type)}/>

```sql watch_timeline
select watched_at, media_type, title, show_title, season, episode_number, runtime_mins
from warehouse.fct_watch_history
where media_type in ${inputs.media_type_filter.value}
order by watched_at desc
```

<DataTable data={watch_timeline}/>

</Tab>
<Tab label="Movies">

## Top Movies

Every movie I've watched, sortable by watch count, total runtime, or rating.

<Dropdown name=movie_sort title="Sort by" defaultValue="watch_count">
    <DropdownOption value="watch_count" valueLabel="Watch Count"/>
    <DropdownOption value="total_runtime_hours" valueLabel="Runtime"/>
    <DropdownOption value="rating" valueLabel="Rating"/>
</Dropdown>

<Slider name=movie_top_n title="Top N" min=5 max=50 defaultValue=20 step=5/>

```sql top_movies
select m.title, m.year, m.rating, m.runtime_mins, s.watch_count, s.total_runtime_hours, s.last_watched_at
from warehouse.dim_movies m
left join warehouse.fct_movie_stats s on m.trakt_movie_id = s.trakt_movie_id
order by ${inputs.movie_sort.value} desc nulls last
limit ${inputs.movie_top_n.value}
```

<DataTable data={top_movies}/>

## Rating Distribution

How the community rating is spread out across movies I've watched.

```sql movie_ratings
select m.rating
from warehouse.dim_movies m
where m.rating is not null
```

<Histogram data={movie_ratings} x=rating title="Movie Rating Distribution"/>

</Tab>
<Tab label="Shows">

## Top Shows

Shows ranked by episodes watched, completion percentage, or rating.

<Dropdown name=show_sort title="Sort by" defaultValue="episodes_watched">
    <DropdownOption value="episodes_watched" valueLabel="Episodes Watched"/>
    <DropdownOption value="completion_pct" valueLabel="Completion %"/>
    <DropdownOption value="show_rating" valueLabel="Rating"/>
</Dropdown>

<Slider name=show_top_n title="Top N" min=5 max=50 defaultValue=20 step=5/>

```sql top_shows
select sh.show_title, sh.show_year, sh.network, sh.content_type, sh.show_rating,
    st.episodes_watched, st.seasons_watched, st.completion_pct, st.total_runtime_hours
from warehouse.dim_shows sh
left join warehouse.fct_show_stats st on sh.trakt_show_id = st.trakt_show_id
order by ${inputs.show_sort.value} desc nulls last
limit ${inputs.show_top_n.value}
```

<DataTable data={top_shows}/>

</Tab>
<Tab label="Watchlist">

## Watchlist

Movies and shows queued up but not yet watched.

```sql watchlist
select * from warehouse.fct_watchlist order by rank
```

<DataTable data={watchlist}>
    <Column id=rank/>
    <Column id=title/>
    <Column id=year/>
    <Column id=media_type/>
    <Column id=listed_at/>
    <Column id=notes/>
</DataTable>

</Tab>
<Tab label="Genres">

## Genre Breakdown

Which genres dominate my watch history, split by movies vs. shows.

```sql genre_stats
select * from warehouse.fct_genre_stats order by title_count desc limit 15
```

<BarChart
    data={genre_stats}
    x=title_count
    y=genre
    series=media_type
    swapXY=true
    title="Top Genres by Title Count"
/>

<DataTable data={genre_stats}/>

</Tab>
</Tabs>
