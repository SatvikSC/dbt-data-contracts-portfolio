{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='merge'
    )
}}

WITH orders AS (

    SELECT * FROM {{ ref('int_orders_with_customers') }}

),

dim_customers AS (

    SELECT
        customer_id,
        customer_key
    FROM {{ ref('dim_customers') }}

),

final AS (

    SELECT
        {{ dbt_utils.generate_surrogate_key(['order_id']) }}     AS order_key,
        o.order_id,
        o.customer_id,
        c.customer_key,
        o.order_date,
        o.order_status,
        o.order_channel,
        o.shipping_city,
        o.shipping_state,
        o.shipping_country,
        o.customer_segment,
        o.customer_tier,
        o.order_amount,
        o.order_created_at                                       AS created_at,
        o.order_updated_at                                       AS updated_at

    FROM orders o
    LEFT JOIN dim_customers c USING (customer_id)

    {% if is_incremental() %}
        WHERE o.order_updated_at > (SELECT MAX(updated_at) FROM {{ this }})
    {% endif %}

)

SELECT * FROM final
