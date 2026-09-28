with source as (
    select * from `us-corn-data`.`us_corn_data`.`us_corn_prices`
),

cleaned as (
    select
        CAST(Year as INT64) as year,
        Period as period,
        Data_Item as data_item,
        CAST(Value as FLOAT64) as price_value
    from source
),

filtered_prices as (
    select
        year,
        price_value
    from cleaned
    where 
        -- 1. Filter for Harvest Month
        period = 'NOV'
        
        -- 2. Filter for the correct UNIT (exclude 'PCT OF PARITY')
        -- We use LIKE to be safe, but specific enough to catch '$ / BU'
        AND data_item LIKE '%$ / BU'
),

final_unique as (
    select
        year,
        -- If duplicate rows still exist for the SAME metric (rare but possible),
        -- averaging them now is safe because they are the same unit.
        AVG(price_value) as price_per_bushel
    from filtered_prices
    group by year
)

select * from final_unique
order by year desc