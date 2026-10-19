{{ config(order_by='(price_date, coin_id)') }}

with prices as (
    select * from {{ ref('stg_coingecko__prices') }}
),

usd as (
    select rate_date, rate_kzt as usd_kzt
    from {{ ref('stg_nbk__rates') }}
    where currency_code = 'USD'
)

select
    prices.price_date,
    prices.coin_id,
    prices.symbol,
    prices.coin_name,
    prices.price_usd,
    -- an unmatched LEFT JOIN yields 0 in ClickHouse: NULL until the NBK rate for that day is loaded
    nullIf(toFloat64(usd.usd_kzt), 0) as usd_kzt,
    prices.price_usd * usd_kzt as price_kzt,
    prices.market_cap_usd,
    prices.volume_usd
from prices
left join usd on prices.price_date = usd.rate_date
