-- Evidence's parquet writer produces an invalid file for a truly empty
-- result set (crashes the dev server on load with "too small to be a
-- Parquet file"), so guarantee at least one row here — no books finished
-- yet means marts.fct_reading_stats is genuinely empty. The placeholder
-- is filtered back out in pages/hardcover.md (where year is not null).
select * from marts.fct_reading_stats
union all
select
    null::date as year,
    0 as books_read,
    0 as pages_read,
    null::numeric as avg_rating,
    null::numeric as avg_pages_per_book
where not exists (select 1 from marts.fct_reading_stats)
