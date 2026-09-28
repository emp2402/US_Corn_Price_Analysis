with supply as (
    select * from {{ ref('stg_corn_supply_demand') }}
),

prices as (
    select * from {{ ref('stg_corn_prices') }}
),

conditions as (
    select * from {{ ref('stg_corn_conditions') }}
),

climate as (
    select * from {{ ref('stg_corn_climate_features') }}
),

final_join as (
    select
        -- 1. Everything from Supply & Demand
        s.*,
        
        -- 2. Target Variable
        p.price_per_bushel,
        
        -- 3. Crop Condition
        c.avg_condition_pollination_index,
        
        -- 4. Climate Features
        cl.planting_50_pct_doy,        
        cl.rainfall_effectiveness_index,
        cl.temp_stress_july_count,
        cl.post_pollination_rain

    from supply s
    
    left join prices p on s.year = p.year
    left join conditions c on s.year = c.year
    left join climate cl on s.year = cl.year
)

select * from final_join
where price_per_bushel IS NOT NULL
order by year desc