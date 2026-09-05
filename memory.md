# Memory — Modern ELT with dbt + Data Contracts

## Project Status
- **Phase:** Phase 4 complete (Documentation & Portfolio Polish)
- **Started:** 2026-09-05
- **Phases complete:** 1 (Staging), 2 (Marts), 3 (CI/CD), 4 (Documentation)

## Key Decisions Made
- dbt Core 1.12.3 (not dbt Cloud)
- Databricks SQL as prod warehouse; DuckDB 1.5.5 for local dev (zero cost)
- Staging: `view` materialization
- Intermediate: `ephemeral` (inlined as CTE)
- Dims: `table`; Facts: `incremental` with `merge` strategy
- Data contracts via dbt `_sources.yml`
- SCD Type 2 via dbt `snapshot` (strategy: timestamp, updated_at)
- Slim CI using `state:modified+` with manifest artifact
- Docs deployed to GitHub Pages
- `dbt_expectations` package: use `metaplane/dbt_expectations` (calogica namespace deprecated)
- `accepted_values` tests: use `arguments:` nesting (dbt 1.9+ syntax required)

## Environment
- Python 3.13.10
- venv: `C:\venvs\proj02_dbt` (short path — Windows 260-char limit; metricflow has deep subpaths)
- DuckDB dev DB: `C:\venvs\proj02_dbt_db\dev.duckdb`
- `pip-system-certs` required for corporate SSL proxy (hub.getdbt.com)

## What's Built
### Staging (Phase 1)
- `stg_orders.sql` — rename, cast, clean from raw.orders
- `stg_customers.sql` — rename, lowercase email, derive full_name
- `_sources.yml` — data contracts for orders + customers (17 col-level tests)
- `_staging__models.yml` — 30 model-level tests
- 47/47 tests pass

### Marts (Phase 2)
- `snap_customers` — SCD Type 2 snapshot
- `int_orders_with_customers` — ephemeral join intermediate
- `dim_customers` — current-state dimension, surrogate key
- `fact_orders` — incremental, merge, 5,000 rows, 0 duplicates
- `seeds/order_status_codes.csv` — 5 static status rows
- 79/79 tests pass

### CI/CD (Phase 3 ✅)
- `tests/generic/assert_positive_amounts.sql` — custom test
- `.github/workflows/ci.yml` — PR gate + docs deploy
- `scripts/setup_ci_db.py` — self-contained CI data generator
- 80/80 tests pass; contract breach demo confirmed (break channel → CI fails)

### Documentation (Phase 4 ✅)
- `meta` tags on all 5 models: owner, domain, tier, contains_pii
- `models/marts/sales/_exposures.yml` — Power BI dashboard + ML Feature Platform (Project 4)
- `README.md` — architecture diagram, setup guide, test table, design decisions, GitHub repo instructions
- `phases.md` and `ProdReadyCheckList.md` updated through Phase 4
- Pending: `dbt docs generate` locally + lineage screenshot + GitHub push → Pages

## Gotchas Discovered
- Windows Long Path: venv must be at short root path (`C:\venvs\`)
- Corporate SSL proxy: `pip-system-certs` needed for `dbt deps` to reach hub.getdbt.com
- Source data `channel` field uses `api` not `partner` — contract caught this mismatch
- dbt 1.12 `accepted_values` requires `arguments:` nested key (breaking from older syntax)
- `dbt-spark 1.10.3` shows update-available warning — safe to ignore (transitive dep of dbt-databricks)
- DuckDB fully-qualified path is `<db_stem>.<schema>.<table>` (e.g. `dev.dev.fact_orders`)

## Open Questions
- [x] Use dbt snapshots for SCD Type 2 → YES
- [x] Install `dbt-expectations` → YES (metaplane namespace)
- [x] Intermediate models: `ephemeral` or `view` → ephemeral (promote if 3+ consumers)

## Blockers
- GitHub Secrets for Databricks (Phase 3 prod validation) — requires live workspace
- GitHub Pages deployment requires repo to be pushed

## Lessons Learned
- Data contracts are most valuable when they catch real mismatches (channel `api` vs `partner`)
- `ephemeral` intermediate models keep lineage clean without warehouse clutter
- dbt snapshot + dim pattern gives clean SCD2 without writing custom MERGE SQL
