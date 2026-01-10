# ============================================================
# Azure Databricks – Historical Bootstrap Load (FINAL)
# ============================================================

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# ------------------------------------------------------------
# 0. SPARK SAFETY SETTINGS (CRITICAL)
# ------------------------------------------------------------

# Disable ALL partition discovery/inference
spark.conf.set("spark.sql.sources.partitionDiscovery.enabled", "false")
spark.conf.set("spark.sql.sources.partitionColumnTypeInference.enabled", "false")

spark.catalog.clearCache()

# ------------------------------------------------------------
# 1. ADLS OAUTH CONFIG (SERVICE PRINCIPAL)
# ------------------------------------------------------------

STORAGE_ACCOUNT = "stregistrationsde001"

CLIENT_ID     = dbutils.secrets.get("adls-secrets", "client-id")
CLIENT_SECRET = dbutils.secrets.get("adls-secrets", "client-secret")
TENANT_ID     = dbutils.secrets.get("adls-secrets", "tenant-id")

# Remove key-based auth if present
spark.conf.unset(
    f"fs.azure.account.key.{STORAGE_ACCOUNT}.dfs.core.windows.net"
)

spark.conf.set(
    f"fs.azure.account.auth.type.{STORAGE_ACCOUNT}.dfs.core.windows.net",
    "OAuth"
)
spark.conf.set(
    f"fs.azure.account.oauth.provider.type.{STORAGE_ACCOUNT}.dfs.core.windows.net",
    "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider"
)
spark.conf.set(
    f"fs.azure.account.oauth2.client.id.{STORAGE_ACCOUNT}.dfs.core.windows.net",
    CLIENT_ID
)
spark.conf.set(
    f"fs.azure.account.oauth2.client.secret.{STORAGE_ACCOUNT}.dfs.core.windows.net",
    CLIENT_SECRET
)
spark.conf.set(
    f"fs.azure.account.oauth2.client.endpoint.{STORAGE_ACCOUNT}.dfs.core.windows.net",
    f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
)

# ------------------------------------------------------------
# 2. PATHS
# ------------------------------------------------------------

INCOMING_BASE  = f"abfss://incoming@{STORAGE_ACCOUNT}.dfs.core.windows.net"
PROCESSED_BASE = f"abfss://processed@{STORAGE_ACCOUNT}.dfs.core.windows.net"

REGISTRATIONS_PATH = f"{INCOMING_BASE}/registrations"
GENDER_MASTER_PATH = f"{INCOMING_BASE}/masters/gender_master.csv"
UNIT_MASTER_PATH   = f"{INCOMING_BASE}/masters/unit_master.csv"


FACT_PATH = f"{PROCESSED_BASE}/reports/fact_registrations"

# ------------------------------------------------------------
# 3. READ HISTORICAL REGISTRATIONS (FLAT, NO PARTITIONS)
# ------------------------------------------------------------

registrations_df = (
    spark.read
    .option("header", True)
    .option("recursiveFileLookup", "true")
    .csv(REGISTRATIONS_PATH)
)

# Safely remove partition columns if they exist
cols_to_drop = [c for c in ["run", "run_date"] if c in registrations_df.columns]
if cols_to_drop:
    registrations_df = registrations_df.drop(*cols_to_drop)



# ------------------------------------------------------------
# 4. READ MASTER DATA
# ------------------------------------------------------------

gender_df = (
    spark.read
    .option("header", True)
    .csv(GENDER_MASTER_PATH)
)

unit_df = (
    spark.read
    .option("header", True)
    .csv(UNIT_MASTER_PATH)
)


# ------------------------------------------------------------
# 5. BASIC VALIDATION
# ------------------------------------------------------------

required_cols = ["registration_id", "modified_at"]
missing_cols = [c for c in required_cols if c not in registrations_df.columns]

if missing_cols:
    raise Exception(f"Missing required columns: {missing_cols}")

# ------------------------------------------------------------
# 6. DEDUPLICATION (LATEST RECORD PER REGISTRATION)
# ------------------------------------------------------------

window_spec = (
    Window
    .partitionBy("registration_id")
    .orderBy(F.col("modified_at").desc())
)

dedup_df = (
    registrations_df
    .withColumn("rn", F.row_number().over(window_spec))
    .filter(F.col("rn") == 1)
    .drop("rn")
)

# ------------------------------------------------------------
# 7. ENRICHMENT
# ------------------------------------------------------------

enriched_df = (
    dedup_df
    .join(gender_df, "gender_id", "left")
    .join(unit_df, "unit_id", "left")
    .withColumn("load_type", F.lit("HISTORY"))
    .withColumn("ingested_at", F.current_timestamp())
)

# ------------------------------------------------------------
# 8. BOOTSTRAP WRITE (CLEAN DELTA)
# ------------------------------------------------------------

# Ensure path is clean (safe in DEV/BOOTSTRAP)
dbutils.fs.rm(FACT_PATH, recurse=True)

(
    enriched_df
    .write
    .format("delta")
    .mode("overwrite")
    .save(FACT_PATH)
)

# ------------------------------------------------------------
# 9. FINAL VALIDATION
# ------------------------------------------------------------

DeltaTable.forPath(spark, FACT_PATH).detail().show(truncate=False)

spark.read.format("delta") \
    .load(FACT_PATH) \
    .groupBy("load_type") \
    .count() \
    .show()

print("✅ Historical bootstrap completed successfully")
