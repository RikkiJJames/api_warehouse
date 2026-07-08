with source as (
    select * from {{ source('hardcover', 'currently_reading') }}
)

select
    id,
    user_book_id,
    book_id,
    book_title          as title,
    book_pages          as pages,
    book_release_date   as release_date,
    read_started_at,
    updated_at
from source
where book_title is not null
