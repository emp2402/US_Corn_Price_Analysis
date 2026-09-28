with source as (
    select * from `us-corn-data`.`us_corn_data`.`us_corn_conditions`
),

base_data as (
    select
        CAST(Year as INT64) as year,
        -- Extract Week Number (1-52) from the date
        EXTRACT(ISOWEEK FROM PARSE_DATE('%Y-%m-%d', Week_Ending)) as week_num,
        Data_Item,
        CAST(Value as INT64) as pct_value
    from source
),

pivoted as (
    select
        year,
        week_num,
        -- Pivot: Create a column for each category
        -- We use MAX() here to grab the value for that specific category in that specific week
        MAX(CASE WHEN Data_Item LIKE '%VERY POOR%' THEN pct_value ELSE 0 END) as vp,
        MAX(CASE WHEN Data_Item LIKE '%PCT POOR%' THEN pct_value ELSE 0 END) as p,
        MAX(CASE WHEN Data_Item LIKE '%FAIR%' THEN pct_value ELSE 0 END) as f,
        MAX(CASE WHEN Data_Item LIKE '%PCT GOOD%' THEN pct_value ELSE 0 END) as g,
        MAX(CASE WHEN Data_Item LIKE '%EXCELLENT%' THEN pct_value ELSE 0 END) as e
    from base_data
    group by year, week_num
),

calculated_index as (
    select
        year,
        week_num,
        vp, p, f, g, e,
        
        -- Calculate Total (Should be ~100, but we calculate to be safe)
        (vp + p + f + g + e) as total_pct,

        -- THE FORMULA: Weighted Average
        -- Scale: 100 (All Very Poor) to 500 (All Excellent)
        SAFE_DIVIDE(
            (vp * 1) + (p * 2) + (f * 3) + (g * 4) + (e * 5),
            (vp + p + f + g + e)
        ) as condition_index

    from pivoted
    -- Filter: Only keep the critical Pollination Window (Weeks 28-32)
    where week_num BETWEEN 28 AND 32
)

select
    year,
    -- Aggregate to one single number per year (The Average during Pollination)
    ROUND(AVG(condition_index), 2) as avg_condition_pollination_index
from calculated_index
group by year
order by year desc