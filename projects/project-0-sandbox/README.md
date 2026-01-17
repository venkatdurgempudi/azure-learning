# Project 0 – Sandbox, Experiments, and Learning

## Overview

Project 0 is a sandbox and experimentation area used to explore Azure Data Engineering concepts before formalizing them into production-style implementations.

This project intentionally contains experimental code, learning notebooks, small sample datasets, and trial-and-error implementations.

It serves as a learning log and proof of hands-on practice, not as a deployable solution.

---

## Why This Project Exists

In real-world data engineering work, engineers prototype ideas quickly, validate logic with small datasets, experiment with APIs, Spark, ADF, and storage patterns, and refactor approaches later.

This project captures that early phase.

Once patterns are validated here, they are re-implemented cleanly in Project 1.

---

## Scope of Work

This project includes experiments related to:
- Azure Data Factory pipeline design
- Databricks ingestion and merge logic
- Incremental vs full loads
- ADLS folder-based ingestion
- Delta Lake merge patterns
- Run-date partitioning strategies
- Local-to-cloud data sync using AzCopy

---

## Folder Structure Explained

```text
├── adf
│   ├── pipeline_registrations.json
├── data
│   ├── masters
│   │   ├── gender_master.csv
│   │   ├── unit_master.csv
│   ├── registrations
│   │   ├── run_date=2026-01-05
│   │   │   ├── registrations.csv
│   │   ├── run_date=2026-01-11
│   │   │   ├── registrations.csv
│   │   ├── run=manual_001
│   │   │   ├── registrations.csv
├── databricks
│   ├── notebooks
│   │   ├── 00_adls_oauth_setup.py
│   │   ├── 01_ingest_registrations_history.py
│   │   ├── gold-silver-schema-creation.ipynb
│   │   ├── ingest_and_merge_registrations.py
├── infra
│   ├── azure-cli
│   │   ├── create_resources.sh
│   │   ├── create_sp_and_role.sh
├── notes
│   ├── .gitkeep
├── README.md
├── secrets
│   ├── README.md
├── sql
│   ├── sample_ddl.sql
│   ├── usp_insert_run_record.sql
├── tools
│   ├── generate_mock_registrations.py
│   ├── sync_to_incoming.ps1
```

## Data Handling Policy

- Sample data may exist in this project
- Data volumes are intentionally small
- No production data is used

---

## What This Project Is Not

- Not production-ready
- Not automated end-to-end
- Not performance-optimized

---

## Learning Outcomes

- Practical Databricks development
- Understanding Spark ingestion patterns
- Hands-on experience with ADLS
- ADF pipeline fundamentals

---

## Disclaimer

This project exists purely for learning and experimentation.
