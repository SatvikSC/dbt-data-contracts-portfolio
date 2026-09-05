# Design Decisions — Modern ELT with dbt + Data Contracts

## Decision 1 — dbt Core over dbt Cloud

**Choice:** dbt Core (open-source)  
**Alternatives considered:** dbt Cloud, SQLMesh  

**Reasoning:**
- dbt Core is free and sufficient for a portfolio project
- Forces understanding of CI/CD setup from scratch (more demonstrable than using dbt Cloud's managed CI)
- SQLMesh is a compelling alternative (Python-native, better state management) but has a smaller adoption footprint in 2025; dbt Core is the industry standard

**Trade-off:** dbt Cloud adds managed scheduling, a browser IDE, and simpler CI/CD. For teams without dedicated DevOps, dbt Cloud is worth the cost. For this project, manual CI/CD setup is a feature, not a limitation.

---

## Decision 2 — Databricks SQL as the Warehouse

**Choice:** Databricks SQL  
**Alternatives considered:** Snowflake, BigQuery, Azure Synapse Analytics  

**Reasoning:**
- Reuses the Delta Lake Gold layer from Project 1 — no data movement or duplication
- Databricks SQL endpoints support dbt natively via the dbt-databricks adapter
- Demonstrates end-to-end coherence of the Azure/Databricks platform

**Trade-off:** Snowflake is arguably more common in enterprise dbt deployments. If demonstrating Snowflake-specific skills is valuable, swap the adapter — the dbt models are identical; only `profiles.yml` and some SQL syntax changes.

---

## Decision 3 — Staging Models Materialized as Views

**Choice:** `view` materialization for staging  
**Alternatives considered:** `table`, `ephemeral`  

**Reasoning:**
- Staging is a pass-through layer: rename, cast, clean — no aggregation
- Views have zero storage cost and always reflect the latest source data
- Staging should not be a persistence boundary; Silver (from Project 1) or marts are

**Trade-off:** If staging models are queried frequently by analysts or have expensive transformations, a table materialization reduces repeated compute. For a typical staging layer, views are correct.

---

## Decision 4 — Incremental Strategy: `merge` over `append`

**Choice:** `merge` with `unique_key` for all incremental models  
**Alternatives considered:** `append`, `delete+insert`  

**Reasoning:**
- `append` creates duplicates if the pipeline re-runs or backfills — makes the model non-idempotent
- `merge` is idempotent: re-running on the same data produces the same result
- `delete+insert` is safer than `append` but less atomic than `merge` on Databricks

**Trade-off:** `merge` is slower than `append` for pure-insert workloads (e.g., immutable event streams). For truly append-only data where the source guarantees no updates, `append` with a proper `unique_key` test is acceptable.

---

## Decision 5 — Data Contracts via dbt Sources (Not a Separate Contract Tool)

**Choice:** dbt `_sources.yml` as the contract definition  
**Alternatives considered:** Confluent Schema Registry, OpenAPI contract files, custom contract framework  

**Reasoning:**
- dbt sources already define expected schema, tests, and freshness in one place
- Contracts are version-controlled alongside the transformations that depend on them
- Violations are caught in CI automatically — no additional tooling required
- Simple and understandable for any engineer working in dbt

**Trade-off:** dbt sources only enforce contracts at read-time (when dbt runs). They do not prevent upstream from writing bad data to the source table. A true data contract platform (e.g., Soda, Great Expectations on the source) enforces at write-time. For this portfolio project, dbt source tests at CI time is sufficient and demonstrates the concept clearly.

---

## Decision 6 — Slim CI (`state:modified+`) over Full CI

**Choice:** Run only modified models and their downstream dependencies in CI  
**Alternatives considered:** Run all models on every PR  

**Reasoning:**
- Running all models on every PR is slow and expensive, especially as the project grows
- `state:modified+` runs only what changed plus anything downstream — correct scope for regression testing
- Requires a dbt state artifact (manifest.json) from the last production run stored in cloud storage or as a CI artifact

**Trade-off:** Slim CI requires managing the production manifest artifact. If the manifest is stale or missing, CI falls back to full run. This is slightly more complex to set up but is the industry-standard approach.

---

## Open Design Questions
- [ ] Use `dbt-expectations` package for richer test library or keep built-in tests only?
- [ ] Implement SCD Type 2 for `dim_customers` using dbt snapshots or manual logic?
- [ ] Should `intermediate` models be `ephemeral` or `view`? Depends on how many downstream models reference them.
