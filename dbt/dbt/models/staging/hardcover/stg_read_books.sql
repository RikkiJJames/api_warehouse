with source as (
    select * from {{ source('hardcover', 'read_books') }}
)

select
    id,
    user_book_id,
    book_id,
    book_title          as title,
    book_pages          as pages,
    book_release_date   as release_date,
    book_image ->> 'url' as cover_image_url,
    my_rating,
    read_started_at,
    read_finished_at,
    updated_at
from source
where book_title is not null
