# Production Readiness Checklist — Project 2 (dbt + Data Contracts)

## Pre-Flight: Project 1 Dependency

Project 2 reads from Project 1's Bronze Delta tables on Databricks.
Project 1 MUST have run successfully before any `dbt run --target prod`.

- [ ] Project 1 pipeline has executed on Databricks at least once
- [ ] Bronze Delta tables exist for: `orders`, `customers`, `order_items`, `products`, `inventory`
- [ ] Tables are readable from a SQL warehouse (not just a cluster)

---

## 1. Source Contract Alignment

Project 1's Bronze layer adds 4 metadata columns and stores ALL columns as `STRING`.
The `_sources.yml` must reflect the real Databricks schema before pointing at prod.

### Update `_sources.yml`:

**Change 1 — Add `database` and correct `schema`:**
```yaml
# Current (DuckDB dev):
sources:
  - name: raw_ecommerce
    schema: raw

# Change to (Databricks prod):
sources:
  - name: raw_ecommerce
    database: "<your_unity_catalog_name>"   # e.g. corp_analytics or main
    schema: bronze                          # Project 1 writes to 'bronze' schema
```

**Change 2 — Change `loaded_at_field` for freshness:**
```yaml
# Current (DuckDB dev):
loaded_at_field: updated_at

# Change to (Databricks prod):
loaded_at_field: _ingest_timestamp     # Project 1 Bronze adds this column
```

**Change 3 — Add Bronze metadata columns to source definitions:**

Project 1's `bronze_ingestor.py` adds these 4 columns to every table:

| Column | Type | Notes |
|---|---|---|
| `_ingest_timestamp` | TIMESTAMP | When the file was ingested — use as freshness field |
| `_source_file` | STRING | CSV filename that produced the row |
| `_batch_id` | STRING | Idempotency hash (MD5 of file path) |
| `ingest_date` | STRING | Partition column (YYYY-MM-DD) |

Add them to each table's `columns:` list in `_sources.yml` so lineage is complete.

---

## 2. `profiles.yml` — Prod Target Credentials

The `prod` target is already defined in `profiles.yml`. Fill in these env vars in `.env` (copied from `.env.example`):

```bash
DBT_DATABRICKS_HOST=<your-workspace>.azuredatabricks.net
DBT_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/<warehouse-id>
DBT_DATABRICKS_TOKEN=dapi<token>
DBT_TARGET_CATALOG=<catalog-name>
DBT_TARGET_SCHEMA=dbt_prod   # schema where dbt will CREATE models
```

Switch to prod target with:
```bash
dbt run --target prod
```

---

## 3. Staging Models — No Changes Required

`stg_orders.sql` and `stg_customers.sql` already CAST all columns from STRING.
This is correct for Databricks Bronze where `inferSchema=False` stores everything as STRING.
No SQL changes needed when switching targets.

---

## 4. CI/CD Secrets (Phase 3)

When setting up GitHub Actions for the prod pipeline, add these as GitHub Secrets:
- `DBT_DATABRICKS_HOST`
- `DBT_DATABRICKS_HTTP_PATH`
- `DBT_DATABRICKS_TOKEN`
- `DBT_TARGET_CATALOG`
- `DBT_TARGET_SCHEMA`

---

## 5. Pre-Prod Validation Commands

Run these in order before the first full prod deploy:

```bash
# 1. Verify source contracts hold against real Databricks data
dbt test --select source:* --target prod

# 2. Check source freshness
dbt source freshness --target prod

# 3. Run models (staging + intermediate + marts)
dbt run --target prod

# 4. Run all tests
dbt test --target prod
```

---

## 6. Slim CI Manifest (Phase 3)

Slim CI (`dbt run --select state:modified+`) requires a `manifest.json` from the last
production run. After first prod deploy, store it as a GitHub Actions artifact or in ADLS:

```bash
# After dbt run --target prod, upload manifest:
az storage blob upload \
  --account-name <storage-account> \
  --container dbt-state \
  --name manifest.json \
  --file target/manifest.json
```

---

## Status

| Phase | Status | Notes |
|---|---|---|
| Phase 1 — Staging | Complete | 47/47 tests passing locally |
| Phase 2 — Marts | Complete | 79/79 tests passing; 5,000 fact rows; 0 duplicates |
| Phase 3 — CI/CD | Complete (local) | 80/80 tests; CI workflow written; contract breach demo passed; GitHub push needed for Pages |
| Phase 4 — Docs | Complete | README, _exposures.yml, meta tags on all 5 models; run `dbt docs generate` + screenshot pending |
