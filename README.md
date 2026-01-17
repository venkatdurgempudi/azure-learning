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

azure-learning/
- projects/
  - project-0-sandbox/         # Learning experiments and prototypes
  - project-1-onprem-to-azure/ # End-to-end production-style project
- learning/                    # Conceptual notes and references
- infra/                       # Shared infrastructure scripts (future use)
- shared/                      # Reusable utilities and templates (future use)
- README.md                    # This file

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
