with planting as (
    select
        year,
        -- Feature 1: Approximate the Day of Year (DOY) where planting crossed 50%
        -- Logic: Take the first week where pct > 50, multiply by 7 to get rough DOY
        min(week_number) * 7 as planting_50pct_doy
    from {{ ref('stg_planting') }}
    where is_majority_planted = 1
    group by year
),

condition as (
    select
        year,
        -- Feature 2: Average Crop Condition during critical growing weeks (e.g. weeks 25-35)
        avg(condition_index) as avg_condition_index
    from {{ ref('stg_condition') }}
    -- Filter for critical weeks (July/Aug) to avoid noise from early/late season
    where week_number between 25 and 35
    group by year
),

weather as (
    select
        -- Extract Year from the date column
        extract(year from date) as year,
        -- Feature 3 & 4: Total Rain and Avg Temp for the year
        sum(precip) as total_annual_precip,
        avg(tmax) as avg_max_temp
    from {{ ref('stg_weather') }} -- Pointing to raw for now as we didn't make stg_weather
    group by 1
)

select
    p.year,
    p.planting_50pct_doy,
    c.avg_condition_index,
    w.total_annual_precip,
    w.avg_max_temp
from planting p
left join condition c on p.year = c.year
left join weather w on p.year = w.year