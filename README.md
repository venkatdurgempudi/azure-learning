# Azure Data Engineering — Registrations Pipeline (CSV + Azure Databricks)

This repository contains a **complete, end-to-end Azure data engineering project** that processes **CSV-based registration data** using **Azure Data Lake Storage Gen2 (ADLS)**, **Azure Databricks**, and **Azure Data Factory (ADF)**.

The project is designed to be:

* ✅ **Low-cost & Pay‑As‑You‑Go friendly**
* ✅ **Runnable by an individual learner**
* ✅ **Production‑realistic & interview‑ready**

This is **not a toy pipeline**. It intentionally mirrors **real-world file-based ingestion patterns** used across healthcare, retail, and enterprise analytics platforms.

---

## 1. High-level architecture

### One-line flow

CSV files → ADLS Gen2 (incoming) → Azure Databricks (history + daily MERGE) → ADLS Gen2 (Delta tables)

### Key design principles

* Data **lands in storage first** (decoupled ingestion)
* ADLS Gen2 is the **system of record**
* Databricks performs **all transformations & business logic**
* Delta Lake ensures **idempotency, updates, and ACID guarantees**

---

## 2. What this project demonstrates

This project demonstrates **core Azure Data Engineering skills**:

* File-based ingestion (CSV)
* ADLS Gen2 container & folder layout design
* Historical (bootstrap) + daily incremental processing
* Explicit schema enforcement
* Data quality handling (timestamp parsing)
* Delta Lake MERGE with **business keys**
* Idempotent, re-runnable pipelines
* Cost-aware Azure Databricks usage

---

## 3. Repository structure

```
.
├── LICENSE
├── README.md
├── adf/
│   └── pipeline_registrations.json
├── azure/
│   ├── create_resources.sh
│   └── create_sp_and_role.sh
├── data/
│   ├── registrations.csv
│   ├── gender_master.csv
│   └── unit_master.csv
├── notebooks/
│   ├── 01_ingest_registrations_history.py
│   └── 02_ingest_registrations_daily.py
├── sql/
│   ├── sample_ddl.sql
│   └── usp_insert_run_record.sql
├── tools/
│   ├── gen-tree.sh
│   └── generate_mock_registrations.py
├── secrets/
│   └── README.md
├── learning/
│   ├── README.md
│   └── resources.md
```

---

## 4. Prerequisites

### Local

* Git
* VS Code or any editor
* Azure CLI (`az login` completed)

### Azure

* Azure Subscription (Free Trial / PAYG)
* ADLS Gen2 Storage Account (HNS enabled)
* Azure Databricks (Standard tier)
* Azure Data Factory (optional orchestration)

Recommended:

* Azure Storage Explorer

---

## 5. How CSV data arrives in Azure

This project assumes **CSV files already land in ADLS Gen2**, which is common in production systems:

* Vendor feeds
* Batch exports
* SFTP drops
* Application snapshots

For learning purposes, **manual upload is perfectly acceptable**.

---

## 6. ADLS Gen2 layout

```
incoming/
├── registrations/
│   ├── run=manual_001/          # historical bootstrap
│   └── run_date=YYYY-MM-DD/     # daily increments
├── masters/
│   ├── gender_master.csv
│   └── unit_master.csv

processed/
└── reports/
    └── fact_registrations/      # Delta Lake table
```

---

## 7. Create Azure resources

Use the provided script:

```bash
./azure/create_resources.sh rg-registrations eastus stregistrationsde001
```

Creates:

* Resource Group
* ADLS Gen2 Storage Account
* Containers: `incoming`, `processed`, `archive`, `control`

---

## 8. Upload CSV files

Upload CSVs to ADLS using:

* Azure Storage Explorer (recommended)
* Azure CLI

Example:

```bash
az storage blob upload \
  --account-name stregistrationsde001 \
  --container-name incoming \
  --name registrations/run_date=2026-01-05/registrations.csv \
  --file data/registrations.csv
```

---

## 9. Azure Databricks setup

### Create workspace

* Azure Portal → Azure Databricks
* Standard tier (PAYG)
* Single-node clusters for cost control

### Cluster settings (important)

* Mode: Single Node
* Auto-termination: 10 minutes
* Smallest available VM

---

## 10. Authentication (ADLS → Databricks)

Databricks accesses ADLS using **Service Principal OAuth**:

* Client ID
* Client Secret
* Tenant ID

OAuth config is applied **inside notebooks** for learning purposes.

---

## 11. Processing design

### Phase 1 — Historical bootstrap (one-time)

Notebook:

```
01_ingest_registrations_history
```

* Reads `incoming/registrations/run=manual_001/`
* Deduplicates by business key
* Writes initial Delta table

### Phase 2 — Daily incremental loads

Notebook:

```
02_ingest_registrations_daily
```

* Reads one `run_date`
* Explicit timestamp parsing (`yyyy-MM-dd HH:mm:ss`)
* Deduplicates latest records
* MERGEs into Delta table

---

## 12. Delta Lake MERGE logic (critical)

The **business key** used for idempotency:

```
(registration_id, patient_id, unit_id)
```

MERGE behavior:

* Match → UPDATE existing row
* No match → INSERT new row

Final table always contains **one row per business key**.

---

## 13. Output

Output is a **Delta Lake table**, not a single file:

```
processed/reports/fact_registrations/
├── _delta_log/
└── part-*.parquet
```

Query using Databricks:

```python
spark.read.format("delta").load(FACT_PATH).show()
```

---

## 14. Validation scenarios

* Re-run same daily file → no duplicates
* Update existing registration → row updated
* Late-arriving data → merged correctly

---

## 15. Cost considerations

* Azure Databricks PAYG
* Single-node cluster
* Auto-termination enabled

Typical learning cost:

* ₹150–₹250 per month

---

## 16. Known limitations (intentional)

* File-based ingestion only
* Manual Databricks execution (no jobs yet)
* Simplified security for learning

---

## 17. Future enhancements

* Databricks Jobs (scheduling)
* ADF orchestration end-to-end
* CDC-based ingestion
* SCD Type 2 dimensions
* Data quality dashboards

---

## 18. How to explain this project in interviews

> “This project implements a production-style Azure data pipeline where CSV files land in ADLS Gen2, Azure Databricks performs historical and daily incremental processing using Delta Lake MERGE with business keys, and the final curated dataset represents the latest state of registrations in an idempotent and cost-efficient manner.”
