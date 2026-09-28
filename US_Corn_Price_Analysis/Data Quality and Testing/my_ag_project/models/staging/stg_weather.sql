with source as (
    select * from {{ source('us_corn_data_source', 'us_climate_data') }}
),

renamed as (
    select
        date,
        Precipitation as precip,
        -- [FIX] Rename 'Max_Temp' to 'tmax' so the next model can find it
        Max_Temp as tmax
    from source
)

select * from renamed