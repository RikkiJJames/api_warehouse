with currently_reading as (
    select
        user_book_id,
        'currently_reading'   as status,
        read_started_at       as status_at,
        book_id,
        title,
        pages,
        release_date
    from {{ ref('stg_currently_reading') }}
),

want_to_read as (
    select
        user_book_id,
        'want_to_read'        as status,
        created_at            as status_at,
        book_id,
        title,
        pages,
        release_date
    from {{ ref('stg_want_to_read') }}
)

select * from currently_reading
union all
select * from want_to_read
order by status_at desc
