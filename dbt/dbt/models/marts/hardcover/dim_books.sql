with books as (
    select book_id, title, pages, release_date from {{ ref('stg_read_books') }}
    union all
    select book_id, title, pages, release_date from {{ ref('stg_currently_reading') }}
    union all
    select book_id, title, pages, release_date from {{ ref('stg_want_to_read') }}
)

select distinct on (book_id)
    book_id,
    title,
    pages,
    release_date
from books
order by book_id
