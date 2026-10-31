
import os
import sys
import time
import csv
import hashlib
from pathlib import Path

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    lower,
    trim,
    regexp_replace,
    sha2,
    count
)

INPUT_DIR = "data/processed/ingested_parquet"
OUTPUT_DIR = "data/processed/deduplicated_parquet"

spark = (
    SparkSession.builder
    .appName("CommonCrawlDeduplication")
    .master("local[2]")
    .config("spark.pyspark.python", sys.executable)
    .config("spark.pyspark.driver.python", sys.executable)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("Starting deduplication...")

    start_time = time.perf_counter()

    df = spark.read.parquet(INPUT_DIR)

    initial_count = df.count()

    # Normalize text for duplicate comparison
    normalized_df = df.withColumn(
        "normalized_text",
        lower(
            trim(
                regexp_replace(
                    col("text"),
                    r"\s+",
                    " "
                )
            )
        )
    )

    # Generate SHA-256 hashes
    hashed_df = normalized_df.withColumn(
        "content_hash",
        sha2(col("normalized_text"), 256)
    )

    # Count duplicate groups
    duplicate_groups = (
        hashed_df.groupBy("content_hash")
        .agg(count("*").alias("copies"))
        .filter(col("copies") > 1)
        .count()
    )

    # Retain one document per content hash
    deduplicated_df = (
        hashed_df
        .dropDuplicates(["content_hash"])
        .drop("normalized_text")
    )

    final_count = deduplicated_df.count()

    duplicates_removed = initial_count - final_count

    removal_percentage = (
        duplicates_removed / initial_count * 100
        if initial_count else 0
    )

    execution_time = time.perf_counter() - start_time

    deduplicated_df.write.mode("overwrite").parquet(
        OUTPUT_DIR
    )

    print("\n========== DEDUPLICATION RESULTS ==========")
    print("Initial documents:", initial_count)
    print("Duplicate groups:", duplicate_groups)
    print("Duplicates removed:", duplicates_removed)
    print("Unique documents:", final_count)
    print(f"Removal percentage: {removal_percentage:.2f}%")
    print(f"Execution time: {execution_time:.4f} seconds")
    print("Output:", OUTPUT_DIR)

    # Save metrics
    Path("results").mkdir(exist_ok=True)

    with open(
        "results/deduplication_metrics.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "initial_documents",
            "duplicate_groups",
            "duplicates_removed",
            "unique_documents",
            "removal_percentage",
            "execution_time_seconds"
        ])

        writer.writerow([
            initial_count,
            duplicate_groups,
            duplicates_removed,
            final_count,
            round(removal_percentage, 2),
            round(execution_time, 4)
        ])

finally:
    spark.stop()

print("\nDEDUPLICATION COMPLETED SUCCESSFULLY!")
