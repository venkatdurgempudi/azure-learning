# ============================================================
# Azure Databricks – Daily Incremental Registrations Load
# (ENRICHED – FINAL, STABLE VERSION)
# ============================================================

from pyspark.sql import functions as F
from pyspark.sql.window import Window
from pyspark.sql.types import *
from delta.tables import DeltaTable
from datetime import datetime

# ------------------------------------------------------------
# 0. SPARK SAFETY SETTINGS (CRITICAL)
# ------------------------------------------------------------

spark.conf.set("spark.sql.sources.partitionDiscovery.enabled", "false")
spark.conf.set("spark.sql.sources.partitionColumnTypeInference.enabled", "false")
spark.catalog.clearCache()

# ------------------------------------------------------------
# 1. PARAMETERS
# ------------------------------------------------------------

def get_run_date():
    try:
        return dbutils.widgets.get("run_date")
    except:
        return datetime.utcnow().strftime("%Y-%m-%d")

RUN_DATE = get_run_date()

STORAGE_ACCOUNT = "stregistrationsde001"

INCOMING_BASE  = f"abfss://incoming@{STORAGE_ACCOUNT}.dfs.core.windows.net"
PROCESSED_BASE = f"abfss://processed@{STORAGE_ACCOUNT}.dfs.core.windows.net"

REGISTRATIONS_PATH = f"{INCOMING_BASE}/registrations/run_date={RUN_DATE}"
GENDER_MASTER_PATH = f"{INCOMING_BASE}/masters/gender_master.csv"
UNIT_MASTER_PATH   = f"{INCOMING_BASE}/masters/unit_master.csv"

FACT_PATH = f"{PROCESSED_BASE}/reports/fact_registrations"

# ------------------------------------------------------------
# 2. EXPLICIT SCHEMA (READ AS STRING FIRST)
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
# 3. READ DAILY DATA (FLAT, NO PARTITIONS)
# ------------------------------------------------------------

raw_df = (
    spark.read
    .schema(daily_schema)
    .option("header", True)
    .option("recursiveFileLookup", "true")
    .csv(REGISTRATIONS_PATH)
)

# Defensive cleanup (in case Spark injects columns)
cols_to_drop = [c for c in ["run", "run_date"] if c in raw_df.columns]
if cols_to_drop:
    raw_df = raw_df.drop(*cols_to_drop)

# ------------------------------------------------------------
# 4. SAFE TIMESTAMP PARSING
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
# 5. FILTER BAD RECORDS (NON-BLOCKING)
# ------------------------------------------------------------

bad_count = parsed_df.filter(F.col("modified_at").isNull()).count()
print(f"Rejected rows due to bad timestamp: {bad_count}")

clean_df = parsed_df.filter(F.col("modified_at").isNotNull())

# ------------------------------------------------------------
# 6. DEDUPLICATION (LATEST PER REGISTRATION)
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
# 7. READ MASTER DATA
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
# 8. ENRICH DAILY DATA (OPTION 1 – REQUIRED)
# ------------------------------------------------------------

enriched_df = (
    dedup_df
    .join(gender_df, "gender_id", "left")
    .join(unit_df, "unit_id", "left")
    .withColumn("load_type", F.lit("DAILY"))
    .withColumn("run_date", F.lit(RUN_DATE))
    .withColumn("ingested_at", F.current_timestamp())
)

# ------------------------------------------------------------
# 9. MERGE INTO FACT TABLE
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
    .whenMatchedUpdateAll()
    .whenNotMatchedInsertAll()
    .execute()
)

# ------------------------------------------------------------
# 10. FINAL VALIDATION
# ------------------------------------------------------------

spark.read.format("delta") \
    .load(FACT_PATH) \
    .groupBy("load_type") \
    .count() \
    .show()

print(f"✅ Daily incremental load completed successfully for {RUN_DATE}")

