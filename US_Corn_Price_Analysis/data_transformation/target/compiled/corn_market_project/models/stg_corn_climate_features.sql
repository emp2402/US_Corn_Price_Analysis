with climate_source as (
    select * from `us-corn-data`.`us_corn_data`.`us_climate_data`
),

planting_source as (
    select * from `us-corn-data`.`us_corn_data_transformed`.`stg_corn_plantings`
),

daily_metrics as (
    select
        EXTRACT(YEAR FROM c.date) as year,
        c.date as weather_date,
        EXTRACT(DAYOFYEAR FROM c.date) as weather_doy,
        CAST(c.Precipitation as FLOAT64) as prcp,
        CAST(c.Max_Temp as FLOAT64) as tmax,
        p.planting_50_pct_doy
    from climate_source c
    inner join planting_source p on EXTRACT(YEAR FROM c.date) = p.year
),

aggregated_features as (
    select
        year,
        planting_50_pct_doy,

        -- 1. Rain Effectiveness (Unchanged)
        SUM(CASE 
            WHEN weather_doy BETWEEN 60 AND 181 THEN prcp 
            ELSE 0 
        END) as soil_prep_rain_cumulative,

        -- 2. NEW: Stress Degree Days (SDD)
        -- Baseline: 30°C (86°F). 
        -- If Avg Temp is 32°C, we add 2.0 to the score.
        SUM(CASE 
            WHEN weather_doy BETWEEN (planting_50_pct_doy + 60) AND (planting_50_pct_doy + 90)
            AND tmax > 30 
            THEN (tmax - 30) 
            ELSE 0 
        END) as heat_stress_index,

        -- 3. Post-Pollination Rain
        SUM(CASE 
            WHEN weather_doy BETWEEN (planting_50_pct_doy + 60) AND (planting_50_pct_doy + 90)
            THEN prcp 
            ELSE 0 
        END) as post_pollination_rain_cumulative

    from daily_metrics
    group by year, planting_50_pct_doy
)

select
    year,
    planting_50_pct_doy,
    
    SAFE_DIVIDE(soil_prep_rain_cumulative, planting_50_pct_doy) as rainfall_effectiveness_index,
    
    heat_stress_index as temp_stress_july_count,
    
    post_pollination_rain_cumulative as post_pollination_rain

from aggregated_features
order by year desc