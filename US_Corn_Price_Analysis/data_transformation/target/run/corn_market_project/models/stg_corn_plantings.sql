
  
    

    create or replace table `us-corn-data`.`us_corn_data_transformed`.`stg_corn_plantings`
      
    
    

    
    OPTIONS()
    as (
      with source as (
    select * from `us-corn-data`.`us_corn_data`.`us_corn_plantings`
),

cleaned as (
    select
        -- 1. Standardize Year
        CAST(Year as INT64) as year,
        
        -- 2. Parse the Date (Column 'Week Ending' became 'Week_Ending')
        PARSE_DATE('%Y-%m-%d', Week_Ending) as measurement_date,
        
        -- 3. Value is the Percentage (0-100)
        CAST(Value as INT64) as progress_pct,
        
        -- 4. Keep Data_Item just for the safety check below
        Data_Item as data_item

    from source
    -- Safety Check: Even though the scraper filters this, we double-check here.
    where Data_Item LIKE '%PCT PLANTED%'
),

calc_threshold as (
    select
        year,
        -- Find the EARLIEST date where progress was >= 50%
        MIN(measurement_date) as date_reached_50_pct
    from cleaned
    where progress_pct >= 50
    group by year
)

select
    year,
    -- Convert that date into a simple integer (Day of Year 1-365)
    -- Example: May 20th becomes ~140
    EXTRACT(DAYOFYEAR FROM date_reached_50_pct) as planting_50_pct_doy
from calc_threshold
order by year desc
    );
  