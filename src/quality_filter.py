
import os
import sys
import time
import csv
from pathlib import Path

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, length, trim, regexp_replace, split, size,
    when
)

INPUT_DIR = "data/processed/deduplicated_parquet"
OUTPUT_DIR = "data/processed/quality_filtered_parquet"

spark = (
    SparkSession.builder
    .appName("CommonCrawlQualityFiltering")
    .master("local[2]")
    .config("spark.pyspark.python", sys.executable)
    .config("spark.pyspark.driver.python", sys.executable)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")

try:
    print("Starting quality filtering...")

    start_time = time.perf_counter()

    df = spark.read.parquet(INPUT_DIR)

    initial_count = df.count()

    # Rule 1: Remove empty documents
    nonempty = df.filter(
        col("text").isNotNull() &
        (length(trim(col("text"))) > 0)
    )
    empty_removed = initial_count - nonempty.count()

    # Rule 2: Minimum 200 characters
    length_filtered = nonempty.filter(
        length(trim(col("text"))) >= 200
    )
    short_removed = nonempty.count() - length_filtered.count()

    # Rule 3: Minimum 30 words
    word_filtered = length_filtered.filter(
        size(split(trim(col("text")), r"\s+")) >= 30
    )
    word_removed = length_filtered.count() - word_filtered.count()

    # Rule 4: At least 50% alphabetic characters
    measured = word_filtered.withColumn(
        "alpha_ratio",
        length(regexp_replace(col("text"), r"[^A-Za-z]", "")) /
        length(col("text"))
    )

    final_df = (
        measured
        .filter(col("alpha_ratio") >= 0.50)
        .drop("alpha_ratio")
    )

    final_count = final_df.count()

    alpha_removed = word_filtered.count() - final_count

    total_removed = initial_count - final_count

    removal_percentage = (
        total_removed / initial_count * 100
        if initial_count else 0
    )

    execution_time = time.perf_counter() - start_time

    # Save output
    final_df.write.mode("overwrite").parquet(OUTPUT_DIR)

    # Save filter statistics
    Path("results").mkdir(exist_ok=True)

    metrics = [
        ["initial_documents", initial_count],
        ["empty_documents_removed", empty_removed],
        ["short_documents_removed", short_removed],
        ["low_word_count_removed", word_removed],
        ["low_alphabetic_ratio_removed", alpha_removed],
        ["final_documents", final_count],
        ["total_removed", total_removed],
        ["removal_percentage", round(removal_percentage, 2)],
        ["execution_time_seconds", round(execution_time, 4)]
    ]

    with open(
        "results/quality_filter_metrics.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        writer.writerows(metrics)

    print("\n========== QUALITY FILTER RESULTS ==========")
    print("Initial documents:", initial_count)
    print("Empty documents removed:", empty_removed)
    print("Short documents removed:", short_removed)
    print("Low word-count documents removed:", word_removed)
    print("Low alphabetic-ratio documents removed:", alpha_removed)
    print("Final documents:", final_count)
    print("Total removed:", total_removed)
    print(f"Removal percentage: {removal_percentage:.2f}%")
    print(f"Execution time: {execution_time:.4f} seconds")
    print("Output:", OUTPUT_DIR)
    print("Metrics: results/quality_filter_metrics.csv")

finally:
    spark.stop()

print("\nQUALITY FILTERING COMPLETED SUCCESSFULLY!")
