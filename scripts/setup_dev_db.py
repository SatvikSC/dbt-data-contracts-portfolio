"""
Populate the local DuckDB dev database with raw source tables from Project 1 CSVs.
Run this once before `dbt run` in local dev:

    python scripts/setup_dev_db.py

Source CSVs: Project 1 data/raw/<table>/<table>_*.csv
Target DB:   C:/venvs/proj02_dbt_db/dev.duckdb  (raw schema)
"""

import duckdb
from pathlib import Path

RAW_DATA_ROOT = Path(
    r"C:\Users\satvisa\OneDrive - Ecolab\Documents\Git_clone"
    r"\ClaudeCodeRepo\BrainStorm\Projects\01_Lakehouse_Platform\data\raw"
)

DB_PATH = Path(r"C:\venvs\proj02_dbt_db\dev.duckdb")

# Maps DuckDB table name -> glob pattern relative to RAW_DATA_ROOT
SOURCES = {
    "orders":      "orders/orders_*.csv",
    "customers":   "customers/customers_*.csv",
    "order_items": "order_items/order_items_*.csv",
    "products":    "products/products_*.csv",
}


def setup() -> None:
    if not RAW_DATA_ROOT.exists():
        raise FileNotFoundError(
            f"Project 1 raw data not found at: {RAW_DATA_ROOT}\n"
            "Run Project 1 data_generator.py first."
        )

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Drop and recreate for a clean, deterministic state
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"Removed existing database: {DB_PATH}")

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")

    print(f"\nLoading source tables into raw schema -> {DB_PATH}\n")

    for table, glob_pattern in SOURCES.items():
        csv_glob = str(RAW_DATA_ROOT / glob_pattern).replace("\\", "/")
        con.execute(f"""
            CREATE OR REPLACE TABLE raw.{table} AS
            SELECT *
            FROM read_csv_auto('{csv_glob}', union_by_name = true)
        """)
        count = con.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
        print(f"  raw.{table:<15} {count:>7,} rows")

    con.close()
    print(f"\nDev database ready. Run 'dbt run' to build staging models.")


if __name__ == "__main__":
    setup()
