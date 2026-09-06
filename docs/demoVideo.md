# Demo Video Script — Modern ELT with dbt + Data Contracts

## Overview (30 seconds)
"This project demonstrates production-grade analytics engineering with dbt. It shows how data contracts prevent schema-breaking changes from reaching downstream consumers, how a dimensional model is built and maintained incrementally, and how CI/CD enforces quality on every PR — automatically."

---

## Scene 1: Show the Data Contract (1 minute)

Open `models/staging/_sources.yml`. Point to:
- The `channel` accepted_values test: `['web', 'mobile', 'store', 'api']`
- The freshness thresholds: `warn_after: 25h, error_after: 49h`
- The `not_null` + `unique` tests on primary keys
- The description block explaining this file IS the contract

"This YAML file is the contract between producers and consumers. If upstream changes the schema — adds a new channel, removes a column, delivers stale data — CI catches it immediately."

---

## Scene 2: Demonstrate Contract Enforcement (1 minute)

Switch to GitHub. Open the **`test/contract-break` branch** PR:
- Scroll to the CI checks section
- Show the CI failure at `dbt test --select source:*`
- Click into the failed step and show: `Got 12 results, configured to fail if != 0`
- Show the column: `order_channel` — a value outside `['web','mobile','store','api']`

"A single removed value from the accepted list — and CI fails. The PR is blocked. The violation never reaches analysts."

---

## Scene 3: Show the dbt DAG / Lineage (1 minute)

Open the live dbt docs site (GitHub Pages URL).
- Click the blue lineage icon (bottom right of the page)
- Show the DAG: raw sources → staging views → intermediate (ephemeral) → fact + dim
- Click `fact_orders` → show the **Tests** tab (all passing) and **Columns** tab (with descriptions)
- Click `dim_customers` → show it reads from `snap_customers` (SCD2)
- Click a source node → show freshness threshold configuration

"Every model is documented, every column is described, every test is visible. This is the living contract between the data team and its consumers."

---

## Scene 4: Show the CI/CD Pipeline (1 minute)

Open **GitHub → Actions**:
- Show `ci.yml` — runs on every PR with DuckDB, no Databricks secrets needed, completes in ~3 minutes
- Show `run-prod.yml` — manual trigger; runs against Databricks SQL Warehouse, creates `workspace.dbt_prod.*`
- Show `deploy-docs.yml` — auto-deploys dbt docs to GitHub Pages on every push to main
- Point out the green checkmarks on `main`

"Three workflows. Contract enforcement on every PR — free, fast, no warehouse. Production Databricks run on demand. Docs auto-deployed on merge."

---

## Scene 5: Run Locally (1 minute)

In the terminal (portfolio venv active):
```bash
python scripts/setup_ci_db.py --db-path C:/venvs/portfolio_db/dev.duckdb
dbt snapshot && dbt seed && dbt run
dbt test
```

Show the output: `Completed with 0 errors` — 80 tests pass, 5 models built.

"Zero infrastructure. Anyone who clones this repo can run the full pipeline in under 2 minutes."

---

## Talking Points for Live Demo / Interview

- "The contract is the `_sources.yml` file — it's version-controlled, co-located with the models that depend on it, and enforced in CI. Not a separate tool, not a spreadsheet."
- "Incremental `merge` strategy means the pipeline is idempotent. Re-running on the same data produces the same result. No duplicate rows, no manual deduplication."
- "DuckDB for dev/CI and Databricks for prod is not a compromise — the model SQL is identical. Only the `--target` flag changes."
- "Slim CI with `state:modified+` means a staging-only change doesn't rerun the entire pipeline. Only what changed plus anything downstream."
- "SCD2 via dbt snapshots keeps the customer history automatically. `dim_customers` always shows current records with `WHERE dbt_valid_to IS NULL`. To see historical state, remove that filter."
