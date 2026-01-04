#!/bin/bash
# Usage: ./create_sp_and_role.sh <rg> <storageAccount> <spName>
RG=${1:-rg-health-data}
STORAGE=${2:-<STORAGE_ACCOUNT_NAME>}  # replace with your storage account name
SPNAME=${3:-sp-health-data}

SUB_ID=$(az account show --query id -o tsv)

echo "Creating service principal $SPNAME with Storage Blob Data Contributor on storage account $STORAGE..."
az ad sp create-for-rbac --name $SPNAME \
  --role "Storage Blob Data Contributor" \
  --scopes /subscriptions/$SUB_ID/resourceGroups/$RG/providers/Microsoft.Storage/storageAccounts/$STORAGE \
  --sdk-auth
# Save the printed JSON securely (contains clientId/clientSecret/tenant)
