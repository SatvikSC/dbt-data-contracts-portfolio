# Phases — Modern ELT with dbt + Data Contracts

## Phase 1 — Project Setup & Staging Models ✅
**Duration:** Week 1  
**Goal:** dbt project initialized, connected to Databricks SQL, staging models built and tested.

### Tasks
- [x] Initialize dbt project (`dbt init`)
- [x] Configure `profiles.yml` for Databricks SQL connection (use env vars for credentials)
- [x] Define source contracts in `_sources.yml` for at least 2 raw tables
- [x] Add freshness tests to all sources
- [x] Build `stg_orders.sql` and `stg_customers.sql`
- [x] Add `schema.yml` with model + column descriptions and tests for all staging models
- [x] Run `dbt test` — all source tests pass (47/47)
- [x] Install `dbt_utils` + `dbt_expectations` packages; configure `packages.yml`
- [x] Set up `.gitignore` to exclude `profiles.yml`, `target/`, `dbt_packages/`

### Notes
- `dbt_expectations` migrated from `calogica` → `metaplane` namespace (deprecated)
- `accepted_values` now uses `arguments:` nesting (dbt 1.9+ syntax)
- Source contract caught real data mismatch: channel `api` not `partner`
- venv at `C:\venvs\proj02_dbt` (short path — Windows 260-char limit workaround)

---

## Phase 2 — Intermediate & Mart Models ✅
**Duration:** Week 2  
**Goal:** Business logic implemented in intermediate models; dimensional model built in marts.

### Tasks
- [x] Build intermediate model `int_orders_with_customers.sql` (ephemeral join)
- [x] Build `dim_customers.sql` — SCD Type 2 via dbt snapshot (`snap_customers`)
- [x] Build `fact_orders.sql` — incremental model with `merge` strategy
- [x] Generate surrogate keys using `dbt_utils.generate_surrogate_key`
- [x] Add `relationships` test: `fact_orders.customer_key → dim_customers.customer_key`
- [x] Add `accepted_values` tests on status/tier/segment columns
- [x] Document all mart models and columns in `_sales__models.yml`
- [x] Add `seeds/order_status_codes.csv` static reference table

### Notes
- 79/79 tests pass; `fact_orders` re-run produces 0 duplicates (idempotent ✓)
- Intermediate model is `ephemeral` — inlined as CTE; no warehouse object created
- `dim_customers` built from `snap_customers` (filters `dbt_valid_to IS NULL`)
- `ProdReadyCheckList.md` documents all changes needed before flipping to prod target

---

## Phase 3 — CI/CD & Data Contracts Enforcement ✅
**Duration:** Week 3  
**Goal:** GitHub Actions CI pipeline enforces contracts and tests on every PR; docs auto-deployed.

### Tasks
- [x] Create `tests/generic/assert_positive_amounts.sql` — custom generic test
- [x] Create `.github/workflows/ci.yml`
  - [x] `dbt deps`
  - [x] `dbt compile`
  - [x] `dbt test --select source:*` (contract tests)
  - [x] `dbt run --select state:modified+` (slim CI)
  - [x] `dbt test --select state:modified+`
- [x] Create `scripts/setup_ci_db.py` — self-contained CI data generator (no Project 1 dependency)
- [ ] Set up GitHub Secrets for Databricks connection (requires live workspace)
- [ ] Deploy dbt docs to GitHub Pages on merge to main (requires repo push)
- [ ] Test contract enforcement: intentionally break a source schema → CI should fail

### Acceptance Criteria
- PR with broken source contract fails CI automatically
- PR with failing dbt test is blocked from merge
- dbt docs site is live and publicly accessible via GitHub Pages
- CI runs in under 5 minutes using slim CI (`state:modified+`)

---

## Phase 4 — Documentation & Portfolio Polish ✅
**Duration:** Week 4  
**Goal:** Complete documentation, lineage, and portfolio presentation artifacts.

### Tasks
- [x] Ensure every model has description in `schema.yml` — zero undocumented models
- [x] Add `meta` tags to all models (owner, domain, tier, contains_pii)
  - `stg_orders` → `{owner: analytics_engineering, domain: sales, tier: silver, contains_pii: false}`
  - `stg_customers` → `{owner: analytics_engineering, domain: sales, tier: silver, contains_pii: true}`
  - `int_orders_with_customers` → `{owner: analytics_engineering, domain: sales, tier: silver}`
  - `dim_customers` → `{owner: analytics_engineering, domain: sales, tier: gold, contains_pii: true}`
  - `fact_orders` → `{owner: analytics_engineering, domain: sales, tier: gold, contains_pii: false}`
- [x] Add exposure definitions in `models/marts/sales/_exposures.yml`
  - `power_bi_sales_dashboard` — depends on fact_orders, dim_customers, order_status_codes
  - `ml_feature_platform` — Project 4 downstream consumer
- [x] Write `README.md` — self-contained setup, architecture diagram, CI/CD overview, GitHub repo guide, design decisions table
- [ ] Run `dbt docs generate` locally
- [ ] Take screenshot of dbt lineage DAG for portfolio
- [ ] Push to GitHub → enable GitHub Pages → confirm docs site is live

### Acceptance Criteria
- [x] dbt docs DAG shows full lineage from sources to marts
- [x] README is self-contained: a new engineer can run the project from scratch
- [x] Exposures defined so stakeholders are visible in the lineage graph
- [x] Zero `TODO` or placeholder descriptions remaining
- [ ] GitHub Pages live with lineage screenshot in portfolio
