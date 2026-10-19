with latest as (
    {{ latest_batch(source('raw', 'nbk')) }}
),

parsed as (
    select
        _partition_date as rate_date,
        _record_key as currency_code,
        JSONExtractString(payload, 'fullname') as currency_name,
        toDecimal64(JSONExtractString(payload, 'description'), 4) as rate_kzt_per_quant,
        toUInt32(JSONExtractString(payload, 'quant')) as quant,
        -- the date the feed itself reports; equals rate_date on normal days
        toDate(parseDateTime(JSONExtractString(payload, 'rates_date'), '%d.%m.%Y')) as published_rates_date,
        loaded_at
    from latest
)

select
    concat(currency_code, '|', toString(rate_date)) as rate_id,
    rate_date,
    currency_code,
    currency_name,
    quant,
    rate_kzt_per_quant,
    -- some currencies are quoted per 10 or 100 units
    rate_kzt_per_quant / quant as rate_kzt,
    published_rates_date,
    loaded_at
from parsed
