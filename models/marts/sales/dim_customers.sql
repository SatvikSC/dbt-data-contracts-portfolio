-- Dimension table: current-state customer records built from the SCD Type 2 snapshot.
-- Historical rows live in snap_customers; this model exposes only the active record
-- per customer (dbt_valid_to IS NULL).

WITH snapshot AS (

    SELECT * FROM {{ ref('snap_customers') }}

),

current_records AS (

    SELECT * FROM snapshot
    WHERE dbt_valid_to IS NULL

),

final AS (

    SELECT
        {{ dbt_utils.generate_surrogate_key(['customer_id']) }}  AS customer_key,
        customer_id,
        first_name,
        last_name,
        LOWER(email)                            AS email,
        phone,
        segment                                 AS customer_segment,
        tier                                    AS customer_tier,
        city,
        state,
        country,
        CAST(created_at   AS TIMESTAMP)         AS created_at,
        CAST(updated_at   AS TIMESTAMP)         AS updated_at,
        CAST(dbt_valid_from AS TIMESTAMP)       AS scd_valid_from,
        dbt_scd_id                              AS scd_id

    FROM current_records

)

SELECT * FROM final
