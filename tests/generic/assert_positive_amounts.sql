{% test assert_positive_amounts(model, column_name) %}

-- Fails if any row has a zero or negative value in the target column.
-- Used on fact_orders.order_amount and any future monetary columns.

SELECT *
FROM {{ model }}
WHERE {{ column_name }} <= 0

{% endtest %}
