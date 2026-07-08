with finished as (
    select
        book_id,
        pages,
        my_rating,
        read_finished_at
    from {{ ref('stg_read_books') }}
    where read_finished_at is not null
)

select
    date_trunc('year', read_finished_at)::date                        as year,
    count(*)                                                          as books_read,
    sum(coalesce(pages, 0))                                           as pages_read,
    round(avg(my_rating)::numeric, 2)                                 as avg_rating,
    round(sum(coalesce(pages, 0))::numeric / nullif(count(*), 0), 1)  as avg_pages_per_book
from finished
group by 1
order by 1 desc
