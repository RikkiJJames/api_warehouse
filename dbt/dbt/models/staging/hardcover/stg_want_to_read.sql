with source as (
    select * from {{ source('hardcover', 'want_to_read') }}
)

select
    id,
    user_book_id,
    book_id,
    book_title          as title,
    book_pages          as pages,
    book_release_date   as release_date,
    created_at
from source
where book_title is not null
