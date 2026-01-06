# ============================================================
# Azure Databricks – Historical Bootstrap Load
# ============================================================

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from delta.tables import DeltaTable

# ------------------------------------------------------------
# ADLS OAUTH CONFIGURATION (REQUIRED)
# ------------------------------------------------------------

STORAGE_ACCOUNT = "stregistrationsde001"

# Safety: remove any old key-based config
try:
    spark.conf.unset(
        f"fs.azure.account.key.{STORAGE_ACCOUNT}.dfs.core.windows.net"
    )
except:
    pass

# 🔴 REPLACE THESE 3 VALUES

CLIENT_ID = "<CLIENT_ID>"
CLIENT_SECRET = "<CLIENT_SECRET>"
TENANT_ID = "<TENANT_ID>"


configs = {
    "fs.azure.account.auth.type": "OAuth",
    "fs.azure.account.oauth.provider.type":
        "org.apache.hadoop.fs.azurebfs.oauth2.ClientCredsTokenProvider",
    "fs.azure.account.oauth2.client.id": CLIENT_ID,
    "fs.azure.account.oauth2.client.secret": CLIENT_SECRET,
    "fs.azure.account.oauth2.client.endpoint":
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
}

for k, v in configs.items():
    spark.conf.set(
        f"{k}.{STORAGE_ACCOUNT}.dfs.core.windows.net", v
    )

# ------------------------------------------------------------
# PATH DEFINITIONS
# ------------------------------------------------------------

INCOMING_BASE = f"abfss://incoming@{STORAGE_ACCOUNT}.dfs.core.windows.net"
PROCESSED_BASE = f"abfss://processed@{STORAGE_ACCOUNT}.dfs.core.windows.net"

# Historical data (one-time manual load)
REGISTRATIONS_PATH = (
    f"{INCOMING_BASE}/registrations/run=manual_001/"
)

# Master data
GENDER_MASTER_PATH = (
    f"{INCOMING_BASE}/masters/gender_master.csv"
)

UNIT_MASTER_PATH = (
    f"{INCOMING_BASE}/masters/unit_master.csv"
)

# Delta target
FACT_PATH = (
    f"{PROCESSED_BASE}/reports/fact_registrations"
)

# ------------------------------------------------------------
# READ HISTORY DATA
# ------------------------------------------------------------

registrations_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(REGISTRATIONS_PATH)
)

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
# BASIC VALIDATION
# ------------------------------------------------------------

required_cols = ["registration_id", "modified_at"]
missing_cols = [c for c in required_cols if c not in registrations_df.columns]

if missing_cols:
    raise Exception(f"Missing required columns: {missing_cols}")

# ------------------------------------------------------------
# DEDUPLICATION (LATEST RECORD PER REGISTRATION)
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
# ENRICHMENT
# ------------------------------------------------------------

enriched_df = (
    dedup_df
    .join(gender_df, "gender_id", "left")
    .join(unit_df, "unit_id", "left")
    .withColumn("load_type", F.lit("HISTORY"))
    .withColumn("ingested_at", F.current_timestamp())
)

# ------------------------------------------------------------
# MERGE INTO DELTA FACT TABLE (IDEMPOTENT)
# ------------------------------------------------------------

if DeltaTable.isDeltaTable(spark, FACT_PATH):
    target = DeltaTable.forPath(spark, FACT_PATH)

    (
        target.alias("t")
        .merge(
            enriched_df.alias("s"),
            "t.registration_id = s.registration_id"
        )
        .whenMatchedUpdateAll()
        .whenNotMatchedInsertAll()
        .execute()
    )
else:
    (
        enriched_df
        .write
        .format("delta")
        .mode("overwrite")
        .save(FACT_PATH)
    )

# ------------------------------------------------------------
# FINAL VALIDATION
# ------------------------------------------------------------

final_count = (
    spark.read
    .format("delta")
    .load(FACT_PATH)
    .count()
)

print("✅ Historical bootstrap completed successfully")
print(f"📊 Total records in fact_registrations: {final_count}")



spark.read.format("delta") \
  .load("abfss://processed@stregistrationsde001.dfs.core.windows.net/reports/fact_registrations") \
  .groupBy("load_type") \
  .count() \
  .show()
