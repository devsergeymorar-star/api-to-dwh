-- An official exchange rate of zero or below means the feed or the parsing broke.
select *
from {{ ref('stg_nbk__rates') }}
where rate_kzt <= 0
