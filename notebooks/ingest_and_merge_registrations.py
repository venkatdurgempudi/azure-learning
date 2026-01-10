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
# SECURE ADLS AUTH (Databricks Secret Scope)
# ------------------------------------------------------------

CLIENT_ID = dbutils.secrets.get("adls-secrets", "client-id")
CLIENT_SECRET = dbutils.secrets.get("adls-secrets", "client-secret")
TENANT_ID = dbutils.secrets.get("adls-secrets", "tenant-id")

# Clear any accidental key-based config
try:
    spark.conf.unset(
        f"fs.azure.account.key.{STORAGE_ACCOUNT}.dfs.core.windows.net"
    )
except:
    pass

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
# PATHS
# ------------------------------------------------------------

INCOMING_BASE = f"abfss://incoming@{STORAGE_ACCOUNT}.dfs.core.windows.net"
PROCESSED_BASE = f"abfss://processed@{STORAGE_ACCOUNT}.dfs.core.windows.net"

REGISTRATIONS_PATH = (
    f"{INCOMING_BASE}/registrations/run={RUN_DATE}/"
)

FACT_PATH = (
    f"{PROCESSED_BASE}/reports/fact_registrations"
)

# ------------------------------------------------------------
# EXPLICIT SCHEMA (AS STRING FIRST)
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
# SAFE TIMESTAMP PARSING (MULTI FORMAT)
# ------------------------------------------------------------

def parse_ts(col):
    return F.coalesce(
        F.to_timestamp(col, "yyyy-MM-dd HH:mm:ss"),
        F.to_timestamp(col, "dd-MM-yy HH:mm"),
        F.to_timestamp(col, "dd-MM-yyyy HH:mm:ss")
    )

parsed_df = (
    raw_df
    .withColumn("reg_dt", parse_ts("reg_dt"))
    .withColumn("created_at", parse_ts("created_at"))
    .withColumn("modified_at", parse_ts("modified_at"))
)

# ------------------------------------------------------------
# REJECT BAD ROWS (DO NOT FAIL PIPELINE)
# ------------------------------------------------------------

rejected_count = parsed_df.filter(F.col("modified_at").isNull()).count()
print(f"Rejected rows due to bad timestamp: {rejected_count}")

clean_df = parsed_df.filter(F.col("modified_at").isNotNull())

# ------------------------------------------------------------
# DEDUPLICATION (LATEST PER REGISTRATION)
# ------------------------------------------------------------

window_spec = (
    Window
    .partitionBy("registration_id")
    .orderBy(F.col("modified_at").desc())
)

dedup_df = (
    clean_df
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
    .withColumn("run_date", F.lit(RUN_DATE))
    .withColumn("ingested_at", F.current_timestamp())
)

# ------------------------------------------------------------
# MERGE INTO FACT TABLE (CORRECT BUSINESS KEYS)
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
        "run_date": "s.run_date",
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
        "run_date": "s.run_date",
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
    .load(FACT_PATH) \
    .filter("registration_id = '1027'") \
    .show(truncate=False)
