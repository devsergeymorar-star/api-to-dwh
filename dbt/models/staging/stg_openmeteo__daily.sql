with latest as (
    {{ latest_batch(source('raw', 'openmeteo')) }}
)

select
    concat(_record_key, '|', toString(_partition_date)) as weather_id,
    _partition_date as weather_date,
    _record_key as city,
    JSONExtractFloat(payload, 'latitude') as latitude,
    JSONExtractFloat(payload, 'longitude') as longitude,
    -- the connector requests exactly one day, so daily arrays have a single element
    JSONExtractFloat(payload, 'daily', 'temperature_2m_max', 1) as temperature_max_c,
    JSONExtractFloat(payload, 'daily', 'temperature_2m_min', 1) as temperature_min_c,
    JSONExtractFloat(payload, 'daily', 'precipitation_sum', 1) as precipitation_mm,
    JSONExtractFloat(payload, 'daily', 'wind_speed_10m_max', 1) as wind_speed_max_kmh,
    loaded_at
from latest
