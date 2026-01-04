# Azure Data Engineering — Registrations Pipeline (CSV + Databricks Community Edition)

This repository contains a **detailed, end-to-end Azure data engineering demo project** that processes **CSV-based registration data** using **Azure Data Factory**, **Azure Data Lake Storage Gen2**, and **Databricks Community Edition**.

The project is intentionally designed to be:

* ✅ **Low-cost / free-tier friendly**
* ✅ **Runnable by an individual learner**
* ✅ **Interview-ready**, showing real-world Azure data engineering patterns

This is **not a toy example** — it mirrors how file-based ingestion pipelines are commonly built in production.

---

## 1. High-level architecture

**One-line flow**

CSV files → ADLS Gen2 (incoming) → Azure Data Factory (orchestration & archive) → Databricks Community (transform & merge) → ADLS Gen2 (processed Delta)

**Key design principle**

* Data **lands in storage first**
* Azure Data Factory manages **file movement & orchestration**
* Databricks handles **business logic and transformations only**

---

## 2. What this project demonstrates

This project demonstrates core Azure data engineering skills:

* File-based ingestion (CSV)
* Azure Data Lake Storage Gen2 layout design
* Azure Data Factory pipelines and orchestration
* Medallion architecture (Raw → Staging → Curated)
* Incremental + idempotent processing
* Delta Lake MERGE for deduplication
* Cost-aware architectural decisions
* Clear separation of concerns

---

## 3. Repository structure

```
.
├── LICENSE
├── README.md                 # Main project documentation
├── adf/
│   └── pipeline_registrations.json   # Azure Data Factory pipeline (CSV orchestration)
├── azure/
│   ├── create_resources.sh           # Creates RG + ADLS Gen2 + containers
│   └── create_sp_and_role.sh         # Creates Service Principal for ADLS access
├── data/
│   ├── registrations.csv             # Sample registration fact data (CSV source)
│   ├── gender_master.csv             # Reference / master data
│   └── unit_master.csv               # Reference / master data
├── notebooks/
│   └── ingest_and_merge_registrations.py  # Databricks PySpark notebook (Delta MERGE)
├── sql/
│   ├── sample_ddl.sql                # Optional SQL schema (control / demo use)
│   └── usp_insert_run_record.sql     # Optional run-metadata stored procedure
├── tools/
│   ├── gen-tree.sh                   # Utility to print repo tree
│   └── generate_mock_registrations.py# Generates synthetic CSV registration data
├── secrets/
│   └── README.md                     # Guidance for handling secrets (no secrets committed)
├── learning/
│   ├── README.md                     # Learning notes & walkthroughs
│   └── resources.md                  # Reference links & study material
```

---

## 4. Prerequisites

### Local

* Git (optional)
* VS Code or any text editor
* Azure CLI (`az login` completed)

### Azure

* Azure subscription (Free Trial is fine)
* Azure Storage Account (ADLS Gen2 enabled)
* Azure Data Factory
* Databricks **Community Edition** account

Optional:

* Azure Storage Explorer (recommended for beginners)

---

## 5. How CSV data arrives in Azure (important concept)

This project assumes **CSV files already arrive in Azure Data Lake Storage**.

This is very common in real-world systems where:

* Vendors drop daily CSV exports
* Applications write files directly to storage
* Databases export snapshots
* SFTP feeds land files automatically

For learning and demos, **manual upload is perfectly acceptable**.

---

## 6. Create Azure resources

### A. Create Resource Group & Storage Account

Use the provided script:

```bash
./azure/create_resources.sh my-rg eastus mystorageacct123
```

This creates:

* Resource Group
* ADLS Gen2 Storage Account
* Containers:

  * `incoming` (raw files)
  * `processed` (Delta tables)
  * `archive` (historical raw files)
  * `control` (run metadata)

Alternatively, create the same resources using the Azure Portal.

---

## 7. Upload CSV files to ADLS Gen2

Upload CSV files to the **incoming** container.

### Recommended folder structure

```
incoming/
└── registrations/
    └── run=2026-01-04/
        └── sample_registrations.csv
```

### Upload options

**Option A — Azure Storage Explorer**

* Drag & drop the file

**Option B — Azure CLI**

```bash
az storage blob upload \
  --account-name mystorageacct123 \
  --container-name incoming \
  --name registrations/run=2026-01-04/sample_registrations.csv \
  --file data/sample_registrations.csv
```

---

## 8. Azure Data Factory setup

### Create Data Factory

1. Azure Portal → Create Resource → **Azure Data Factory**
2. Choose Resource Group & region
3. Create without Git integration (simpler)

---

## 9. ADF pipeline responsibility (important)

Because this project uses **Databricks Community Edition**, ADF does **not** trigger Databricks directly.

ADF is responsible for:

* Organizing raw files
* Creating run-based folders
* Archiving processed CSVs
* (Optionally) writing run metadata

Databricks is run **separately**.

This limitation is **intentional and realistic** for low-cost setups.

---

## 10. Import ADF pipeline

1. Open ADF → Author tab
2. Pipelines → **Import from JSON**
3. Select:

```
adf/pipeline_registrations.json
```

### After import

* Update Linked Service names
* Disable or remove Databricks activities (if present)
* Validate pipeline

---

## 11. Databricks Community Edition setup

### Upload notebook

1. Log into Databricks Community Edition
2. Workspace → Create → Notebook
3. Paste contents of:

```
notebooks/ingest_and_merge_registrations.py
```

---

## 12. Accessing data in Databricks Community

Databricks Community **cannot securely mount ADLS Gen2**.

For learning purposes, use one of these approaches:

### Option A — Temporary public container (demo only)

* Make container public
* Read using HTTPS

### Option B — Upload CSVs to DBFS (recommended for Community)

```python
dbutils.fs.cp(
  "file:/Workspace/sample_registrations.csv",
  "dbfs:/tmp/registrations/sample_registrations.csv"
)
```

Then read:

```python
spark.read.csv("dbfs:/tmp/registrations/", header=True)
```

---

## 13. Databricks processing logic

The notebook performs:

* Explicit schema enforcement
* Deduplication by `registration_id`
* Enrichment (derived fields)
* Delta Lake MERGE (idempotent)

### Output structure

```
processed/
├── staging/patient_registrations
└── reports/fact_registrations
```

---

## 14. Validation scenarios

Run the notebook multiple times to validate:

* ✅ Idempotency (no duplicates)
* ✅ Updates overwrite existing records
* ✅ Late-arriving records are merged correctly

---

## 15. Cost considerations

* Databricks Community Edition = **free**
* ADLS Gen2 costs are minimal for small CSVs
* No always-on compute

---

## 16. Known limitations (intentional)

* No direct ADF → Databricks trigger
* Simplified security model
* File-based ingestion only

These are deliberate trade-offs for learning and cost control.

---

## 17. Future enhancements

* Move to Azure Databricks for full integration
* Add SFTP → ADLS ingestion
* Implement CDC-based ingestion
* Add CI/CD for ADF pipelines
* Implement SCD Type 2 dimensions

---

## 18. How to explain this project in interviews

> “This project demonstrates a file-based Azure data pipeline where CSV files land in ADLS Gen2, Azure Data Factory handles orchestration and file management, and Databricks Community Edition performs transformation and Delta Lake merges. The design mirrors real-world ingestion patterns while remaining cost-effective.”

