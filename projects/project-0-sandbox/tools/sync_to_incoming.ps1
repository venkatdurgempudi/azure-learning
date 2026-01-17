# ================================
# Sync local data to Azure Blob
# ================================

#$env:AZ_SAS="?<SAS_TOKEN_HERE>"
#echo $env:AZ_SAS

if (-not $env:AZ_SAS) {
    Write-Error "AZ_SAS environment variable is not set."
    exit 1
}

$SourcePath = "D:\Projects\azure-learning\data"
$Destination = "https://stregistrationsde001.blob.core.windows.net/incoming"

Write-Host "Starting AzCopy sync..."
Write-Host "Source: $SourcePath"
Write-Host "Destination: $Destination"

& "C:\Program Files\AzCopy\azcopy.exe" sync `
    $SourcePath `
    "$Destination$env:AZ_SAS" `
    --recursive

if ($LASTEXITCODE -ne 0) {
    Write-Error "AzCopy failed with exit code $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host "AzCopy sync completed successfully."
