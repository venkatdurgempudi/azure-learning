# ============================================================
# Azure Databricks – Daily Incremental Registrations Load
# ============================================================

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import *
from delta.tables import DeltaTable

# ------------------------------------------------------------
# PARAMETERS
# ------------------------------------------------------------

RUN_DATE = "2026-01-05"
STORAGE_ACCOUNT = "stregistrationsde001"

# ------------------------------------------------------------
# ADLS OAUTH CONFIGURATION
# ------------------------------------------------------------

# Clear any old key-based config
try:
    spark.conf.unset(
        f"fs.azure.account.key.{STORAGE_ACCOUNT}.dfs.core.windows.net"
    )
except:
    pass



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
# PATHS
# ------------------------------------------------------------

INCOMING_BASE = f"abfss://incoming@{STORAGE_ACCOUNT}.dfs.core.windows.net"
PROCESSED_BASE = f"abfss://processed@{STORAGE_ACCOUNT}.dfs.core.windows.net"

REGISTRATIONS_PATH = (
    f"{INCOMING_BASE}/registrations/run_date={RUN_DATE}/"
)

FACT_PATH = (
    f"{PROCESSED_BASE}/reports/fact_registrations"
)

# ------------------------------------------------------------
# EXPLICIT SCHEMA (MATCHES CSV)
# ------------------------------------------------------------

daily_schema = StructType([
    StructField("registration_id", StringType(), True),
    StructField("patient_id", StringType(), True),
    StructField("reg_dt", StringType(), True),
    StructField("unit_id", StringType(), True),
    StructField("gender_id", StringType(), True),
    StructField("source", StringType(), True),
    StructField("created_at", StringType(), True),
    StructField("modified_at", StringType(), True)
])

# ------------------------------------------------------------
# READ DAILY CSV
# ------------------------------------------------------------

raw_df = (
    spark.read
    .schema(daily_schema)
    .option("header", True)
    .csv(REGISTRATIONS_PATH)
)

# ------------------------------------------------------------
# PARSE TIMESTAMPS (CORRECT FORMAT)
# ------------------------------------------------------------

parsed_df = (
    raw_df
    .withColumn(
        "modified_at",
        F.to_timestamp("modified_at", "yyyy-MM-dd HH:mm:ss")
    )
    .withColumn(
        "reg_dt",
        F.to_timestamp("reg_dt", "yyyy-MM-dd HH:mm:ss")
    )
    .withColumn(
        "created_at",
        F.to_timestamp("created_at", "yyyy-MM-dd HH:mm:ss")
    )
)

# Reject bad rows safely
bad_rows = parsed_df.filter(F.col("modified_at").isNull()).count()
print(f"Rejected rows due to bad timestamp: {bad_rows}")

parsed_df = parsed_df.filter(F.col("modified_at").isNotNull())

# ------------------------------------------------------------
# DEDUPLICATION (LATEST PER REGISTRATION)
# ------------------------------------------------------------

window_spec = (
    Window.partitionBy("registration_id")
          .orderBy(F.col("modified_at").desc())
)

dedup_df = (
    parsed_df
    .withColumn("rn", F.row_number().over(window_spec))
    .filter(F.col("rn") == 1)
    .drop("rn")
)

# ------------------------------------------------------------
# ENRICHMENT / METADATA
# ------------------------------------------------------------

enriched_df = (
    dedup_df
    .withColumn("load_type", F.lit("DAILY"))
    .withColumn("ingested_at", F.current_timestamp())
)

# ------------------------------------------------------------
# MERGE INTO DELTA FACT TABLE (EXPLICIT & SAFE)
# ------------------------------------------------------------

target = DeltaTable.forPath(spark, FACT_PATH)

(
    target.alias("t")
    .merge(
        enriched_df.alias("s"),
        """
        t.registration_id = s.registration_id
        AND t.patient_id = s.patient_id
        AND t.unit_id = s.unit_id
        """
    )
    .whenMatchedUpdate(set={
        "gender_id": "s.gender_id",
        "source": "s.source",
        "reg_dt": "s.reg_dt",
        "created_at": "s.created_at",
        "modified_at": "s.modified_at",
        "load_type": "s.load_type",
        "ingested_at": "s.ingested_at"
    })
    .whenNotMatchedInsert(values={
        "registration_id": "s.registration_id",
        "patient_id": "s.patient_id",
        "gender_id": "s.gender_id",
        "unit_id": "s.unit_id",
        "source": "s.source",
        "reg_dt": "s.reg_dt",
        "created_at": "s.created_at",
        "modified_at": "s.modified_at",
        "load_type": "s.load_type",
        "ingested_at": "s.ingested_at"
    })
    .execute()
)

# ------------------------------------------------------------
# FINAL VALIDATION
# ------------------------------------------------------------

spark.read.format("delta") \
    .load(FACT_PATH) \
    .groupBy("load_type") \
    .count() \
    .show()

print(f"✅ Daily load completed successfully for {RUN_DATE}")


spark.read.format("delta") \
  .load("abfss://processed@stregistrationsde001.dfs.core.windows.net/reports/fact_registrations") \
  .filter("registration_id = '1027'") \
  .show(truncate=False)
