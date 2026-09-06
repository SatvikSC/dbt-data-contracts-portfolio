# Setup Guide — Modern ELT with dbt + Data Contracts

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| Python | 3.11–3.13 | dbt runtime |
| pip | latest | Package manager |
| git | any | Version control |
| Databricks workspace | free trial OK | Prod target (optional for local dev) |

---

## Part 1: Local Development (DuckDB — zero cost)

### Step 1: Clone and create venv
```bash
git clone https://github.com/SatvikSC/dbt-data-contracts-portfolio.git
cd dbt-data-contracts-portfolio

# Windows — short path avoids 260-char limit on deep dbt_packages subpaths
python -m venv C:\venvs\portfolio
C:\venvs\portfolio\Scripts\activate
```

### Step 2: Install dbt
```bash
pip install dbt-duckdb pip-system-certs
```
> `pip-system-certs` is required if you are behind a corporate SSL proxy. It lets `dbt deps` reach hub.getdbt.com for package downloads.

### Step 3: Install dbt packages
```bash
dbt deps
```

### Step 4: Create profiles.yml (not committed — local only)
Create `profiles.yml` in the project root:
```yaml
ecommerce_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "C:/venvs/portfolio_db/dev.duckdb"
      schema: dev
      threads: 4
```

### Step 5: Populate the source database
```bash
python scripts/setup_ci_db.py --db-path C:/venvs/portfolio_db/dev.duckdb
```
Expected output:
```
  raw.customers          20 rows
  raw.orders             50 rows
  raw.order_items        50 rows
  raw.products           10 rows

CI database ready: C:/venvs/portfolio_db/dev.duckdb
```

### Step 6: Run the full pipeline
```bash
dbt snapshot        # creates snap_customers (SCD2)
dbt seed            # loads order_status_codes
dbt run             # builds stg_*, int_*, dim_*, fact_*
dbt test            # runs all 80 tests
```
Expected: `Completed with 0 errors, 0 warnings`

### Step 7: Explore the docs locally
```bash
dbt docs generate
dbt docs serve      # opens http://localhost:8080
```
Click the blue circle icon (bottom right) to open the lineage DAG.

---

## Part 2: Databricks Production Target

### Prerequisites
1. Create a Databricks SQL Warehouse: **Compute → SQL Warehouses → Create Warehouse**
2. Go to the **Connection details** tab → copy:
   - **Server hostname** (e.g. `adb-123456789.1.azuredatabricks.net`)
   - **HTTP path** (e.g. `/sql/1.0/warehouses/abc1234def`)
3. Create a Personal Access Token: **User Settings → Developer → Access Tokens → Generate**

### Step 1: Install Databricks adapter
```bash
pip install dbt-databricks
```

### Step 2: Add prod target to profiles.yml
```yaml
ecommerce_dbt:
  target: dev
  outputs:
    dev:
      type: duckdb
      path: "C:/venvs/portfolio_db/dev.duckdb"
      schema: dev
      threads: 4
    prod:
      type: databricks
      host: "your-workspace.azuredatabricks.net"
      http_path: "/sql/1.0/warehouses/your-warehouse-id"
      token: "dapiXXXXXXXXXXXXXXXXXXXX"
      catalog: workspace
      schema: dbt_prod
      threads: 4
```

### Step 3: Populate Databricks raw schema
```bash
export DBT_DATABRICKS_HOST=your-workspace.azuredatabricks.net
export DBT_DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
export DBT_DATABRICKS_TOKEN=dapiXXXXXX

python scripts/setup_prod_db.py
```
Expected output:
```
Schema ready: workspace.raw
  workspace.raw.customers          20 rows
  workspace.raw.orders             50 rows
  workspace.raw.order_items        50 rows
  workspace.raw.products           10 rows

Databricks raw schema ready: workspace.raw
```

### Step 4: Run dbt against prod
```bash
dbt snapshot --target prod    # workspace.snapshots.snap_customers
dbt seed     --target prod    # workspace.dbt_prod.order_status_codes
dbt run      --target prod    # workspace.dbt_prod.{stg_*, dim_*, fact_*}
dbt test     --target prod    # all 80 tests
```

Output tables: `workspace.dbt_prod.{dim_customers, fact_orders}` + `workspace.snapshots.snap_customers`

---

## Part 3: GitHub Actions CI/CD

### CI (automatic — no setup needed)
Every PR to `main` automatically triggers `.github/workflows/ci.yml`:
1. `setup_ci_db.py` — populates DuckDB raw schema
2. `dbt compile` — syntax check
3. `dbt test --select source:*` — **contract gate**
4. `dbt snapshot + dbt seed`
5. `dbt run/test --select state:modified+` — slim CI

No Databricks secrets needed. CI is fully DuckDB-based.

### GitHub Pages (one-time setup)
1. Go to repo **Settings → Pages**
2. Source: **GitHub Actions**
3. Click Save

On every push to `main`, `deploy-docs.yml` generates and deploys the dbt docs site automatically.

### Databricks Prod Run (manual trigger)
1. Add 3 GitHub Secrets (repo **Settings → Secrets and variables → Actions → New repository secret**):
   - `DBT_DATABRICKS_HOST`
   - `DBT_DATABRICKS_HTTP_PATH`
   - `DBT_DATABRICKS_TOKEN`
2. Go to **Actions → dbt Prod Run (Databricks) → Run workflow**

---

## Part 4: Demonstrate Contract Enforcement

The `test/contract-break` branch has `api` removed from the channel `accepted_values` in `_sources.yml`.

```bash
git checkout test/contract-break
# Push to GitHub and open a PR → CI fails at dbt test --select source:*
```

To restore:
```bash
git checkout main
```

This is the live demonstration that schema violations are caught in CI before merge.
