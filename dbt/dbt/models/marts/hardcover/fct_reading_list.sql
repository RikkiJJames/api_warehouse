-- Ingest only ever inserts into the raw Hardcover tables (ON CONFLICT DO
-- NOTHING), so when a book moves shelf — want-to-read -> currently reading ->
-- read — its old row stays behind and the same user_book_id ends up in more
-- than one table. Keep each book only on its furthest-along shelf: anything
-- in stg_read_books is dropped entirely, and currently_reading wins over
-- want_to_read.
with currently_reading as (
    select
        user_book_id,
        'currently_reading'   as status,
        read_started_at       as status_at,
        book_id,
        title,
        pages,
        release_date,
        cover_image_url
    from {{ ref('stg_currently_reading') }} c
    where not exists (
        select 1 from {{ ref('stg_read_books') }} r
        where r.user_book_id = c.user_book_id
    )
),

want_to_read as (
    select
        user_book_id,
        'want_to_read'        as status,
        created_at            as status_at,
        book_id,
        title,
        pages,
        release_date,
        cover_image_url
    from {{ ref('stg_want_to_read') }} w
    where not exists (
        select 1 from {{ ref('stg_read_books') }} r
        where r.user_book_id = w.user_book_id
    )
      and not exists (
        select 1 from {{ ref('stg_currently_reading') }} c
        where c.user_book_id = w.user_book_id
    )
)

select * from currently_reading
union all
select * from want_to_read
order by status_at desc
