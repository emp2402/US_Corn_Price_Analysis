with supply_demand as (
    select * from {{ ref('stg_wasde') }}
),

annual_aggs as (
    select * from {{ ref('int_annual_aggregates') }}
),

final as (
    select
        -- Primary Key
        sd.year,

        -- Target Variable
        sd.yield_per_acre,

        -- Key Features (Supply/Demand)
        sd.total_production_bushels as production_bushels,
        sd.harvested_acres,
        sd.planted_acres,
        -- Checklist: "Ratio must be positive" (Calculated here)
        safe_divide(sd.ending_stocks, sd.total_usage_bushels) as stocks_to_use_ratio,

        -- Key Features (Weather & Crop)
        aa.planting_50pct_doy,
        aa.avg_condition_index,
        aa.total_annual_precip,
        aa.avg_max_temp

    from supply_demand sd
    -- INNER JOIN: Enforces "Feature Completeness" by dropping years with missing data
    inner join annual_aggs aa on sd.year = aa.year
)

select * from final