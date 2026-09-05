# Modern ELT with dbt + Data Contracts

[![dbt CI/CD](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/YOUR_REPO/actions/workflows/ci.yml)
![dbt](https://img.shields.io/badge/dbt-1.12.3-orange)
![Python](https://img.shields.io/badge/python-3.12%2B-blue)

> **Portfolio Project 2 of 5** — Analytics engineering layer built with dbt Core on Databricks SQL.
> Demonstrates data contracts, dimensional modeling, SCD Type 2, incremental fact tables,
> and automated CI/CD with tests blocking every PR.

---

## What This Project Demonstrates

| Concept | Implementation |
|---|---|
| **Data contracts** | Column-level schema + freshness expectations in `_sources.yml` — CI fails automatically if upstream breaks the contract |
| **Dimensional modeling** | `dim_customers` (SCD Type 2 via snapshot) + `fact_orders` (incremental, merge) |
| **Surrogate keys** | `dbt_utils.generate_surrogate_key` — deterministic, never raw MD5 |
| **Incremental models** | `fact_orders` uses `merge` strategy — idempotent, no duplicates on re-run |
| **Slim CI** | `dbt run --select state:modified+` — only changed models run per PR |
| **dbt docs** | Auto-generated site with full lineage DAG, deployed to GitHub Pages on every merge |
| **Custom tests** | `assert_positive_amounts` — generic test enforcing business rules |

---

## Architecture

```
 DATA SOURCE (Project 1 Bronze / local DuckDB)
       │
       ▼
 ┌─────────────────────────────┐
 │  _sources.yml  (CONTRACT)   │  ← Column definitions, freshness, accepted values
 │  schema: raw                │    CI fails if upstream violates these rules
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
       ┌───────┴────────┐
       ▼                ▼
 fact_orders.sql   dim_customers.sql       MART (Gold — analyst-ready)
  (incremental)    (from snapshot)
       │                │
       └───────┬────────┘
               ▼
    Power BI / ML Feature Platform         EXPOSURES
```

**Snapshot:** `snap_customers` tracks SCD Type 2 history for every customer change.

---

## Project Structure

```
02_ELT_dbt_Data_Contracts/
├── models/
│   ├── staging/
│   │   ├── _sources.yml            # Data contracts — the producer-consumer agreement
│   │   ├── _staging__models.yml    # Staging docs + tests
│   │   ├── stg_orders.sql
│   │   └── stg_customers.sql
│   ├── intermediate/
│   │   ├── _intermediate__models.yml
│   │   └── int_orders_with_customers.sql
│   └── marts/sales/
│       ├── _sales__models.yml      # Gold layer docs + tests
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
│   ├── setup_dev_db.py             # Load Project 1 CSVs into local DuckDB
│   └── setup_ci_db.py              # Generate synthetic data for CI
├── .github/workflows/
│   └── ci.yml                      # PR gate + GitHub Pages docs deploy
├── dbt_project.yml
├── packages.yml
├── profiles.yml                    # NOT committed — see .env.example
└── ProdReadyCheckList.md           # What to change before switching to Databricks prod
```

---

## Prerequisites

- Python 3.12+
- Git

No Java, no Spark, no cloud credentials needed for local development.

---

## Quick Start (Local Dev — DuckDB)

**1. Clone the repo**
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd 02_ELT_dbt_Data_Contracts
```

**2. Create and activate the virtual environment**
```bash
# venv lives at a short path to avoid Windows 260-char limit
python -m venv C:\venvs\proj02_dbt
# Windows PowerShell:
. .\activate_env.ps1
# macOS/Linux:
source C:/venvs/proj02_dbt/bin/activate
```

**3. Install dependencies**
```bash
pip install dbt-databricks==1.12.5 dbt-duckdb==1.11.0 pip-system-certs
```

**4. Create `profiles.yml`** (not committed — copy this)
```yaml
ecommerce_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "C:/venvs/proj02_dbt_db/dev.duckdb"
      schema: dev
      threads: 4
```

**5. Populate the local database**
```bash
# Uses Project 1 CSVs (5,000 orders, 500 customers):
python scripts/setup_dev_db.py

# OR use the self-contained CI generator (no Project 1 needed):
python scripts/setup_ci_db.py --db-path C:/venvs/proj02_dbt_db/dev.duckdb
```

**6. Install dbt packages + run everything**
```bash
dbt deps
dbt snapshot          # Build SCD Type 2 snap_customers
dbt seed              # Load order_status_codes
dbt run               # Build all models
dbt test              # Run all 80 tests
```

**7. Browse the docs**
```bash
dbt docs generate
dbt docs serve        # Opens browser at http://localhost:8080
```

---

## Running Tests

```bash
# All tests (80)
dbt test

# Source contract tests only (PR gate in CI)
dbt test --select source:*

# Staging tests only
dbt test --select staging

# Mart tests only
dbt test --select marts
```

---

## Switching to Databricks (Production)

See [`ProdReadyCheckList.md`](ProdReadyCheckList.md) for the full checklist.
The short version:

1. Add Databricks credentials to `.env` (copy from `.env.example`)
2. Update `_sources.yml`: set `database`, change `schema: raw` → `schema: bronze`, update `loaded_at_field: _ingest_timestamp`
3. Run: `dbt run --target prod`

---

## CI/CD

Every PR triggers `.github/workflows/ci.yml`:

```
Push / PR
    │
    ├── dbt compile          (syntax check)
    ├── dbt test source:*    (contract gate — PR blocked on violation)
    ├── dbt snapshot + seed
    └── dbt run / test       (slim CI: state:modified+ if manifest exists)

Merge to main
    └── deploy-docs job → dbt docs generate → GitHub Pages
```

**Slim CI** stores `target/manifest.json` as a GitHub Actions artifact after each main-branch run.
Subsequent PRs download it and run only the changed models + downstream dependencies.

---

## GitHub Repository Setup

If you haven't pushed this project yet:

```bash
# From the project root:
git init
git add .
git commit -m "feat: add dbt + data contracts project (Phases 1-4)"

# Create a new repo on GitHub (github.com → New repository)
# Then:
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git branch -M main
git push -u origin main
```

**After pushing**, enable GitHub Pages:
`Settings → Pages → Source: GitHub Actions`

Update the badge URLs at the top of this README with your actual repo path.

---

## Key Design Decisions

| Decision | Choice | Why |
|---|---|---|
| Transformation layer | dbt Core | Version-controlled SQL, built-in testing, auto-docs — industry standard |
| Warehouse | Databricks SQL (prod) / DuckDB (dev) | Reuses Project 1 Delta tables; DuckDB = zero-cost local dev |
| Staging materialization | `view` | No storage cost; always reflects latest source |
| Intermediate materialization | `ephemeral` | Inlined as CTE — clean lineage, no warehouse objects |
| Fact materialization | `incremental` + `merge` | Idempotent; avoids full recompute on every run |
| SCD Type 2 | dbt `snapshot` | Battle-tested, no custom MERGE SQL needed |
| Data contracts | `_sources.yml` | Version-controlled alongside transformations; violations caught in CI |
| Slim CI | `state:modified+` | Only run changed models — keeps CI under 5 minutes as project grows |

Full rationale in [`design.md`](design.md).

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

## Related Projects

| # | Project | Relationship |
|---|---|---|
| 1 | [Lakehouse Platform](../01_Lakehouse_Platform) | Upstream — produces the Bronze Delta tables this project reads |
| 3 | Streaming Pipeline | Sibling — adds real-time orders alongside this batch layer |
| 4 | ML Feature Platform | Downstream — consumes `fact_orders` + `dim_customers` for feature engineering |
| 5 | GenAI Data Assistant | Downstream — queries mart tables via natural language |
