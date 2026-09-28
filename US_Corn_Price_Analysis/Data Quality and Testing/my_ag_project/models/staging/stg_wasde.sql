with source as (
    select * from {{ source('us_corn_data_source', 'us_corn_supply_demand') }}
),

renamed as (
    select
        -- Rename columns to match what we used before
        cast(Year as int64) as year,
        Planted_Acres as planted_acres,
        Harvested_Acres as harvested_acres,
        Actual_Yield as yield_per_acre,
        Production as total_production_bushels,
        Total_Supply as total_supply_bushels,
        Total_Usage as total_usage_bushels,
        Ending_Stocks as ending_stocks
    from source
)

select * from renamed