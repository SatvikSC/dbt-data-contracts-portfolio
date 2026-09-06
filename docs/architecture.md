# Architecture — Modern ELT with dbt + Data Contracts

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
│   raw.{customers, orders, order_items, products}                 │
│   Populated by: scripts/setup_ci_db.py   (DuckDB)               │
│                 scripts/setup_prod_db.py  (Databricks)           │
└──────────────────────────┬──────────────────────────────────────┘
                           │
              ┌────────────▼────────────┐
              │     dbt Sources          │
              │   _sources.yml           │
              │   Data Contract Layer    │
              │   · column schema        │
              │   · accepted_values      │
              │   · freshness thresholds │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │   Staging (Views)        │
              │   stg_customers          │
              │   stg_orders             │
              │   · rename columns       │
              │   · cast types           │
              │   · lowercase email      │
              └────────────┬────────────┘
                           │
              ┌────────────▼────────────┐
              │  Intermediate (Ephemeral)│
              │  int_orders_with_        │
              │  customers               │
              │  · join orders+customers │
              │  · business logic CTEs   │
              └────────────┬────────────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
┌────────▼───────┐ ┌───────▼──────┐  ┌───────▼──────┐
│  Snapshot       │ │ dim_customers│  │ fact_orders   │
│  snap_customers │ │ (Table)      │  │ (Incremental) │
│  SCD Type 2     │ │ SCD2 from    │  │ merge strategy│
│  timestamp      │ │ snap         │  │ unique_key    │
└─────────────────┘ └──────────────┘  └───────────────┘

Seeds: order_status_codes (reference table)

CI/CD:
  PR → GitHub Actions (DuckDB) → contract tests → slim CI → block/merge
  main push → dbt docs generate → deploy to GitHub Pages
  Manual/tag → Databricks prod run → workspace.dbt_prod
```

## Environment Matrix

| Dimension | Dev (local) | CI (GitHub Actions) | Prod (Databricks) |
|---|---|---|---|
| Engine | DuckDB | DuckDB | Databricks SQL Warehouse |
| Raw data | `setup_ci_db.py` | `setup_ci_db.py` | `setup_prod_db.py` |
| Source catalog | *(auto from target)* | *(auto from target)* | `workspace` (via `catalog:` in profiles) |
| Output schema | `dev` | `dev` | `workspace.dbt_prod` |
| Snapshot schema | `dev` | `dev` | `workspace.snapshots` |
| Trigger | manual | every PR | manual / release tag |
| Cost | free | free | SQL Warehouse compute |

## dbt Model Inventory

| Model | Layer | Materialization | Source |
|---|---|---|---|
| `stg_customers` | Staging | view | `raw.customers` |
| `stg_orders` | Staging | view | `raw.orders` |
| `int_orders_with_customers` | Intermediate | ephemeral | stg_orders + stg_customers |
| `snap_customers` | Snapshot | table (SCD2) | `raw.customers` |
| `dim_customers` | Mart | table | `snap_customers` |
| `fact_orders` | Mart | incremental (merge) | `int_orders_with_customers` |
| `order_status_codes` | Seed | table | `seeds/order_status_codes.csv` |

## Data Contract Definition

Contracts live in `models/staging/_sources.yml`. Example accepted_values contract:

```yaml
- name: channel
  tests:
    - accepted_values:
        arguments:
          values: ['web', 'mobile', 'store', 'api']
```

If upstream adds a new channel value not in this list, CI fails at `dbt test --select source:*`
and the PR is blocked automatically. See `test/contract-break` branch for a live example.

## Materialization Strategy

| Layer | Materialization | Reason |
|---|---|---|
| Staging | `view` | Zero storage; always reflects latest source |
| Intermediate | `ephemeral` | Inlined as CTE — no warehouse object; clean lineage |
| Dims | `table` | Small, fully refreshed each run |
| Facts | `incremental` + `merge` | Avoid full recompute; idempotent on re-run |
| Snapshot | `table` (dbt-managed) | SCD2 via `strategy: timestamp`; `dbt_valid_to IS NULL` = current |

## CI/CD Pipeline

```
PR opened
  ↓
GitHub Actions (ci.yml) — DuckDB, no Databricks secrets needed
  ↓
setup_ci_db.py → populate raw.{customers, orders, ...}
  ↓
dbt deps → dbt compile (syntax check)
  ↓
dbt test --select source:*         ← CONTRACT GATE: fails if schema violated
  ↓
dbt snapshot + dbt seed
  ↓
dbt run --select state:modified+   ← slim CI: only changed + downstream
  ↓
dbt test --select state:modified+
  ↓
PR blocked on any failure / approved on green
  ↓
Merge to main → deploy-docs.yml → dbt docs generate → GitHub Pages

Manual trigger → run-prod.yml → Databricks SQL Warehouse → workspace.dbt_prod
```

## Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Transformation | dbt Core 1.12.3 | Version-controlled SQL, built-in tests, auto-docs |
| Dev/CI warehouse | DuckDB 1.5.5 | Zero cost, zero infra, identical SQL dialect |
| Prod warehouse | Databricks SQL Warehouse | Unity Catalog, Delta, production-grade |
| CI/CD | GitHub Actions | Native GitHub; free for public repos |
| Docs hosting | GitHub Pages | Zero cost; auto-deployed from CI |
| Surrogate keys | `dbt_utils.generate_surrogate_key` | Deterministic, replicable across runs |
| SCD2 | dbt Snapshot | Native; no custom MERGE SQL needed |
| Contract enforcement | dbt `_sources.yml` | Version-controlled alongside models |
