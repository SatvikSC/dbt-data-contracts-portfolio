# Data Dictionary — Modern ELT with dbt + Data Contracts

All models in the `ecommerce_dbt` project. Source tables live in the `raw` schema; output tables are in `dbt_prod` (Databricks) or `dev` (DuckDB).

---

## Source Tables (`raw` schema)

### raw.customers
Populated by `scripts/setup_ci_db.py` (DuckDB) or `scripts/setup_prod_db.py` (Databricks).

| Column | Type | Description |
|---|---|---|
| customer_id | VARCHAR | Primary key. Format: `CUST-00001` |
| first_name | VARCHAR | Customer first name |
| last_name | VARCHAR | Customer last name |
| email | VARCHAR | Email address (unique per customer) |
| phone | VARCHAR | Phone number. Format: `+1-555-000-0001` |
| segment | VARCHAR | `B2B` or `B2C` |
| tier | VARCHAR | `Bronze`, `Silver`, `Gold`, or `Platinum` |
| city | VARCHAR | City of residence |
| state | VARCHAR | US state code |
| country | VARCHAR | Country code (`US`) |
| created_at | TIMESTAMP | Account creation timestamp |
| updated_at | TIMESTAMP | Last profile update timestamp |

### raw.orders

| Column | Type | Description |
|---|---|---|
| order_id | VARCHAR | Primary key. Format: `ORD-000001` |
| customer_id | VARCHAR | FK → raw.customers.customer_id |
| order_date | DATE | Date the order was placed |
| order_status | VARCHAR | `pending`, `confirmed`, `shipped`, `delivered`, `cancelled` |
| channel | VARCHAR | `web`, `mobile`, `store`, `api` ← **contract-enforced via accepted_values** |
| shipping_city | VARCHAR | Destination city |
| shipping_state | VARCHAR | Destination state |
| shipping_country | VARCHAR | Destination country |
| created_at | TIMESTAMP | Record creation timestamp |
| updated_at | TIMESTAMP | Record update timestamp |
| total_amount | DECIMAL | Order total in USD |

### raw.order_items

| Column | Type | Description |
|---|---|---|
| order_item_id | VARCHAR | Primary key. Format: `ITEM-0000001` |
| order_id | VARCHAR | FK → raw.orders.order_id |
| product_id | VARCHAR | FK → raw.products.product_id |
| quantity | INTEGER | Units ordered |
| unit_price | DECIMAL | Price per unit |
| discount_pct | DECIMAL | Discount percentage (0.0 = no discount) |
| line_total | DECIMAL | `quantity × unit_price` |

### raw.products

| Column | Type | Description |
|---|---|---|
| product_id | VARCHAR | Primary key. Format: `PROD-0001` |
| product_name | VARCHAR | Display name |
| category | VARCHAR | Product category |
| subcategory | VARCHAR | Product subcategory |
| brand | VARCHAR | Brand name |
| unit_price | DECIMAL | Current selling price |
| cost_price | DECIMAL | Cost of goods |
| weight_kg | DECIMAL | Product weight |
| is_active | VARCHAR | `True` or `False` |
| created_at | TIMESTAMP | Product creation timestamp |

---

## Staging Models

### stg_customers (view)
Light cleaning layer over `raw.customers`. No business logic.

| Column | Type | Description | Tests |
|---|---|---|---|
| customer_id | VARCHAR | PK — unchanged from source | not_null, unique |
| first_name | VARCHAR | Unchanged | not_null |
| last_name | VARCHAR | Unchanged | not_null |
| full_name | VARCHAR | Derived: `first_name \|\| ' ' \|\| last_name` | not_null |
| email | VARCHAR | Lowercased | not_null, unique |
| phone | VARCHAR | Unchanged | — |
| customer_segment | VARCHAR | Renamed from `segment` | not_null, accepted_values(B2B/B2C) |
| customer_tier | VARCHAR | Renamed from `tier` | not_null, accepted_values(Bronze/Silver/Gold/Platinum) |
| city | VARCHAR | Unchanged | — |
| state | VARCHAR | Unchanged | — |
| country | VARCHAR | Unchanged | — |
| created_at | TIMESTAMP | Cast to TIMESTAMP | not_null |
| updated_at | TIMESTAMP | Cast to TIMESTAMP | not_null |

### stg_orders (view)
Light cleaning layer over `raw.orders`.

| Column | Type | Description | Tests |
|---|---|---|---|
| order_id | VARCHAR | PK — unchanged | not_null, unique |
| customer_id | VARCHAR | FK → stg_customers | not_null |
| order_date | DATE | Cast to DATE | not_null |
| order_status | VARCHAR | Unchanged | not_null, accepted_values |
| order_channel | VARCHAR | Renamed from `channel` | not_null, accepted_values(web/mobile/store/api) |
| shipping_city | VARCHAR | Unchanged | — |
| shipping_state | VARCHAR | Unchanged | — |
| shipping_country | VARCHAR | Unchanged | — |
| order_amount | DECIMAL(12,2) | Renamed + cast from `total_amount` | not_null, assert_positive_amounts |
| created_at | TIMESTAMP | Cast to TIMESTAMP | not_null |
| updated_at | TIMESTAMP | Cast to TIMESTAMP | not_null |

---

## Intermediate Models

### int_orders_with_customers (ephemeral)
Join of `stg_orders` + `stg_customers`. Not persisted — inlined as a CTE in downstream models.

| Column | Type | Source |
|---|---|---|
| order_id | VARCHAR | stg_orders |
| customer_id | VARCHAR | stg_orders |
| order_date | DATE | stg_orders |
| order_status | VARCHAR | stg_orders |
| order_channel | VARCHAR | stg_orders |
| order_amount | DECIMAL | stg_orders |
| shipping_city | VARCHAR | stg_orders |
| shipping_state | VARCHAR | stg_orders |
| shipping_country | VARCHAR | stg_orders |
| customer_segment | VARCHAR | stg_customers (join) |
| customer_tier | VARCHAR | stg_customers (join) |
| full_name | VARCHAR | stg_customers (join) |
| created_at | TIMESTAMP | stg_orders |
| updated_at | TIMESTAMP | stg_orders |

---

## Snapshot

### snap_customers (table — SCD Type 2)
dbt snapshot tracking all historical changes to `raw.customers`. Strategy: `timestamp` on `updated_at`.

Includes all columns from `raw.customers` plus dbt-managed SCD2 columns:

| Column | Type | Description |
|---|---|---|
| dbt_scd_id | VARCHAR | Surrogate key for this snapshot row |
| dbt_updated_at | TIMESTAMP | When this snapshot row was last evaluated |
| dbt_valid_from | TIMESTAMP | When this version became active |
| dbt_valid_to | TIMESTAMP | When this version expired (`NULL` = current record) |

---

## Mart Models

### dim_customers (table)
Current-state customer dimension. Source: `snap_customers WHERE dbt_valid_to IS NULL`.

| Column | Type | Description | Tests |
|---|---|---|---|
| customer_key | VARCHAR | Surrogate key — `generate_surrogate_key(['customer_id'])` | not_null, unique |
| customer_id | VARCHAR | Natural key | not_null |
| full_name | VARCHAR | first_name + last_name | not_null |
| email | VARCHAR | Lowercased | — |
| customer_segment | VARCHAR | `B2B` or `B2C` | not_null, accepted_values |
| customer_tier | VARCHAR | `Bronze`/`Silver`/`Gold`/`Platinum` | not_null, accepted_values |
| city | VARCHAR | — | — |
| state | VARCHAR | — | — |
| country | VARCHAR | — | — |
| valid_from | TIMESTAMP | SCD2 start date | not_null |
| valid_to | TIMESTAMP | SCD2 end date (`NULL` = current) | — |
| is_current | BOOLEAN | `TRUE` for the active record | — |
| created_at | TIMESTAMP | — | not_null |
| updated_at | TIMESTAMP | — | not_null |

### fact_orders (incremental — merge)
Order fact table. Incremental on `updated_at`; merge strategy with `unique_key = order_id`.

| Column | Type | Description | Tests |
|---|---|---|---|
| order_key | VARCHAR | Surrogate key — `generate_surrogate_key(['order_id'])` | not_null, unique |
| order_id | VARCHAR | Natural key | not_null |
| customer_key | VARCHAR | FK → dim_customers.customer_key | not_null, relationships |
| customer_id | VARCHAR | Natural key (denormalized) | not_null |
| order_date | DATE | — | not_null |
| order_status | VARCHAR | — | not_null, accepted_values |
| order_channel | VARCHAR | — | not_null, accepted_values |
| order_amount | DECIMAL(12,2) | — | not_null, assert_positive_amounts |
| shipping_city | VARCHAR | — | — |
| shipping_state | VARCHAR | — | — |
| shipping_country | VARCHAR | — | — |
| created_at | TIMESTAMP | — | not_null |
| updated_at | TIMESTAMP | Incremental high-watermark | not_null |

---

## Seeds

### order_status_codes (table)
Static reference table mapping status codes to display labels.

| Column | Type | Description |
|---|---|---|
| status_code | VARCHAR | PK — `pending`, `confirmed`, `shipped`, `delivered`, `cancelled` |
| display_name | VARCHAR | Human-readable label |
| is_terminal | BOOLEAN | Whether the order cannot change status further |
