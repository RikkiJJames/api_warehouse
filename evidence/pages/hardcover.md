---
title: Hardcover
---

# Hardcover

<Tabs>
<Tab label="Read Books">

## Top Books

Every finished book, sortable by when you finished it, your rating, or page count.

<Dropdown name=book_sort title="Sort by" defaultValue="read_finished_at">
    <DropdownOption value="read_finished_at" valueLabel="Finished Date"/>
    <DropdownOption value="my_rating" valueLabel="Rating"/>
    <DropdownOption value="pages" valueLabel="Pages"/>
</Dropdown>

<Slider name=book_top_n title="Top N" min=5 max=50 defaultValue=20 step=5/>

```sql top_books
select title, pages, my_rating, read_started_at, read_finished_at
from marts.fct_reading_history
order by ${inputs.book_sort.value} desc nulls last
limit ${inputs.book_top_n.value}
```

<DataTable data={top_books}/>

## Rating Distribution

How your personal book ratings are spread out.

```sql book_ratings
select my_rating from marts.fct_reading_history where my_rating is not null
```

<Histogram data={book_ratings} x=my_rating title="Personal Rating Distribution"/>

</Tab>
<Tab label="Reading List">

## Currently Reading & Want to Read

Everything on deck — filter by status to see what's in progress vs. still on the list.

```sql reading_list_statuses
select distinct status from marts.fct_reading_list
```

<Dropdown data={reading_list_statuses} name=reading_status value=status multiple=true defaultValue={reading_list_statuses.map(d => d.status)}/>

```sql filtered_reading_list
select status, status_at, title, pages, release_date
from marts.fct_reading_list
where status in ${inputs.reading_status.value}
order by status_at desc
```

<DataTable data={filtered_reading_list}/>

</Tab>
<Tab label="Stats">

## Books Read per Year

Books finished per calendar year, alongside pages and average rating.

```sql reading_stats
select * from marts.fct_reading_stats order by year desc
```

<BarChart data={reading_stats} x=year y=books_read title="Books Read per Year"/>

<DataTable data={reading_stats}/>

</Tab>
</Tabs>
