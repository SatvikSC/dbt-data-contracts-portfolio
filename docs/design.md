# Design Decisions — Modern ELT with dbt + Data Contracts

## Decision 1 — dbt Core over dbt Cloud

**Choice:** dbt Core (open-source)
**Alternatives considered:** dbt Cloud, SQLMesh

**Reasoning:**
- dbt Core is free and sufficient for a portfolio project
- Forces understanding of CI/CD setup from scratch (more demonstrable than dbt Cloud's managed CI)
- SQLMesh is compelling (Python-native, better state management) but has smaller adoption than dbt Core in 2025

**Trade-off:** dbt Cloud adds managed scheduling, a browser IDE, and simpler CI/CD. For teams without dedicated DevOps, dbt Cloud is worth the cost. Manual CI/CD setup here is a feature, not a limitation.

---

## Decision 2 — Databricks SQL as Production Warehouse, DuckDB for Dev/CI

**Choice:** Databricks SQL (prod) + DuckDB (dev/CI)
**Alternatives considered:** Snowflake, BigQuery, DuckDB-only

**Reasoning:**
- DuckDB for dev/CI: zero cost, zero infra, starts in milliseconds, identical SQL dialect — every PR gets full test coverage without a running warehouse
- Databricks SQL for prod: Unity Catalog, Delta Lake, production-grade; consistent with Project 1 Lakehouse Platform
- `profiles.yml` has both targets; only `--target prod` flag changes; model SQL is identical across both engines

**Trade-off:** Snowflake is more common in enterprise dbt deployments. Swapping adapters only requires changing `profiles.yml` and `setup_prod_db.py` — model SQL is warehouse-agnostic.

---

## Decision 3 — Staging Models Materialized as Views

**Choice:** `view` materialization for staging
**Alternatives considered:** `table`, `ephemeral`

**Reasoning:**
- Staging is a pass-through layer: rename, cast, clean — no aggregation
- Views have zero storage cost and always reflect the latest source data
- Staging should not be a persistence boundary; marts are

**Trade-off:** If staging models are queried frequently by analysts or have expensive transformations, a table materialization reduces repeated compute. For a typical staging layer, views are correct.

---

## Decision 4 — Incremental Strategy: `merge` over `append`

**Choice:** `merge` with `unique_key` for all incremental models
**Alternatives considered:** `append`, `delete+insert`

**Reasoning:**
- `append` creates duplicates if the pipeline re-runs or backfills — non-idempotent
- `merge` is idempotent: re-running on the same data produces the same result
- `delete+insert` is safer than `append` but less atomic than `merge` on Databricks

**Trade-off:** `merge` is slower than `append` for pure-insert workloads (e.g., immutable event streams). For truly append-only data where the source guarantees no updates, `append` with a proper `unique_key` test is acceptable.

---

## Decision 5 — Data Contracts via dbt Sources (Not a Separate Contract Tool)

**Choice:** dbt `_sources.yml` as the contract definition
**Alternatives considered:** Confluent Schema Registry, OpenAPI contract files, custom contract framework

**Reasoning:**
- dbt sources define expected schema, tests, and freshness in one place
- Contracts are version-controlled alongside the transformations that depend on them
- Violations are caught in CI automatically — no additional tooling required
- Contract enforcement is demonstrated on the `test/contract-break` branch (removes `api` from channel accepted_values → CI fails)

**Trade-off:** dbt sources only enforce contracts at read-time (when dbt runs). They do not prevent upstream from writing bad data. A true data contract platform (Soda, Great Expectations on the source) enforces at write-time.

---

## Decision 6 — Slim CI (`state:modified+`) over Full CI

**Choice:** Run only modified models and their downstream dependencies in CI
**Alternatives considered:** Run all models on every PR

**Reasoning:**
- Running all models on every PR is slow and expensive as the project grows
- `state:modified+` runs only what changed plus anything downstream
- Requires a dbt state artifact (manifest.json) from the last prod run, stored as a GitHub Actions artifact
- Falls back to full run if manifest is missing (first-ever run)

**Trade-off:** Slightly more complex setup (manifest management). Industry-standard approach.

---

## Decision 7 — Intermediate Models as `ephemeral` (not `view`)

**Choice:** `ephemeral` for `int_orders_with_customers`
**Alternatives considered:** `view`, `table`

**Reasoning:**
- The intermediate model is a simple join used by only 2 downstream models
- `ephemeral` inlines the CTE — no warehouse object is created, lineage stays clean
- If 3+ downstream models reference it, promote to `view` to avoid repeated computation

**Trade-off:** `ephemeral` can make debugging harder (no table to query directly). Use `--full-refresh` and inspect compiled SQL in `target/compiled/` when debugging.

---

## Decision 8 — SCD Type 2 via dbt Snapshots

**Choice:** dbt snapshot with `strategy: timestamp, updated_at`
**Alternatives considered:** Manual MERGE SQL, overwrite-and-archive pattern

**Reasoning:**
- dbt snapshots handle SCD2 bookkeeping automatically: `dbt_valid_from`, `dbt_valid_to`, `dbt_scd_id`
- No custom MERGE SQL needed — easier to maintain and test
- `dim_customers` reads `WHERE dbt_valid_to IS NULL` for current records

**Trade-off:** dbt snapshots must run **before** `dbt run` in every pipeline execution. If snapshot is skipped, `dim_customers` will not reflect changes since the last snapshot.

---

## Decision 9 — `target.database` Auto-Resolution for Sources

**Choice:** Omit `database:` from `_sources.yml`; let dbt resolve from `target.database`
**Alternatives considered:** Jinja `{% if %}` block per target, `var()` per environment

**Reasoning:**
- dbt YAML source files do not support Jinja `{% if %}` block-level conditionals for property keys — this causes a YAML parse error
- Omitting `database:` makes dbt use `target.database` automatically: DuckDB uses no catalog qualifier; Databricks uses `catalog: workspace` from `profiles.yml`
- Zero code change between environments — single `_sources.yml` works for both

**Trade-off:** Less explicit. Requires understanding that `catalog:` in `profiles.yml` drives source resolution on Databricks.
