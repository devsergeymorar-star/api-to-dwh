with latest as (
    {{ latest_batch(source('raw', 'coingecko')) }}
)

select
    concat(_record_key, '|', toString(_partition_date)) as price_id,
    _partition_date as price_date,
    _record_key as coin_id,
    upper(JSONExtractString(payload, 'symbol')) as symbol,
    JSONExtractString(payload, 'name') as coin_name,
    JSONExtractFloat(payload, 'market_data', 'current_price', 'usd') as price_usd,
    JSONExtractFloat(payload, 'market_data', 'market_cap', 'usd') as market_cap_usd,
    JSONExtractFloat(payload, 'market_data', 'total_volume', 'usd') as volume_usd,
    loaded_at
from latest
