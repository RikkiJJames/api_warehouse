select *
from {{ ref('dim_shows') }}
where content_type = 'anime'
