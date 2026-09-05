# CLAUDE.md — Modern ELT with dbt + Data Contracts

## Project Overview
Analytics engineering layer built with dbt Core on Databricks SQL. Demonstrates data contract enforcement via dbt sources, dimensional modeling (fact + dims), incremental materializations, and automated CI/CD with tests blocking bad PRs.

## Repository Structure
```
02_ELT_dbt_Data_Contracts/
├── models/
│   ├── staging/
│   │   ├── _sources.yml          # Data contracts — all source definitions here
│   │   ├── _staging__models.yml  # Staging model docs + tests
│   │   ├── stg_orders.sql
│   │   └── stg_customers.sql
│   ├── intermediate/
│   │   ├── _intermediate__models.yml
│   │   └── int_orders_enriched.sql
│   └── marts/
│       ├── sales/
│       │   ├── _sales__models.yml
│       │   ├── fact_orders.sql
│       │   └── dim_customers.sql
│       └── ...
├── tests/
│   └── generic/                  # Custom generic test macros
├── macros/
├── seeds/
├── .github/
│   └── workflows/
│       └── ci.yml
├── dbt_project.yml
├── packages.yml
├── .env.example
└── README.md
```

## How to Run

### Setup
```bash
pip install dbt-databricks dbt-utils
cp .env.example .env  # fill in Databricks credentials
```

### Run all models
```bash
dbt deps
dbt run
dbt test
```

### Run only changed models (slim CI)
```bash
dbt run --select state:modified+
dbt test --select state:modified+
```

### Generate and serve docs locally
```bash
dbt docs generate
dbt docs serve
```

### Test source contracts only
```bash
dbt test --select source:*
```

## Environment Variables
See `.env.example`:
- `DBT_DATABRICKS_HOST`
- `DBT_DATABRICKS_HTTP_PATH`
- `DBT_DATABRICKS_TOKEN`
- `DBT_TARGET_CATALOG`
- `DBT_TARGET_SCHEMA`

## Critical Rules
- Every new model requires a `schema.yml` entry with description + at least 3 tests before merging
- Staging models: `view` only — never `table`
- Fact tables: `incremental` with `unique_key` and `merge` strategy
- Surrogate keys: always use `dbt_utils.generate_surrogate_key` — never raw MD5
- Source contracts in `_sources.yml` must be updated in the same PR as any model depending on that source

## Gotchas
- `profiles.yml` is never committed — it's in `.gitignore`; use environment variables in CI
- Slim CI requires the production `manifest.json` artifact — store in ADLS or as a GitHub Actions artifact
- dbt test `relationships` requires both tables to exist — run `dbt run` before `dbt test` in CI
- Databricks SQL warehouses have a startup time — account for this in CI timeout settings
- `is_incremental()` macro returns `False` on first run (full refresh) — test both paths

## CI/CD
`.github/workflows/ci.yml` runs on every PR:
1. `dbt deps`
2. `dbt compile`
3. `dbt source freshness`
4. `dbt test --select source:*`
5. `dbt run --select state:modified+`
6. `dbt test --select state:modified+`

On merge to `main`:
1. `dbt run` (full)
2. `dbt docs generate`
3. Deploy docs to GitHub Pages
