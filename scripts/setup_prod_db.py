"""
Create workspace.raw schema in Databricks with synthetic data.
Equivalent of scripts/setup_ci_db.py but targets a Databricks SQL Warehouse.

Requires:
    pip install databricks-sql-connector  (already installed as a dbt-databricks dep)

Environment variables:
    DBT_DATABRICKS_HOST       your-workspace.azuredatabricks.net
    DBT_DATABRICKS_HTTP_PATH  /sql/1.0/warehouses/your-warehouse-id
    DBT_DATABRICKS_TOKEN      dapiXXXXXXXXXXXXXX

Usage:
    python scripts/setup_prod_db.py
"""

import os
import databricks.sql


def _cursor():
    host = os.environ["DBT_DATABRICKS_HOST"]
    http_path = os.environ["DBT_DATABRICKS_HTTP_PATH"]
    token = os.environ["DBT_DATABRICKS_TOKEN"]
    conn = databricks.sql.connect(
        server_hostname=host,
        http_path=http_path,
        access_token=token,
    )
    return conn


def setup() -> None:
    with _cursor() as conn:
        cur = conn.cursor()

        cur.execute("CREATE SCHEMA IF NOT EXISTS workspace.raw")
        print("Schema ready: workspace.raw")

        # ── customers (20 rows) ─────────────────────────────────────────────
        cur.execute("""
            CREATE OR REPLACE TABLE workspace.raw.customers AS
            SELECT
                concat('CUST-', lpad(cast(i AS STRING), 5, '0'))            AS customer_id,
                concat('First', cast(i AS STRING))                          AS first_name,
                concat('Last',  cast(i AS STRING))                          AS last_name,
                concat('cust-', cast(i AS STRING), '@example.com')          AS email,
                concat('+1-555-000-', lpad(cast(i AS STRING), 4, '0'))      AS phone,
                CASE i % 2 WHEN 0 THEN 'B2B' ELSE 'B2C' END                AS segment,
                CASE i % 4
                    WHEN 0 THEN 'Bronze' WHEN 1 THEN 'Silver'
                    WHEN 2 THEN 'Gold'   ELSE 'Platinum' END                AS tier,
                concat('City', cast(i AS STRING))                           AS city,
                'CA'                                                        AS state,
                'US'                                                        AS country,
                cast(date_add(date '2024-01-01', i) AS TIMESTAMP)           AS created_at,
                cast(date_add(date '2024-06-01', i) AS TIMESTAMP)           AS updated_at
            FROM (SELECT explode(sequence(1, 20)) AS i) t
        """)

        # ── orders (50 rows, all channels + statuses covered) ───────────────
        cur.execute("""
            CREATE OR REPLACE TABLE workspace.raw.orders AS
            SELECT
                concat('ORD-', lpad(cast(i AS STRING), 6, '0'))             AS order_id,
                concat('CUST-', lpad(cast((i % 20) + 1 AS STRING), 5, '0')) AS customer_id,
                date_add(date '2024-01-01', i)                              AS order_date,
                CASE i % 5
                    WHEN 0 THEN 'pending'   WHEN 1 THEN 'confirmed'
                    WHEN 2 THEN 'shipped'   WHEN 3 THEN 'delivered'
                    ELSE        'cancelled' END                             AS order_status,
                CASE i % 4
                    WHEN 0 THEN 'web'    WHEN 1 THEN 'mobile'
                    WHEN 2 THEN 'store'  ELSE 'api' END                     AS channel,
                concat('City', cast(i AS STRING))                           AS shipping_city,
                'CA'                                                        AS shipping_state,
                'US'                                                        AS shipping_country,
                cast(date_add(date '2024-01-01', i) AS TIMESTAMP)           AS created_at,
                cast(date_add(date '2024-01-01', i) AS TIMESTAMP)           AS updated_at,
                round(100.0 + i * 10.5, 2)                                 AS total_amount
            FROM (SELECT explode(sequence(1, 50)) AS i) t
        """)

        # ── order_items (50 rows) ────────────────────────────────────────────
        cur.execute("""
            CREATE OR REPLACE TABLE workspace.raw.order_items AS
            SELECT
                concat('ITEM-', lpad(cast(i AS STRING), 7, '0'))            AS order_item_id,
                concat('ORD-',  lpad(cast(i AS STRING), 6, '0'))            AS order_id,
                concat('PROD-', lpad(cast((i % 10) + 1 AS STRING), 4, '0')) AS product_id,
                (i % 5) + 1                                                 AS quantity,
                round(50.0 + i * 5.0, 2)                                   AS unit_price,
                0.0                                                         AS discount_pct,
                round((50.0 + i * 5.0) * ((i % 5) + 1), 2)                 AS line_total
            FROM (SELECT explode(sequence(1, 50)) AS i) t
        """)

        # ── products (10 rows) ───────────────────────────────────────────────
        cur.execute("""
            CREATE OR REPLACE TABLE workspace.raw.products AS
            SELECT
                concat('PROD-', lpad(cast(i AS STRING), 4, '0'))            AS product_id,
                concat('Product ', cast(i AS STRING))                       AS product_name,
                concat('Category', cast(i % 3 AS STRING))                   AS category,
                concat('Sub', cast(i % 5 AS STRING))                        AS subcategory,
                concat('Brand', cast(i % 4 AS STRING))                      AS brand,
                round(50.0 + i * 10.0, 2)                                  AS unit_price,
                round(20.0 + i * 4.0,  2)                                  AS cost_price,
                round(1.0  + i * 0.5,  2)                                  AS weight_kg,
                CASE WHEN i % 10 = 0 THEN 'False' ELSE 'True' END           AS is_active,
                cast(date_add(date '2020-01-01', i * 30) AS TIMESTAMP)      AS created_at
            FROM (SELECT explode(sequence(1, 10)) AS i) t
        """)

        for table in ["customers", "orders", "order_items", "products"]:
            cur.execute(f"SELECT COUNT(*) FROM workspace.raw.{table}")
            n = cur.fetchone()[0]
            print(f"  workspace.raw.{table:<15} {n:>4} rows")

    print("\nDatabricks raw schema ready: workspace.raw")


if __name__ == "__main__":
    setup()
