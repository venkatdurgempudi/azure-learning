# Azure Data Engineering – Learning & Projects

## Overview

This repository is a **mono-repo** containing multiple Azure data engineering projects
along with supporting learning material.

It is designed to demonstrate:
- Real-world Azure data engineering architecture
- Clean project organization
- Clear separation between learning and production-style work

---

## Repository Structure

```text
├── gen-tree.sh
├── infra
│   ├── .gitkeep
├── learning
│   ├── README.md
│   ├── resources.md
├── LICENSE
├── projects
│   ├── project-0-sandbox
│   │   ├── adf
│   │   │   ├── pipeline_registrations.json
│   │   ├── data
│   │   │   ├── masters
│   │   │   │   ├── gender_master.csv
│   │   │   │   ├── unit_master.csv
│   │   │   ├── registrations
│   │   │   │   ├── run_date=2026-01-05
│   │   │   │   │   ├── registrations.csv
│   │   │   │   ├── run_date=2026-01-11
│   │   │   │   │   ├── registrations.csv
│   │   │   │   ├── run=manual_001
│   │   │   │   │   ├── registrations.csv
│   │   ├── databricks
│   │   │   ├── notebooks
│   │   │   │   ├── 00_adls_oauth_setup.py
│   │   │   │   ├── 01_ingest_registrations_history.py
│   │   │   │   ├── gold-silver-schema-creation.ipynb
│   │   │   │   ├── ingest_and_merge_registrations.py
│   │   ├── infra
│   │   │   ├── azure-cli
│   │   │   │   ├── create_resources.sh
│   │   │   │   ├── create_sp_and_role.sh
│   │   ├── notes
│   │   │   ├── .gitkeep
│   │   ├── README.md
│   │   ├── secrets
│   │   │   ├── README.md
│   │   ├── sql
│   │   │   ├── sample_ddl.sql
│   │   │   ├── usp_insert_run_record.sql
│   │   ├── tools
│   │   │   ├── generate_mock_registrations.py
│   │   │   ├── sync_to_incoming.ps1
│   ├── project-1-onprem-to-azure
│   │   ├── adf
│   │   │   ├── datasets
│   │   │   │   ├── .gitkeep
│   │   │   ├── linked-services
│   │   │   │   ├── .gitkeep
│   │   │   ├── pipelines
│   │   │   │   ├── .gitkeep
│   │   ├── architecture
│   │   │   ├── .gitkeep
│   │   ├── databricks
│   │   │   ├── bronze
│   │   │   │   ├── .gitkeep
│   │   │   ├── gold
│   │   │   │   ├── .gitkeep
│   │   │   ├── silver
│   │   │   │   ├── .gitkeep
│   │   ├── docs
│   │   │   ├── .gitkeep
│   │   ├── infra
│   │   │   ├── .gitkeep
│   │   ├── powerbi
│   │   │   ├── .gitkeep
│   │   ├── README.md
│   │   ├── synapse
│   │   │   ├── serverless-sql
│   │   │   │   ├── .gitkeep
│   │   ├── tools
│   │   │   ├── .gitkeep
├── README.md
├── shared
│   ├── .gitkeep
```

---

## Projects

### Project 0 – Sandbox
**Location:** projects/project-0-sandbox

- Experimental notebooks
- Prototype pipelines
- Small sample datasets
- Learning-focused work

Use this project to understand concepts and test ideas.

---

### Project 1 – On-Prem SQL to Azure Analytics
**Location:** projects/project-1-onprem-to-azure

A complete Azure data engineering solution:

On-Prem SQL Server  
→ Azure Data Factory (SHIR)  
→ ADLS Gen2 (Bronze)  
→ Azure Databricks (Silver / Gold)  
→ Azure Synapse Serverless SQL  
→ Power BI  

This project follows **enterprise best practices** and is suitable for
demonstration and interviews.

---

## How to Navigate This Repo

- Start with **Project 1** for a full end-to-end solution
- Use **Project 0** to explore experiments and learning history
- Refer to the `learning/` folder for conceptual understanding

---

## Security & Data Handling

- No secrets or credentials are stored in GitHub
- Production data is never committed
- `.gitignore` enforces safe version control practices

---

## Disclaimer

All projects are for learning and demonstration purposes only.
