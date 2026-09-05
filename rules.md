# Rules — Modern ELT with dbt + Data Contracts

## SQL Style
- All SQL keywords uppercase: `SELECT`, `FROM`, `WHERE`, `JOIN`
- One column per line in SELECT statements
- CTEs preferred over nested subqueries
- CTE names: descriptive, snake_case (`renamed`, `validated`, `joined`, `final`)
- Last CTE always named `final`; model ends with `SELECT * FROM final`
- No `SELECT *` except in the final CTE of a staging model (where source schema is controlled)

## dbt Model Naming
| Layer | Prefix | Example |
|---|---|---|
| Staging | `stg_` | `stg_orders.sql` |
| Intermediate | `int_` | `int_orders_enriched.sql` |
| Fact | `fact_` | `fact_orders.sql` |
| Dimension | `dim_` | `dim_customers.sql` |
| Aggregate/report | `rpt_` | `rpt_daily_revenue.sql` |

## Model Documentation Rules
- Every model must have a `description` in `schema.yml`
- Every column in staging and mart models must have a `description`
- Intermediate models: at minimum a model-level description
- No model deployed to main without documentation

## Testing Rules
- Every staging model: `not_null` + `unique` on primary key column
- Every mart fact table: `not_null` + `unique` on surrogate key
- Every foreign key relationship: `relationships` test
- Every status/type column: `accepted_values` test
- Source tables: freshness test defined (`warn_after` + `error_after`)
- Custom tests go in `tests/generic/` as macros

## Data Contract Rules
- Source schemas defined in `_sources.yml` in the staging folder — this IS the contract
- Changing a source column name or type requires updating the contract file in the same PR
- Any new source table added to the project must have a source definition before use
- Freshness thresholds must be agreed with the upstream team and documented in `_sources.yml`

## Materialization Rules
- Staging: always `view` (never `table` — staging is not a persistence layer)
- Intermediate: `ephemeral` by default; use `view` only if reused by 3+ downstream models
- Marts: `table` for dimensions; `incremental` for facts with >1M rows
- Incremental strategy: `merge` with `unique_key` — never `append` (creates duplicates)

## Surrogate Keys
- Never use source system IDs as surrogate keys in dimension tables
- Use `{{ dbt_utils.generate_surrogate_key(['col1', 'col2']) }}` for deterministic keys
- Document the natural key components in column description

## Git Workflow
- Branch naming: `feature/model-name`, `fix/test-name`, `chore/docs`
- PRs must pass CI (dbt compile + dbt test) before merge
- Squash and merge to keep main history clean
- Commit messages describe the business change, not the SQL (`add customer lifetime value metric`)

## Column Naming Conventions
| Column Type | Convention | Example |
|---|---|---|
| Primary key | `<entity>_id` | `order_id` |
| Foreign key | `<entity>_id` | `customer_id` |
| Date | `<event>_date` | `order_date` |
| Timestamp | `<event>_at` | `created_at` |
| Boolean | `is_<state>` or `has_<thing>` | `is_active`, `has_discount` |
| Amount/money | `<metric>_amount` | `order_amount` |
| Count | `<thing>_count` | `line_item_count` |
| Flag/status | `<thing>_status` | `order_status` |
