WITH source AS (

    SELECT * FROM {{ source('raw_ecommerce', 'customers') }}

),

renamed AS (

    SELECT
        customer_id,
        first_name,
        last_name,
        first_name || ' ' || last_name          AS full_name,
        LOWER(email)                            AS email,
        phone,
        segment                                 AS customer_segment,
        tier                                    AS customer_tier,
        city,
        state,
        country,
        CAST(created_at AS TIMESTAMP)           AS created_at,
        CAST(updated_at AS TIMESTAMP)           AS updated_at

    FROM source

),

final AS (

    SELECT * FROM renamed

)

SELECT * FROM final
