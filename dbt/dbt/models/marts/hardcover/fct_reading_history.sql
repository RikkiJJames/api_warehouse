select
    user_book_id,
    book_id,
    title,
    pages,
    cover_image_url,
    my_rating,
    read_started_at,
    read_finished_at
from {{ ref('stg_read_books') }}
order by read_finished_at desc
