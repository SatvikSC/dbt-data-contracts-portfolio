WITH source AS (

    SELECT * FROM {{ source('raw_ecommerce', 'orders') }}

),

renamed AS (

    SELECT
        order_id,
        customer_id,
        CAST(order_date   AS DATE)              AS order_date,
        order_status,
        channel                                 AS order_channel,
        shipping_city,
        shipping_state,
        shipping_country,
        CAST(total_amount AS DECIMAL(12, 2))    AS order_amount,
        CAST(created_at   AS TIMESTAMP)         AS created_at,
        CAST(updated_at   AS TIMESTAMP)         AS updated_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
