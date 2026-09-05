"""
Generate minimal synthetic data in DuckDB for CI — no external file dependencies.
Creates raw schema tables with enough rows to pass all dbt tests.

Usage:
    python scripts/setup_ci_db.py [--db-path /tmp/ci_dev.duckdb]
"""

import argparse
import duckdb
from pathlib import Path


def setup(db_path: str) -> None:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        path.unlink()

    con = duckdb.connect(db_path)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # ── customers (20 rows) ──────────────────────────────────────────────────
    con.execute("""
        CREATE OR REPLACE TABLE raw.customers AS
        SELECT
            'CUST-' || LPAD(CAST(i AS VARCHAR), 5, '0')            AS customer_id,
            'First' || i                                            AS first_name,
            'Last'  || i                                            AS last_name,
            'cust-' || i || '@example.com'                         AS email,
            '+1-555-000-' || LPAD(CAST(i AS VARCHAR), 4, '0')      AS phone,
            CASE i % 2 WHEN 0 THEN 'B2B' ELSE 'B2C' END            AS segment,
            CASE i % 4
                WHEN 0 THEN 'Bronze' WHEN 1 THEN 'Silver'
                WHEN 2 THEN 'Gold'   ELSE 'Platinum' END            AS tier,
            'City' || i                                             AS city,
            'CA'                                                    AS state,
            'US'                                                    AS country,
            TIMESTAMP '2024-01-01' + INTERVAL (i) DAY               AS created_at,
            TIMESTAMP '2024-06-01' + INTERVAL (i) DAY               AS updated_at
        FROM generate_series(1, 20) t(i)
    """)

    # ── orders (50 rows, all channels + statuses covered) ───────────────────
    con.execute("""
        CREATE OR REPLACE TABLE raw.orders AS
        SELECT
            'ORD-' || LPAD(CAST(i AS VARCHAR), 6, '0')             AS order_id,
            'CUST-' || LPAD(CAST((i % 20) + 1 AS VARCHAR), 5, '0') AS customer_id,
            DATE '2024-01-01' + INTERVAL (i) DAY                    AS order_date,
            CASE i % 5
                WHEN 0 THEN 'pending'   WHEN 1 THEN 'confirmed'
                WHEN 2 THEN 'shipped'   WHEN 3 THEN 'delivered'
                ELSE        'cancelled' END                         AS order_status,
            CASE i % 4
                WHEN 0 THEN 'web'    WHEN 1 THEN 'mobile'
                WHEN 2 THEN 'store'  ELSE 'api' END                 AS channel,
            'City' || i                                             AS shipping_city,
            'CA'                                                    AS shipping_state,
            'US'                                                    AS shipping_country,
            TIMESTAMP '2024-01-01' + INTERVAL (i) DAY               AS created_at,
            TIMESTAMP '2024-01-01' + INTERVAL (i) DAY               AS updated_at,
            ROUND(100.0 + i * 10.5, 2)                              AS total_amount
        FROM generate_series(1, 50) t(i)
    """)

    # ── order_items (50 rows) ────────────────────────────────────────────────
    con.execute("""
        CREATE OR REPLACE TABLE raw.order_items AS
        SELECT
            'ITEM-' || LPAD(CAST(i AS VARCHAR), 7, '0')            AS order_item_id,
            'ORD-' || LPAD(CAST(i AS VARCHAR), 6, '0')             AS order_id,
            'PROD-' || LPAD(CAST((i % 10) + 1 AS VARCHAR), 4, '0') AS product_id,
            (i % 5) + 1                                             AS quantity,
            ROUND(50.0 + i * 5.0, 2)                               AS unit_price,
            0.0                                                     AS discount_pct,
            ROUND((50.0 + i * 5.0) * ((i % 5) + 1), 2)             AS line_total
        FROM generate_series(1, 50) t(i)
    """)

    # ── products (10 rows) ───────────────────────────────────────────────────
    con.execute("""
        CREATE OR REPLACE TABLE raw.products AS
        SELECT
            'PROD-' || LPAD(CAST(i AS VARCHAR), 4, '0')            AS product_id,
            'Product ' || i                                         AS product_name,
            'Category' || (i % 3)                                   AS category,
            'Sub' || (i % 5)                                        AS subcategory,
            'Brand' || (i % 4)                                      AS brand,
            ROUND(50.0 + i * 10.0, 2)                              AS unit_price,
            ROUND(20.0 + i * 4.0,  2)                              AS cost_price,
            ROUND(1.0  + i * 0.5,  2)                              AS weight_kg,
            CASE WHEN i % 10 = 0 THEN 'False' ELSE 'True' END       AS is_active,
            TIMESTAMP '2020-01-01' + INTERVAL (i * 30) DAY          AS created_at
        FROM generate_series(1, 10) t(i)
    """)

    for table in ["customers", "orders", "order_items", "products"]:
        n = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
        print(f"  raw.{table:<15} {n:>4} rows")

    con.close()
    print(f"\nCI database ready: {db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db-path", default="/tmp/ci_dev.duckdb",
        help="Path to output DuckDB file",
    )
    args = parser.parse_args()
    setup(args.db_path)
