# Memory — Modern ELT with dbt + Data Contracts

## Project Status
- **All Phases:** Complete (1 through 4 + 3b Databricks prod)
- **Started:** 2026-09-05
- **Last updated:** 2026-09-06

## Key Decisions Made
- dbt Core 1.12.3 (not dbt Cloud)
- DuckDB 1.5.5 for local dev + CI (zero cost); Databricks SQL Warehouse for prod
- Staging: `view`; Intermediate: `ephemeral`; Dims: `table`; Facts: `incremental` + `merge`
- SCD2 via dbt snapshot (strategy: timestamp, updated_at)
- Data contracts via `_sources.yml` — contract-break branch demonstrates CI failure
- Slim CI using `state:modified+` with manifest artifact
- Docs deployed to GitHub Pages via `deploy-docs.yml`
- `dbt_expectations` package: use `metaplane/dbt_expectations` (calogica namespace deprecated)
- `accepted_values` tests: use `arguments:` nesting (dbt 1.9+ syntax)
- `database:` field omitted from `_sources.yml` — dbt auto-resolves from `target.database`

## Environment
- Python 3.13.10
- venv: `C:\venvs\portfolio` (short path — Windows 260-char limit; metricflow has deep subpaths)
- DuckDB dev DB: `C:\venvs\portfolio_db\dev.duckdb`
- `pip-system-certs` required for corporate SSL proxy (hub.getdbt.com)

## What's Built

### Staging (Phase 1) — 47/47 tests pass
- `stg_orders.sql` — rename, cast, clean from raw.orders
- `stg_customers.sql` — rename, lowercase email, derive full_name
- `_sources.yml` — data contracts for orders + customers (17 col-level tests)
- `_staging__models.yml` — 30 model-level tests

### Marts (Phase 2) — 79/79 tests pass
- `snap_customers` — SCD Type 2 snapshot
- `int_orders_with_customers` — ephemeral join intermediate
- `dim_customers` — current-state dimension, surrogate key
- `fact_orders` — incremental, merge, idempotent ✓
- `seeds/order_status_codes.csv` — 5 static status rows

### CI/CD (Phase 3) ✅ — 80/80 tests pass
- `tests/generic/assert_positive_amounts.sql` — custom test
- `.github/workflows/ci.yml` — PR gate (DuckDB, no secrets)
- `.github/workflows/deploy-docs.yml` — dbt docs → GitHub Pages on push to main
- `scripts/setup_ci_db.py` — self-contained CI data generator
- Contract breach demo: `test/contract-break` branch → CI fails at source tests ✓

### Databricks Prod (Phase 3b) ✅
- `scripts/setup_prod_db.py` — creates workspace.raw.* via Databricks SQL connector
- `.github/workflows/run-prod.yml` — manual/tag-triggered Databricks prod pipeline
- `profiles.yml` — dual target: dev (DuckDB) + prod (Databricks SQL Warehouse)
- Prod pipeline: setup_prod_db → dbt seed → dbt snapshot → dbt run → dbt test ✓

### Documentation (Phase 4) ✅
- `meta` tags on all 5 models: owner, domain, tier, contains_pii
- `models/marts/sales/_exposures.yml` — Power BI dashboard + ML Feature Platform (Project 4)
- `README.md` — architecture diagram, setup guide, test table, design decisions
- `images/dbt-dag.png` — lineage DAG screenshot
- GitHub Pages live: dbt docs site deployed via deploy-docs.yml
- `docs/` — complete 12-file documentation suite

## Gotchas Discovered
- Windows Long Path: venv must be at short root path (`C:\venvs\`)
- Corporate SSL proxy: `pip-system-certs` needed for `dbt deps` to reach hub.getdbt.com
- Source data `channel` field uses `api` not `partner` — contract caught this mismatch
- dbt 1.12 `accepted_values` requires `arguments:` nested key (breaking change from older syntax)
- `{% if %}` blocks are NOT valid in dbt `_sources.yml` for source-level YAML keys — use `target.database` auto-resolution instead
- `dbt-utils` is a dbt package (via `dbt deps`), NOT a pip package
- `dbt snapshot` must run BEFORE `dbt run` — `dim_customers` depends on `snap_customers`
- Databricks: `catalog: workspace` in profiles.yml sets `target.database` automatically — no need for `database:` in `_sources.yml`
- DuckDB fully-qualified path is `<db_stem>.<schema>.<table>` (e.g. `dev.dev.fact_orders`)
