with books as (
    select book_id, title, pages, release_date, cover_image_url from {{ ref('stg_read_books') }}
    union all
    select book_id, title, pages, release_date, cover_image_url from {{ ref('stg_currently_reading') }}
    union all
    select book_id, title, pages, release_date, cover_image_url from {{ ref('stg_want_to_read') }}
)

select distinct on (book_id)
    book_id,
    title,
    pages,
    release_date,
    cover_image_url
from books
-- Prefer a row that actually has a cover over one that doesn't, since the
-- same book can appear across read/currently_reading/want_to_read with
-- inconsistent image capture depending on when each was ingested.
order by book_id, cover_image_url is null
