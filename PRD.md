# PRD — Modern ELT with dbt + Data Contracts

## Problem Statement
Raw data is loaded into a data warehouse but transformations are managed as ad-hoc SQL scripts with no versioning, no testing, and no documentation. Schema changes from upstream break downstream models silently. There is no contract between data producers and consumers.

## Goal
Build a production-grade analytics engineering layer using dbt on Databricks SQL (or Snowflake), enforce data contracts between producers and consumers, and automate testing + documentation through CI/CD.

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

## Functional Requirements
- Raw data loaded from at least 2 sources into a staging area
- dbt staging models: rename, cast, and clean raw data
- dbt intermediate models: joins, business logic, reusable building blocks
- dbt mart models: final fact and dimension tables for analytics consumption
- Data contracts: column-level schema and quality expectations defined in dbt sources
- dbt tests: not-null, unique, accepted values, referential integrity — on all models
- dbt documentation: auto-generated docs site describing all models, columns, tests
- CI/CD: tests run on every PR; deployment automated on merge to main

## Non-Functional Requirements
| Requirement | Target |
|---|---|
| Test coverage | Every model has at least 3 dbt tests |
| Documentation | Every model and column has a description in `schema.yml` |
| Incremental models | Large fact tables use incremental materialization |
| CI/CD | PRs blocked if any dbt test fails |
| Idempotency | Full refresh produces the same result as incremental run |
| Lineage | Column-level lineage visible in dbt docs |

## Success Metrics
- Zero undocumented models or columns in mart layer
- All dbt tests pass on every CI run
- A schema change in a source that violates a contract is caught automatically in CI
- Any engineer can understand any model by reading the docs site alone
- Incremental models complete faster than full refresh by measurable margin
