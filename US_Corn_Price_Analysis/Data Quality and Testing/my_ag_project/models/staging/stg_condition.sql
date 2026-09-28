with source as (
    select * from {{ source('us_corn_data_source', 'us_corn_conditions') }}
),

renamed as (
    select
        Year as year,
        Week_Ending as week_ending,
        extract(week from cast(Week_Ending as date)) as week_number,
        State as state_name,
        Data_Item,
        Value as pct_value
    from source
    -- Filter to only include the condition rows you found
    where Data_Item LIKE '%CORN - CONDITION%'
),

final as (
    select
        *,
        -- [FIX] Extract the rating from the 'Data_Item' text string
        case
            when Data_Item LIKE '%PCT EXCELLENT' then 5
            when Data_Item LIKE '%PCT GOOD' then 4
            when Data_Item LIKE '%PCT FAIR' then 3
            -- Important: Check 'VERY POOR' before 'POOR' so we don't mix them up!
            when Data_Item LIKE '%PCT VERY POOR' then 1
            when Data_Item LIKE '%PCT POOR' then 2
            else null
        end as condition_index
    from renamed
)

select * from final