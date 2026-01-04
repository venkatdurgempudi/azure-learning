# Azure Data Engineering — Registrations Pipeline (starter)

This repository contains starter artifacts to build a small end‑to‑end Azure data engineering pipeline for a Registrations dashboard. It is designed to run from your laptop (local SQL Server Developer Edition) and a low‑cost Azure subscription.

Contents (what I added)
- azure/create_resources.sh — CLI script to create Resource Group + ADLS Gen2 storage account + containers
- azure/create_sp_and_role.sh — CLI script to create a Service Principal (Storage Blob Data Contributor)
- sql/sample_ddl.sql — local SQL Server DDL: masters, `patient_registrations`, control table
- sql/usp_insert_run_record.sql — optional stored procedure to upsert run metadata into Azure SQL
- data/sample_registrations.csv — small sample CSV
- adf/pipeline_registrations.json — ADF pipeline template (incremental 7‑day extract → Databricks → archive → metadata)
- notebooks/ingest_and_merge_registrations.py — Databricks PySpark notebook for dedupe/enrich/merge into Delta

This README below contains exact step‑by‑step instructions tailored to your environment (Windows 10, SQL Server Developer) so you can run the project with minimal Azure spend.

---

## Quick architecture (one line)
On‑prem (local SQL Server) → ADF (Self‑Hosted IR) copies 7‑day window → ADLS Gen2 incoming → Databricks notebook dedupe/enrich → Delta in processed container → archive + run metadata.

---

## Prerequisites (local & Azure)
Local (on your laptop)
- Microsoft SQL Server 2022 Developer (you already have)
- SQL client: SQL Server Management Studio (SSMS) or Azure Data Studio
- Git (optional) + text editor (VS Code)
- PowerShell / Git Bash / WSL (for Azure CLI scripts)
- Python (optional, for generating mock data)

Azure
- Azure subscription (free trial if eligible)
- Azure CLI installed and logged in: `az login`
- (Recommended) GitHub account for repo (you already have)

Optional but recommended
- Azure Storage Explorer (visual for ADLS)
- Databricks Community (free) OR Azure Databricks (real integration)

---

## 1 — Prepare local SQL Server (mock data)
1. Open SSMS or Azure Data Studio and run the DDL in `sql/sample_ddl.sql` to create `mock_his` db, masters, `patient_registrations`, and `pipeline_runs`.
   - In SSMS: File → New → Query → paste file contents → Execute.
2. Load sample data:
   - Option A (quick manual): In SSMS use Import Data wizard to import `data/sample_registrations.csv` into `mock_his.dbo.patient_registrations`.
   - Option B (T-SQL BULK INSERT, ensure file accessible to SQL Server service):
     ```sql
     BULK INSERT mock_his.dbo.patient_registrations
     FROM 'C:\path\to\data\sample_registrations.csv'
     WITH (
       FIRSTROW = 2,
       FIELDTERMINATOR = ',',
       ROWTERMINATOR = '\n',
       FORMAT = 'CSV'
     );
     ```
   - Option C: Use INSERT statements for a few rows.

Confirm that rows exist:
```sql
USE mock_his;
SELECT TOP 10 * FROM dbo.patient_registrations ORDER BY modified_at DESC;
```

---

## 2 — Create minimal Azure resources (low cost)
You can run the convenience scripts in `azure/` or create resources via Portal.

A. Install Azure CLI (if not already):
- Windows: follow https://learn.microsoft.com/cli/azure/install-azure-cli-windows
- Login: `az login`

B. Run create resources script (use Git Bash, WSL, or PowerShell with Bash support)
- Make script executable (in Bash): `chmod +x azure/create_resources.sh`
- Run example:
  ```bash
  ./azure/create_resources.sh my-rg eastus mystorageacct123
  ```
  Replace:
  - `my-rg` with your resource group name
  - `eastus` with preferred region
  - `mystorageacct123` with a globally unique storage account name (lowercase)

What the script creates:
- Resource group `my-rg`
- Storage account `mystorageacct123` with hierarchical namespace (ADLS Gen2)
- Containers: `incoming`, `processed`, `archive`, `control`

If you prefer Portal:
- Create Resource Group → Storage Account (General purpose v2) → Enable Hierarchical namespace → Create containers in Storage Explorer.

---

## 3 — Create a Service Principal (SP) and assign blob role
Use the helper script or run manually.

A. Using helper script:
```bash
chmod +x azure/create_sp_and_role.sh
./azure/create_sp_and_role.sh my-rg mystorageacct123 sp-health-data
```
The command prints JSON with `clientId`, `clientSecret`, `tenantId` — save this JSON securely (or place into Azure Key Vault).

B. Manual (CLI):
```bash
SUB_ID=$(az account show --query id -o tsv)
az ad sp create-for-rbac --name sp-health-data \
  --role "Storage Blob Data Contributor" \
  --scopes /subscriptions/$SUB_ID/resourceGroups/my-rg/providers/Microsoft.Storage/storageAccounts/mystorageacct123 \
  --sdk-auth
```

You’ll use the SP credentials when creating the ADLS linked service in ADF and/or configuring Databricks to access ADLS.

---

## 4 — Create Azure Data Factory and install Self‑Hosted Integration Runtime (SH IR)
A. Create Data Factory
- Portal → Create resource → Data Factory → Fill name & RG → Git configuration optional → Create.

B. Install SH IR (on your laptop) to let ADF access local SQL Server
1. In Azure Portal → Data Factory → Manage (left) → Integration Runtimes → + New → Self‑Hosted.
2. Follow wizard; it will generate a key and download an installer (Windows).
3. Run the installer on your laptop. When prompted, paste the auto-generated authentication key to register the node.
4. Confirm in ADF that the SH IR shows state: Online.

Notes:
- SH IR initiates outbound HTTPS (443) to Azure — no inbound firewall changes needed.
- If your laptop sleeps or is restarted often, run pipelines manually or run SH IR on a small always‑on VM.

---

## 5 — Provision Databricks (two options)
Option A — Databricks Community (free)
- Good for learning notebooks and PySpark.
- Limitations: integrating with ADLS via SP is harder; you may upload files to DBFS manually.

Option B — Azure Databricks workspace (recommended for integration)
- Portal → Create resource → Azure Databricks → Workspace → Create.
- Use Databricks clusters with auto-termination and small worker types to control costs.

Configuring Databricks to access ADLS Gen2 (when using Azure Databricks):
- Use the SP credentials and set up a scoped secret in Databricks or mount via abfss with Spark config.
- Follow Databricks docs: Configure access to Azure Data Lake Storage Gen2 using service principal: https://learn.microsoft.com/azure/databricks/data/data-sources/azure/azure-datalake-gen2

---

## 6 — Create Linked Services & Datasets in ADF
In ADF (Author tab):

1. Linked Service: On‑prem SQL Server
   - Type: Azure SQL Database / SQL Server (choose SQL Server).
   - For Integration Runtime: select your Self‑Hosted IR.
   - Server name: your local machine name or IP (accessible from SH IR host).
   - Auth: SQL Authentication (create a read‑only SQL user for extraction).

2. Linked Service: ADLS Gen2
   - Type: Azure Data Lake Storage Gen2 (Azure Data Lake Storage Gen2).
   - Auth method: Service principal (use clientId/clientSecret/tenantId from SP). Prefer Key Vault to store secret.

3. Linked Service: Azure Databricks
   - Use Workspace URL and personal access token (create token in Databricks User Settings).

4. Create datasets:
   - Source dataset: SQL (table/query) — you can define dataset type `AzureSqlTable` or `AzureSqlQuery`.
   - Sink dataset: AzureBlobFS / ADLS pointing to `incoming/registrations/run=<run_id>` path (CSV).

Important: After you import the pipeline JSON, edit the pipeline to reference the exact Linked Service and Dataset names you created.

---

## 7 — Import and configure the ADF pipeline
1. In ADF Author → Pipelines → Import from JSON → select `adf/pipeline_registrations.json`.
2. Edit the pipeline in the UI:
   - Replace `LS_OnPrem_SQL_SHIR`, `LS_AzureDatabricks`, `LS_AzureSQL_Control` and dataset names with the names you created.
   - Replace `<STORAGE>` placeholders in the Databricks notebook activity `baseParameters.run_path` and `processed_base` with your storage account name (or use parameterized dataset).
   - For the Copy activity `sqlReaderQuery`, set it as dynamic content if needed. Example expression to set `start_date` and `end_date` using pipeline variables:
     - Use the pipeline's Set Variable activity already provided. In Copy activity source, choose `Query` and paste:
       ```
       SELECT * FROM dbo.patient_registrations
       WHERE modified_at >= '@{variables('start_date')}'
         AND modified_at < '@{variables('end_date')}'
       ```
     - If paste doesn't accept variables directly, use dataset parameterization or build the query in a Lookup activity and pass to the Copy activity.

3. Save the pipeline.

---

## 8 — Deploy Databricks notebook & test locally
A. Upload notebook:
- In Databricks workspace → Repos or Workspace → Create → File → Paste `notebooks/ingest_and_merge_registrations.py` content.
- Create a Job (optional) that runs the notebook with parameters:
  - `run_path` (e.g., `abfss://incoming@mystorageacct123.dfs.core.windows.net/registrations/run=run_20260104/`)
  - `processed_base` (e.g., `abfss://processed@mystorageacct123.dfs.core.windows.net/`)
  - `run_id` (string)

B. Test notebook manually:
- Upload the sample CSV to the incoming path:
  - Use Azure Storage Explorer to upload `data/sample_registrations.csv` to `incoming/registrations/run=test_run/`.
  - OR use `az storage blob upload` (example):
    ```bash
    az storage blob upload --account-name mystorageacct123 --container-name incoming --name registrations/run=test_run/sample_registrations.csv --file data/sample_registrations.csv
    ```
- Run the notebook in Databricks (or run job) with `run_path` pointing to the uploaded file.
- Confirm outputs in `processed` container (Delta files under `staging/patient_registrations/` and `reports/fact_registrations/`).

---

## 9 — Wire ADF pipeline to run end‑to‑end
1. In your imported pipeline, ensure the Databricks Notebook activity points to the notebook path and passes correct parameters (`run_path`, `processed_base`, `run_id`).
2. Manually trigger the pipeline with default parameters, or schedule a trigger.
3. Monitor pipeline runs in ADF Monitor tab. If failures occur, click the activity to view logs. For Databricks failure logs, open the Databricks run.

Validation checklist (after successful run)
- Raw file moved from `incoming` to `archive/<date>/` (or archived per pipeline).
- Delta files in processed container: `staging/patient_registrations/` and `reports/fact_registrations/`.
- `control/runs/` contains run metadata (parquet) OR Azure SQL `pipeline_runs` updated (if you implemented stored proc).
- Re-run same `run_id` or same window — ensure no duplicate rows in Delta (idempotency via merge).

---

## 10 — Testing scenarios to validate behavior
- Idempotency: Run same pipeline twice — no duplicate `registration_id` in Delta.
- Updates: Update a row in local SQL with a later `modified_at` and re-run — Delta row should be updated.
- Late data: Insert a backdated modified row that falls into overlapping 7‑day window — verify it’s captured and merged.
- Error handling: Force a failure (e.g., bad schema), inspect ADF activity logs and Databricks job logs.

---

## 11 — Monitoring, alerts & housekeeping
- Enable ADF diagnostic logs to Log Analytics to create alerts on pipeline failures.
- In Databricks, configure job failure alerts to email or webhooks.
- Implement retention: automatically expire/archive raw files older than X days; compact Delta files periodically (Databricks `OPTIMIZE` if using Databricks runtime).
- Clean up unused resources: stop Databricks clusters, delete test Resource Group when finished:
  ```bash
  az group delete -n my-rg --yes --no-wait
  ```

---

## 12 — Cost‑saving tips (personal account)
- Use Databricks Community Edition for notebook dev (free). For integration testing use a tiny Azure Databricks cluster and set auto-termination to 5–10 minutes.
- Use serverless Synapse (if performing small queries) instead of dedicated pools.
- Use the smallest SQL tier if you need Azure SQL for control table, or use parquet/delta (cheaper).
- Delete or stop compute resources when idle.

---

## 13 — Troubleshooting notes (common issues)
- SH IR shows Offline: re-run the installer and verify the auth key; ensure machine has outbound 443 access.
- ADF Copy times out: check network bandwidth and SH IR machine CPU; consider splitting extract (predicate pushdown) or using staging in sink.
- Databricks cannot access ADLS: verify SP role assignment, ensure correct configs or mount using dbutils with secrets. Use Databricks docs for ADLS Gen2 + SP.
- Schema drift: make casts explicit in notebook; use `inferSchema=false` and a pre-defined schema for robust production pipelines.

---

## 14 — Next recommended enhancements (later)
- Replace overlapping 7‑day window with CDC (SQL Server CDC + eventing) for efficient incremental capture.
- Implement SCD Type 2 for patient dimension using Delta merges and effective dates.
- Add infra as code (ARM/Bicep/Terraform) for consistent provisioning.
- Add automated tests and a small GitHub Actions workflow to validate pipeline JSON and check notebook syntax.

---

## 15 — Should I update repo files for you?
I can:
- Replace `<STORAGE>` placeholders in the files with your actual storage account name and push updates.
- Add a small Python script to generate synthetic registrations and load them into your local SQL Server.
- Expand the repo README in the repository directly (I can commit the updated README if you want).

If you want me to update and commit the README and/or replace placeholders, reply with:
1. Your Azure storage account name (exact)
2. Whether you use Azure Databricks or Databricks Community
3. Where you want run metadata stored: Azure SQL or Delta/parquet

I'll then commit the updated README or fill the placeholders and push the changes for you.
