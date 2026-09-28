with source as (
    select * from {{ source('us_corn_data_source', 'us_corn_plantings') }}
),

renamed as (
    select
        Year as year,
        Week_Ending as week_ending,
        Value as pct_planted
    from source
    where Data_Item = 'CORN - PROGRESS, PREVIOUS YEAR, MEASURED IN PCT PLANTED'
       OR Data_Item = 'CORN - PROGRESS, MEASURED IN PCT PLANTED'
)

select
    year,
    cast(week_ending as date) as week_ending_date,

    -- [NEW] Calculate the week number from the date
    extract(week from cast(week_ending as date)) as week_number,

    pct_planted,
    case when pct_planted >= 50 then 1 else 0 end as is_majority_planted

from renamed