storage_account = "stregistrationsde001"

configs = {
  "fs.azure.account.auth.type": "OAuth",
  "fs.azure.account.oauth.provider.type": "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
  "fs.azure.account.oauth2.client.id": "<CLIENT_ID>",
  "fs.azure.account.oauth2.client.secret": "<CLIENT_SECRET>",
  "fs.azure.account.oauth2.client.endpoint": "https://login.microsoftonline.com/TENANT_ID/oauth2/token"
}

for k, v in configs.items():
    spark.conf.set(f"{k}.{storage_account}.dfs.core.windows.net", v)


display(
    dbutils.fs.ls("abfss://incoming@stregistrationsde001.dfs.core.windows.net/")
)