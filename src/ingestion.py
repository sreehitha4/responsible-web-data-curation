
import os
import sys
import time
import csv
from pathlib import Path

# Use the current virtual environment's Python interpreter
os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    IntegerType,
    StringType
)

# Project paths
INPUT_FILE = "data/sample/wet_documents.jsonl"
OUTPUT_DIR = "data/processed/ingested_parquet"
METRICS_DIR = Path("results")

METRICS_DIR.mkdir(parents=True, exist_ok=True)

if not Path(INPUT_FILE).exists():
    raise FileNotFoundError(
        f"Input dataset not found: {INPUT_FILE}"
    )

# Create Spark session
spark = (
    SparkSession.builder
    .appName("CommonCrawlIngestion")
    .master("local[2]")
    .config("spark.pyspark.python", sys.executable)
    .config("spark.pyspark.driver.python", sys.executable)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

# Define an explicit schema
schema = StructType([
    StructField("doc_id", IntegerType(), True),
    StructField("domain", StringType(), True),
    StructField("crawl_date", StringType(), True),
    StructField("text", StringType(), True)
])

try:
    print("Starting Spark ingestion...")

    start_time = time.perf_counter()

    df = (
        spark.read
        .schema(schema)
        .json(INPUT_FILE)
    )

    document_count = df.count()

    ingestion_time = time.perf_counter() - start_time

    print("\nDataset schema:")
    df.printSchema()

    print("\nSample documents:")
    df.select(
        "doc_id", "domain", "crawl_date"
    ).show(5, truncate=False)

    print("Total documents:", document_count)
    print(f"Ingestion time: {ingestion_time:.4f} seconds")

    # Save the ingested dataset in Parquet format
    print("\nWriting Parquet output...")

    df.write.mode("overwrite").parquet(OUTPUT_DIR)

    print("Parquet output saved:", OUTPUT_DIR)

    # Save ingestion metrics
    metrics_file = METRICS_DIR / "ingestion_metrics.csv"

    with metrics_file.open(
        "w", newline="", encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "documents",
            "ingestion_time_seconds",
            "documents_per_second"
        ])

        throughput = (
            document_count / ingestion_time
            if ingestion_time > 0 else 0
        )

        writer.writerow([
            document_count,
            round(ingestion_time, 4),
            round(throughput, 2)
        ])

    print("\nIngestion metrics saved:", metrics_file)
    print(f"Throughput: {throughput:.2f} documents/second")

finally:
    spark.stop()

print("\nSPARK INGESTION COMPLETED SUCCESSFULLY!")
