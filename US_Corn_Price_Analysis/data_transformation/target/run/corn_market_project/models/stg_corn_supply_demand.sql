
  
    

    create or replace table `us-corn-data`.`us_corn_data_transformed`.`stg_corn_supply_demand`
      
    
    

    
    OPTIONS()
    as (
      with source as (
    select * from `us-corn-data`.`us_corn_data`.`us_corn_supply_demand`
),

cleaned as (
    select
        -- 1. Fix the Year (Float -> Integer)
        CAST(Year as INT64) as year,

        Planted_Acres as planted_acres,
        Harvested_Acres as harvested_acres,
        Actual_Yield as actual_yield,
        Production as production,
        Exports as exports,
        Imports as imports,
        Total_Supply as total_supply,
        All_Dom_Use as all_dom_use,
        Total_Usage as total_usage,
        Ending_Stocks as ending_stocks,

    from source
),

calculated as (
    select
        *,
        -- 3. Calculate Stock-to-Use Ratio
        -- Formula: (Ending Stocks / Total Usage)
        -- Use SAFE_DIVIDE to prevent errors if Usage is ever 0
        SAFE_DIVIDE(ending_stocks, total_usage) as stock_to_use_ratio

    from cleaned
)

select * from calculated
order by year desc
    );
  