-- Ephemeral: inlined as a CTE into any model that refs it — no warehouse object created.
-- Promoted to view only if consumed by 3+ downstream models.

WITH orders AS (

    SELECT * FROM {{ ref('stg_orders') }}

),

customers AS (

    SELECT * FROM {{ ref('stg_customers') }}

),

joined AS (

    SELECT
        o.order_id,
        o.customer_id,
        o.order_date,
        o.order_status,
        o.order_channel,
        o.shipping_city,
        o.shipping_state,
        o.shipping_country,
        o.order_amount,
        o.created_at                        AS order_created_at,
        o.updated_at                        AS order_updated_at,
        c.full_name                         AS customer_name,
        c.customer_segment,
        c.customer_tier,
        c.email                             AS customer_email,
        c.city                              AS customer_city,
        c.state                             AS customer_state,
        c.country                           AS customer_country

    FROM orders o
    LEFT JOIN customers c ON o.customer_id = c.customer_id

),

final AS (

    SELECT * FROM joined

)

SELECT * FROM final
