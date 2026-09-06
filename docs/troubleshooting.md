# Troubleshooting Guide — Modern ELT with dbt + Data Contracts

All errors encountered during development, with root causes and fixes.

---

## Error 1: SSL Certificate Verification — `pip install dbt-duckdb` fails

**Symptom:**
```
ERROR: Could not fetch URL https://hub.getdbt.com/...
SSL: CERTIFICATE_VERIFY_FAILED unable to get local issuer certificate
```

**Root Cause:**
Corporate proxy replaces SSL certificates with its own CA, which Python/pip does not trust by default.

**Fix:**
```bash
pip install pip-system-certs
pip install dbt-duckdb
```
`pip-system-certs` monkey-patches requests to use the Windows certificate store. Install it before any dbt command that reaches the internet.

---

## Error 2: `dbt deps` fails — hub.getdbt.com unreachable

**Symptom:**
```
ConnectionError: Failed to connect to hub.getdbt.com
```

**Root Cause:** Same SSL proxy issue as Error 1.

**Fix:** Ensure `pip-system-certs` is installed first, then re-run `dbt deps`.

---

## Error 3: `dbt-utils` not found via pip

**Symptom:**
```
ERROR: No matching distribution found for dbt-utils
```

**Root Cause:**
`dbt-utils` is a **dbt package**, not a pip package. It is installed via `dbt deps` from `packages.yml`, not via `pip install dbt-utils`.

**Fix:**
```bash
# Wrong:
pip install dbt-utils

# Correct — reads packages.yml and downloads from hub.getdbt.com:
dbt deps
```

---

## Error 4: YAML Parsing Error — `{% if %}` block in `_sources.yml`

**Symptom:**
```
Parsing Error
  Error reading ecommerce_dbt: staging/_sources.yml - Runtime Error
    Syntax error near line 15
    found character that cannot start any token
```
Line 15 contains a `{% if var('source_database', none) %}` block.

**Root Cause:**
dbt does not support Jinja `{% if %}` block-level conditionals for source-level YAML property keys (like `database:`). The block syntax is invalid inside a YAML key context.

**Fix:**
Remove the `database:` field from `_sources.yml` entirely. dbt auto-resolves from `target.database`:
- DuckDB: no catalog qualifier → resolves `raw.customers`
- Databricks: `catalog: workspace` in `profiles.yml` sets `target.database = workspace` → resolves `workspace.raw.customers`

---

## Error 5: `TABLE_OR_VIEW_NOT_FOUND: workspace.snapshots.snap_customers`

**Symptom:**
```
[TABLE_OR_VIEW_NOT_FOUND] The table or view workspace.snapshots.snap_customers cannot be found.
```
Occurs during `dbt run --target prod`.

**Root Cause:**
`dim_customers` reads from the `snap_customers` snapshot table. If `dbt snapshot` has not been run first, the table does not exist.

**Fix:**
Always run `dbt snapshot` before `dbt run` in every pipeline execution:
```bash
dbt snapshot --target prod
dbt run      --target prod
```
The `run-prod.yml` GitHub Actions workflow already includes `dbt snapshot` as a dedicated step before `dbt run`.

---

## Error 6: `accepted_values` test — wrong YAML syntax

**Symptom:**
```
dbt.exceptions.CompilationException: 'accepted_values' test requires a 'values' argument
```

**Root Cause:**
dbt 1.9+ changed the `accepted_values` test syntax. The `values:` list must be nested under `arguments:`.

**Fix:**
```yaml
# Wrong (pre-1.9 syntax):
- accepted_values:
    values: ['web', 'mobile']

# Correct (dbt 1.9+):
- accepted_values:
    arguments:
      values: ['web', 'mobile']
```

---

## Error 7: Windows Long Path — `pip install` or `dbt deps` fails

**Symptom:**
```
ERROR: Could not install packages due to an OSError
[Errno 2] No such file or directory: '...\very\long\path\...'
```

**Root Cause:**
Windows has a 260-character path limit by default. dbt packages (especially `metricflow`) have deeply nested subdirectories that exceed this limit when the venv is deep inside a user profile.

**Fix:**
Create the venv at a short root path:
```bash
python -m venv C:\venvs\portfolio
```
Not: `C:\Users\username\Documents\very\deep\project\path\.venv`

---

## Error 8: `dbt docs serve` — blank lineage or missing models

**Symptom:**
`dbt docs serve` shows empty lineage graph or models missing from catalog.

**Root Cause:**
`dbt docs generate` must be run AFTER `dbt run` so that `catalog.json` and `run_results.json` exist. Running `dbt docs generate` against an empty target produces an incomplete catalog.

**Fix:**
```bash
dbt snapshot
dbt seed
dbt run
dbt docs generate   # run AFTER dbt run
dbt docs serve
```

---

## Error 9: `is_incremental()` returns False — first run always does full load

**Symptom:**
`fact_orders` replaces all rows on first run instead of incrementally processing only new records.

**Root Cause:**
Expected behavior. On the first run (table does not exist), `is_incremental()` returns `False` and dbt does a full load. On subsequent runs with the table present, it evaluates to `True` and applies the `WHERE updated_at >` filter.

**Not a bug.** To force a full reload on an existing table:
```bash
dbt run --select fact_orders --full-refresh
```

---

## Error 10: GitHub Actions — `dbt source freshness` always fails in CI

**Symptom:**
Source freshness check fails because data is always stale in CI.

**Root Cause:**
`setup_ci_db.py` populates `updated_at` with dates in 2024. The `error_after: 49h` freshness threshold will always fail against ~2-year-old synthetic data.

**Fix:**
Source freshness is intentionally not run in `ci.yml`. CI only runs contract tests (`dbt test --select source:*`). Freshness checks are meaningful only in production against real data.

---

## Error 11: `PropertyMovedToConfigDeprecation` warning in dbt 1.12

**Symptom:**
```
[WARNING][PropertyMovedToConfigDeprecation]: Found `meta` as a top-level property of models[0]
in models/intermediate/_intermediate__models.yml. Move it into `config`.
```

**Root Cause:**
dbt 1.12 changed the location of `meta` — it should be nested under `config:` rather than as a top-level property on the model definition.

**Fix:**
In `_intermediate__models.yml`, move `meta:` inside `config:`:
```yaml
# Old (deprecated):
models:
  - name: int_orders_with_customers
    meta:
      owner: analytics_engineering

# New (dbt 1.12+):
models:
  - name: int_orders_with_customers
    config:
      meta:
        owner: analytics_engineering
```
This is a warning, not an error — the pipeline still completes successfully.
