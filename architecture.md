# Architecture — Modern ELT with dbt + Data Contracts

## High-Level Architecture

```
┌──────────────────────────────────────────────────┐
│                   DATA SOURCES                    │
│   Bronze/Raw Tables (from Project 1 or direct)   │
└───────────────────┬──────────────────────────────┘
                    │
         ┌──────────▼──────────┐
         │   dbt Sources        │
         │   (Contract Layer)   │
         │   - schema defined   │
         │   - freshness tests  │
         │   - source tests     │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │   Staging Models     │
         │   stg_*              │
         │   - rename columns   │
         │   - cast types       │
         │   - light cleaning   │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Intermediate Models │
         │  int_*               │
         │  - joins             │
         │  - business logic    │
         │  - reusable CTEs     │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │    Mart Models       │
         │    fact_* / dim_*    │
         │    - final tables    │
         │    - analyst-ready   │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │   dbt Docs Site      │
         │   (auto-generated)   │
         └─────────────────────┘

CI/CD: GitHub Actions → dbt test → dbt run → deploy docs
```

## dbt Project Structure

```
dbt_project/
├── models/
│   ├── staging/
│   │   ├── _sources.yml          # Data contracts defined here
│   │   ├── _staging__models.yml  # Staging model docs + tests
│   │   ├── stg_orders.sql
│   │   └── stg_customers.sql
│   ├── intermediate/
│   │   ├── _intermediate__models.yml
│   │   └── int_orders_with_customers.sql
│   └── marts/
│       ├── sales/
│       │   ├── _sales__models.yml
│       │   ├── fact_orders.sql
│       │   └── dim_customers.sql
│       └── inventory/
│           └── ...
├── tests/
│   └── generic/                  # Custom generic tests
├── macros/
│   └── generate_surrogate_key.sql
├── seeds/
│   └── date_spine.csv
├── analyses/
├── dbt_project.yml
└── profiles.yml (not committed — use env vars)
```

## Data Contract Definition (in `_sources.yml`)

```yaml
sources:
  - name: raw_sales
    database: corp_analytics
    schema: bronze
    freshness:
      warn_after: {count: 12, period: hour}
      error_after: {count: 24, period: hour}
    tables:
      - name: orders
        loaded_at_field: _ingest_timestamp
        columns:
          - name: order_id
            tests:
              - not_null
              - unique
          - name: customer_id
            tests:
              - not_null
          - name: order_date
            tests:
              - not_null
          - name: status
            tests:
              - accepted_values:
                  values: ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
```

This is the contract. If upstream violates it, CI fails.

## Materialization Strategy

| Model Layer | Materialization | Reason |
|---|---|---|
| Staging | `view` | Low storage cost; always reflects latest source |
| Intermediate | `ephemeral` or `view` | Reusable logic; not queried directly |
| Mart — small dims | `table` | Fully refreshed; simple and correct |
| Mart — large facts | `incremental` | Avoid full recompute on every run |

## Incremental Strategy for Fact Tables

```sql
-- fact_orders.sql
{{
  config(
    materialized='incremental',
    unique_key='order_id',
    incremental_strategy='merge'
  )
}}

SELECT ...
FROM {{ ref('int_orders_with_customers') }}

{% if is_incremental() %}
  WHERE order_updated_at > (SELECT MAX(order_updated_at) FROM {{ this }})
{% endif %}
```

## CI/CD Pipeline

```
PR opened
   ↓
GitHub Actions triggered
   ↓
dbt deps (install packages)
   ↓
dbt compile (syntax check)
   ↓
dbt test --select source:*     (contract/source tests)
   ↓
dbt run --select state:modified+  (changed models only)
   ↓
dbt test --select state:modified+  (tests on changed models)
   ↓
PR blocked if any step fails
   ↓
Merge to main
   ↓
dbt run (full)
   ↓
dbt docs generate + deploy to GitHub Pages
```

## Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Transformation layer | dbt Core | Version-controlled SQL, built-in testing, auto-docs |
| Warehouse | Databricks SQL | Leverages Project 1 Delta tables directly |
| CI/CD | GitHub Actions | Native GitHub integration, free for public repos |
| Docs hosting | GitHub Pages | Zero cost; auto-deployed from CI |
| Surrogate keys | `dbt_utils.generate_surrogate_key` | Deterministic, replicable across runs |
