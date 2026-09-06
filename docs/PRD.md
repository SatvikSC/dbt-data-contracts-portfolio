# PRD — Modern ELT with dbt + Data Contracts

## Problem Statement
Raw data is loaded into a data warehouse but transformations are managed as ad-hoc SQL scripts with no versioning, no testing, and no documentation. Schema changes from upstream break downstream models silently. There is no contract between data producers and consumers.

## Goal
Build a production-grade analytics engineering layer using dbt on Databricks SQL, enforce data contracts between producers and consumers, and automate testing + documentation through CI/CD. Support both local development (DuckDB, zero cost) and production (Databricks SQL Warehouse).

## Non-Goals
- Raw data ingestion (covered in Project 1)
- BI dashboard development
- Real-time or streaming transformations
- ML feature engineering (covered in Project 4)

## Users / Stakeholders
| User | Need |
|---|---|
| Analytics Engineer | Maintainable, testable, version-controlled SQL transformations |
| Data Analyst | Reliable, documented mart tables they can trust |
| Data Producer | Clear contract on what schema/data quality they must deliver |
| Data Consumer | Guarantee that data quality meets their SLA |
| Platform Team | Automated deployment and regression prevention |

## Functional Requirements — All Met ✅
- Raw data in 2+ sources (customers, orders, order_items, products)
- dbt staging models: rename, cast, clean → `stg_customers`, `stg_orders`
- dbt intermediate models: joins, business logic → `int_orders_with_customers` (ephemeral)
- dbt mart models: `dim_customers` (SCD2 table), `fact_orders` (incremental)
- Data contracts: column-level schema + quality expectations in `_sources.yml`
- dbt tests: 80 tests — not_null, unique, accepted_values, relationships, custom
- dbt documentation: auto-generated docs site on GitHub Pages
- CI/CD: tests on every PR (DuckDB); prod deployment to Databricks on manual trigger

## Non-Functional Requirements — All Met ✅
| Requirement | Target | Actual |
|---|---|---|
| Test coverage | ≥3 tests per model | 80/80 pass |
| Documentation | Every model + column described | ✓ zero undocumented |
| Incremental models | `fact_orders` incremental | ✓ merge strategy |
| CI/CD | PR blocked on test failure | ✓ GitHub Actions |
| Idempotency | Full refresh = incremental result | ✓ verified |
| Lineage | Visible in dbt docs | ✓ GitHub Pages |

## Success Metrics — All Achieved
- Zero undocumented models or columns in mart layer ✓
- All dbt tests pass on every CI run ✓
- Schema violation in source caught automatically in CI ✓ (test/contract-break branch)
- Any engineer can understand any model from the docs site alone ✓
- Incremental models faster than full refresh ✓
