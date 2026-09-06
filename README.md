# Modern ELT with dbt + Data Contracts

[![dbt CI/CD](https://github.com/SatvikSC/dbt-data-contracts-portfolio/actions/workflows/ci.yml/badge.svg)](https://github.com/SatvikSC/dbt-data-contracts-portfolio/actions/workflows/ci.yml)
[![dbt Docs](https://github.com/SatvikSC/dbt-data-contracts-portfolio/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/SatvikSC/dbt-data-contracts-portfolio/actions/workflows/deploy-docs.yml)
![dbt](https://img.shields.io/badge/dbt-1.12.3-orange)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)

> **Portfolio Project 2 of 5** — Analytics engineering layer built with dbt Core.
> Demonstrates data contracts, dimensional modeling (SCD Type 2), incremental fact tables,
> and automated CI/CD with schema violations blocking every PR.

---

## What This Project Demonstrates

| Concept | Implementation |
|---|---|
| **Data contracts** | Column-level schema + freshness in `_sources.yml` — CI fails automatically on violation |
| **Dimensional modeling** | `dim_customers` (SCD2 via snapshot) + `fact_orders` (incremental, merge) |
| **Incremental models** | `fact_orders` uses `merge` strategy — idempotent, no duplicates on re-run |
| **SCD Type 2** | `snap_customers` snapshot tracks full customer history; `dbt_valid_to IS NULL` = current |
| **Surrogate keys** | `dbt_utils.generate_surrogate_key` — deterministic, never raw MD5 |
| **Dual-target** | DuckDB (zero-cost dev/CI) + Databricks SQL Warehouse (prod) — same model SQL |
| **Slim CI** | `dbt run --select state:modified+` — only changed models + downstream per PR |
| **dbt docs** | Auto-generated lineage site deployed to GitHub Pages on every merge |
| **Custom tests** | `assert_positive_amounts` — generic test enforcing business rules |

---

## Architecture

```
 RAW SOURCES
 raw.{customers, orders, order_items, products}
 Populated by: setup_ci_db.py (DuckDB) | setup_prod_db.py (Databricks)
       │
       ▼
 ┌─────────────────────────────┐
 │  _sources.yml  (CONTRACT)   │  ← Column schema, freshness, accepted values
 │  schema: raw                │    CI fails if upstream violates any rule
 └─────────────┬───────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
 stg_orders.sql    stg_customers.sql       STAGING (views — no storage cost)
       │                │
       └───────┬────────┘
               ▼
  int_orders_with_customers.sql            INTERMEDIATE (ephemeral CTE)
               │
       ┌───────┴──────────────┐
       ▼                      ▼
 fact_orders.sql         dim_customers.sql       MART (analyst-ready)
  (incremental,          (from snap_customers,
   merge strategy)        SCD Type 2)
```

**Snapshot:** `snap_customers` tracks full SCD Type 2 history; `dim_customers` filters `dbt_valid_to IS NULL` for the current state.

---

## Project Structure

```
02_ELT_dbt_Data_Contracts/
├── models/
│   ├── staging/
│   │   ├── _sources.yml            # Data contracts — producer-consumer agreement
│   │   ├── _staging__models.yml    # Staging docs + tests
│   │   ├── stg_orders.sql
│   │   └── stg_customers.sql
│   ├── intermediate/
│   │   ├── _intermediate__models.yml
│   │   └── int_orders_with_customers.sql
│   └── marts/sales/
│       ├── _sales__models.yml      # Mart docs + tests
│       ├── _exposures.yml          # Downstream consumers (Power BI, ML Platform)
│       ├── dim_customers.sql       # SCD Type 2 dimension
│       └── fact_orders.sql         # Incremental fact (merge strategy)
├── snapshots/
│   └── snap_customers.sql          # SCD Type 2 history table
├── tests/generic/
│   └── assert_positive_amounts.sql # Custom generic test
├── seeds/
│   └── order_status_codes.csv      # Static reference data
├── scripts/
│   ├── setup_ci_db.py              # Populate DuckDB raw schema (local + CI)
│   └── setup_prod_db.py            # Populate Databricks raw schema (prod)
├── images/
│   └── dbt-dag.png                 # Lineage DAG screenshot
├── docs/
│   ├── architecture.md             # Architecture + environment matrix
│   ├── data_dictionary.md          # All model + column definitions
│   ├── design.md                   # Design decisions with trade-offs
│   ├── setup_guide.md              # Step-by-step local + Databricks setup
│   ├── troubleshooting.md          # Common errors and fixes
│   ├── portfolio_showcase.md       # Interview talking points
│   └── demoVideo.md                # Demo walkthrough script
├── .github/workflows/
│   ├── ci.yml                      # PR gate — DuckDB (no secrets needed)
│   ├── deploy-docs.yml             # Auto-deploy dbt docs → GitHub Pages
│   └── run-prod.yml                # Databricks prod run (manual trigger)
├── dbt_project.yml
├── packages.yml
├── .env.example                    # Env var template (no secrets)
└── README.md
```

---

## Prerequisites

- Python 3.11+
- Git

No Java, no Spark, no cloud credentials needed for local development.

---

## Quick Start (Local Dev — DuckDB, zero cost)

**1. Clone and activate venv**
```bash
git clone https://github.com/SatvikSC/dbt-data-contracts-portfolio.git
cd dbt-data-contracts-portfolio

# Short path avoids Windows 260-char limit on deep dbt_packages subpaths
python -m venv C:\venvs\portfolio
C:\venvs\portfolio\Scripts\activate     # Windows PowerShell
# source C:/venvs/portfolio/bin/activate  # macOS/Linux
```

**2. Install dbt**
```bash
pip install dbt-duckdb pip-system-certs
# pip-system-certs is required if behind a corporate SSL proxy
```

**3. Create `profiles.yml`** (never committed — copy this into the project root)
```yaml
ecommerce_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "C:/venvs/portfolio_db/dev.duckdb"
      schema: dev
      threads: 4
```

**4. Populate raw schema + run the pipeline**
```bash
python scripts/setup_ci_db.py --db-path C:/venvs/portfolio_db/dev.duckdb
dbt deps
dbt snapshot && dbt seed && dbt run
dbt test                              # 80 tests — expect 0 errors
```

**5. Browse the lineage docs**
```bash
dbt docs generate
dbt docs serve        # Opens http://localhost:8080
```

---

## Production Run (Databricks SQL Warehouse)

See [`docs/setup_guide.md`](docs/setup_guide.md) for full instructions. Short version:

1. Create a Databricks SQL Warehouse → copy **Server hostname** and **HTTP path**
2. Add prod target to `profiles.yml` with `catalog: workspace`
3. Run:
```bash
pip install dbt-databricks
python scripts/setup_prod_db.py   # populates workspace.raw.*
dbt snapshot --target prod
dbt seed     --target prod
dbt run      --target prod
dbt test     --target prod
```

Output tables: `workspace.dbt_prod.{dim_customers, fact_orders}`

---

## CI/CD

### On every PR — `.github/workflows/ci.yml` (DuckDB, no secrets needed)
```
setup_ci_db.py → populate raw schema
dbt compile    → syntax check
dbt test --select source:*         ← CONTRACT GATE: PR blocked on violation
dbt snapshot + dbt seed
dbt run/test --select state:modified+   ← slim CI: changed models only
```

### On merge to main — `.github/workflows/deploy-docs.yml`
```
dbt docs generate → deploy to GitHub Pages
```

### Manual / release tag — `.github/workflows/run-prod.yml`
```
setup_prod_db.py → workspace.raw.*
dbt snapshot + seed + run + test --target prod → workspace.dbt_prod.*
```

**Enable GitHub Pages:** Settings → Pages → Source: **GitHub Actions**

**Add 3 GitHub Secrets** for the prod workflow:
`DBT_DATABRICKS_HOST` · `DBT_DATABRICKS_HTTP_PATH` · `DBT_DATABRICKS_TOKEN`

---

## Demonstrate Contract Enforcement

```bash
git checkout test/contract-break
# This branch removes 'api' from channel accepted_values in _sources.yml
# Open as a PR → CI fails at: dbt test --select source:*
git checkout main   # to restore
```

---

## Running Tests

```bash
dbt test                        # all 80 tests
dbt test --select source:*      # source contract tests only
dbt test --select staging       # staging tests only
dbt test --select marts         # mart tests only
```

---

## Test Coverage

| Layer | Models | Tests |
|---|---|---|
| Sources (contracts) | 2 | 23 |
| Staging | 2 | 30 |
| Intermediate | 1 (ephemeral) | — |
| Marts | 2 | 27 |
| **Total** | **5** | **80** |

---

## Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Transformation | dbt Core | Version-controlled SQL, built-in testing, auto-docs |
| Dev/CI warehouse | DuckDB | Zero cost, zero infra, identical SQL dialect |
| Prod warehouse | Databricks SQL | Unity Catalog, Delta, production-grade |
| Staging | `view` | No storage cost; always reflects latest source |
| Intermediate | `ephemeral` | Inlined as CTE — clean lineage, no warehouse objects |
| Facts | `incremental` + `merge` | Idempotent; avoids full recompute on every run |
| SCD2 | dbt `snapshot` | No custom MERGE SQL; dbt manages `dbt_valid_from/to` |
| Contracts | `_sources.yml` | Version-controlled alongside transformations |
| Slim CI | `state:modified+` | Only run what changed — keeps CI under 5 minutes |

Full rationale: [`docs/design.md`](docs/design.md)

---

## Documentation

| Doc | Description |
|---|---|
| [`docs/architecture.md`](docs/architecture.md) | Architecture diagrams, environment matrix |
| [`docs/data_dictionary.md`](docs/data_dictionary.md) | All model + column definitions |
| [`docs/setup_guide.md`](docs/setup_guide.md) | Local + Databricks + CI setup |
| [`docs/troubleshooting.md`](docs/troubleshooting.md) | Common errors and fixes |
| [`docs/portfolio_showcase.md`](docs/portfolio_showcase.md) | Interview talking points |

---

## Related Projects

| # | Project | Relationship |
|---|---|---|
| 1 | [Lakehouse Platform](../01_Lakehouse_Platform) | Upstream — produces the Bronze Delta tables this project reads |
| 3 | Streaming Pipeline | Sibling — adds real-time orders alongside this batch layer |
| 4 | ML Feature Platform | Downstream — consumes `fact_orders` + `dim_customers` for feature engineering |
| 5 | GenAI Data Assistant | Downstream — queries mart tables via natural language |
