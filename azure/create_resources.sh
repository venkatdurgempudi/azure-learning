#!/bin/bash
# Usage: ./create_resources.sh <rg> <location> <storageAccount>
RG=${1:-rg-health-data}
LOC=${2:-eastus}
STORAGE=${3:-<STORAGE_ACCOUNT_NAME>}  # replace with your storage account name

echo "Creating resource group $RG in $LOC..."
az group create -n $RG -l $LOC

echo "Creating storage account $STORAGE with hierarchical-namespace (ADLS Gen2)..."
az storage account create \
  --name $STORAGE \
  --resource-group $RG \
  --sku Standard_LRS \
  --kind StorageV2 \
  --hierarchical-namespace true

echo "Creating containers: incoming, processed, archive, control..."
az storage container create -n incoming --account-name $STORAGE
az storage container create -n processed --account-name $STORAGE
az storage container create -n archive --account-name $STORAGE
az storage container create -n control --account-name $STORAGE

echo "Storage account DFS endpoint:"
az storage account show -n $STORAGE -g $RG --query "primaryEndpoints.dfs" -o tsv
