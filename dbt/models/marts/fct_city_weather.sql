{{ config(order_by='(city, weather_date)') }}

select
    city,
    weather_date,
    temperature_min_c,
    temperature_max_c,
    (temperature_min_c + temperature_max_c) / 2 as temperature_avg_c,
    avg((temperature_min_c + temperature_max_c) / 2) over (
        partition by city
        order by weather_date
        rows between 6 preceding and current row
    ) as temperature_avg_7d_c,
    precipitation_mm,
    wind_speed_max_kmh
from {{ ref('stg_openmeteo__daily') }}
