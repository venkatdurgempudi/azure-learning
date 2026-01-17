# Project 0 – Sandbox & Experiments

## Purpose

This project contains **early experiments, prototypes, and learning exercises**
related to Azure Data Engineering.

It is intentionally **not production-grade** and exists to:
- Explore Azure Databricks features
- Practice ingestion and merge patterns
- Test ideas quickly before formalizing them in Project 1

---

## What This Project Is

- A **learning sandbox**
- A place to experiment freely
- A record of your learning journey

It complements **Project 1**, which is the clean, end-to-end, production-style implementation.

---

## Structure

project-0-sandbox/
- adf/               # Prototype ADF pipelines (JSON exports)
- databricks/
  - notebooks/       # Experimental Databricks notebooks
- data/              # Small sample datasets (for learning only)
- infra/
  - azure-cli/       # Azure CLI scripts used during experimentation
- sql/               # Sample SQL scripts and procedures
- tools/             # Helper scripts (data generation, sync tools)
- notes/             # Project-specific notes
- secrets/
  - README.md        # Documentation only (no secrets stored)

---

## Key Characteristics

- Data may be stored locally **only for learning**
- No guarantees of schema stability
- Code may be exploratory or duplicated
- No CI/CD expectations

---

## How This Project Is Used

Typical workflow:
1. Test a concept here
2. Validate logic and approach
3. Rebuild cleanly in **Project 1**

---

## Disclaimer

This project is **not intended for production use**.
It exists purely for learning and experimentation.
