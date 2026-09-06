# Portfolio Showcase — Modern ELT with dbt + Data Contracts

## What This Project Demonstrates

| Skill | Evidence |
|---|---|
| Analytics engineering | Full dbt project: staging → intermediate → mart layer |
| Data modeling | Star schema: `fact_orders` + `dim_customers` (SCD Type 2) |
| Data contracts | `_sources.yml` with schema + freshness + accepted_values tests |
| Contract enforcement | `test/contract-break` branch → CI failure on PR |
| Incremental patterns | `fact_orders`: incremental, merge strategy, idempotent |
| SCD Type 2 | `snap_customers`: dbt snapshot, timestamp strategy, `dbt_valid_to` |
| CI/CD | GitHub Actions: PR gate (DuckDB) + prod deploy (Databricks) |
| Dual-target | DuckDB (dev/CI, zero cost) + Databricks SQL Warehouse (prod) |
| Documentation | 100% model + column coverage; auto-deployed dbt docs site |
| Surrogate keys | `dbt_utils.generate_surrogate_key` — deterministic, replicable |
| Custom tests | `tests/generic/assert_positive_amounts.sql` |
| Slim CI | `state:modified+` — only runs changed models + downstream |

---

## Key Talking Points for Interviews

### "Walk me through your dbt project structure."
> "I follow standard dbt layering: staging views for light cleaning, an ephemeral intermediate for joins and business logic, and mart tables — a `dim_customers` dimension with SCD2 via dbt snapshots and an incremental `fact_orders` with merge strategy. Every layer has documentation and tests."

### "How do you enforce data contracts?"
> "The contract is defined in `_sources.yml` — column names, types, accepted values, and freshness thresholds. When a PR is opened, CI runs `dbt test --select source:*` first. If the contract is violated — wrong channel value, missing column, stale data — the PR is blocked before any model runs."

### "Show me a contract violation in action."
> Point to the `test/contract-break` branch on GitHub. The PR removes `api` from channel accepted_values. CI fails at the source test step. The PR cannot be merged. That is live proof-of-concept.

### "How do you handle local dev vs production?"
> "`profiles.yml` has two targets: `dev` (DuckDB, zero cost, starts instantly) and `prod` (Databricks SQL Warehouse). The model SQL is identical — only the adapter changes. CI uses DuckDB so every PR gets full test coverage without spinning up infrastructure."

### "How does your incremental model work?"
> "`fact_orders` uses `materialized='incremental'`, `incremental_strategy='merge'`, and `unique_key='order_id'`. The merge is idempotent — re-running on the same data produces the same result. On first run it does a full load; subsequent runs only process records where `updated_at > MAX(updated_at)` in the existing table."

### "What would you add in a real production environment?"
> "(1) `dbt source freshness` alerts to Slack/PagerDuty when data is stale. (2) A data observability layer (Monte Carlo, Soda) for write-time contract enforcement — dbt sources only enforce at read time. (3) Column-level lineage to impact-analyze downstream consumers before a schema change. (4) Metadata plane querying `dbt artifacts` (manifest.json, run_results.json) for data reliability SLAs."

---

## GitHub Repository Checklist

Before sharing the repo link in an interview or on a resume:

- [ ] README has architecture diagram and 1-command local setup
- [ ] `test/contract-break` branch exists and shows a failed CI run on its PR
- [ ] GitHub Pages is enabled and the dbt docs site is live
- [ ] `images/dbt-dag.png` lineage screenshot is in the repo
- [ ] All 80 tests pass on main (green CI badge in README)
- [ ] Databricks prod run triggered at least once (Actions history shows successful prod run)
- [ ] `.env` is NOT committed; `.env.example` is present with all vars documented

---

## Resume Bullet Points

- Built production-grade ELT pipeline with dbt Core 1.12 on Databricks SQL Warehouse; 5 models across staging/intermediate/mart layers, 80 data quality tests, 100% column-level documentation
- Implemented data contracts via dbt sources with GitHub Actions CI enforcement — PR with schema violation automatically blocked before merge; demonstrated with live `test/contract-break` branch
- Designed incremental fact table with merge strategy (idempotent, zero duplicates on re-run) and SCD Type 2 customer dimension via dbt snapshots
- Engineered dual-target CI/CD: DuckDB for zero-cost local dev and PR testing, Databricks SQL Warehouse for production; auto-deployed dbt docs to GitHub Pages on every merge
