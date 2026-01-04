# Secrets & Credentials Handling (DO NOT STORE SECRETS IN THIS REPO)

This file documents secure ways to store and use credentials for this project. Never commit plaintext passwords, keys, or connection strings into this repository.

Recommended options:

1) Azure Key Vault (recommended)
- Create a Key Vault:
  az keyvault create --name myVault --resource-group my-rg --location eastus
- Add a secret:
  az keyvault secret set --vault-name myVault --name "sp-client-secret" --value "<secret-value>"
- In ADF or Databricks, grant managed identity or service principal access to Key Vault and reference secrets (do NOT paste secrets in notebooks).

2) GitHub Secrets (for GitHub Actions workflows)
- Set a repository secret via UI or gh CLI:
  gh secret set AZURE_CLIENT_SECRET --body "<secret-value>"
- Use secrets in GitHub Actions workflows as `secrets.AZURE_CLIENT_SECRET`.

3) Databricks Secrets (for notebooks)
- Create secret scope backed by Key Vault or Databricks-managed scope:
  databricks secrets create-scope --scope my-scope --scope-backend-type AZURE_KEYVAULT --resource-id <keyvault-resource-id> --dns-name https://myVault.vault.azure.net/
- Access in notebook:
  dbutils.secrets.get("my-scope", "sp-client-secret")

4) Local development (avoid storing in repo)
- Use environment variables or a local `.env` file that is gitignored. Example:
  export AZURE_CLIENT_ID="..."
  export AZURE_CLIENT_SECRET="..."

Security checklist (do this before sharing or publishing):
- Confirm no secrets in git history (use git-secrets or BFG to remove). 
- Add `secrets/**` to .gitignore so no accidental commits.
- Use least-privilege principals and rotate secrets regularly.

If you need, I can add example scripts showing how to fetch secrets from Key Vault and bind them into ADF linked services or Databricks notebooks.
