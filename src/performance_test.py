
import os
import sys
import time
import csv
import json
from pathlib import Path
from statistics import median
from itertools import islice

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession

SOURCE_FILE = Path("data/sample/wet_documents.jsonl")
SAMPLE_DIR = Path("data/sample/performance")
RESULT_FILE = Path("results/performance_metrics.csv")

SAMPLE_SIZES = [2500, 5000, 10000]
REPEATS = 3

spark = (
    SparkSession.builder
    .appName("CurationPerformanceEvaluation")
    .master("local[2]")
    .config("spark.pyspark.python", sys.executable)
    .config("spark.pyspark.driver.python", sys.executable)
    .getOrCreate()
)

spark.sparkContext.setLogLevel("ERROR")


def create_sample_files():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)

    for size in SAMPLE_SIZES:
        output_file = SAMPLE_DIR / f"sample_{size}.jsonl"

        with SOURCE_FILE.open("r", encoding="utf-8") as source:
            records = list(islice(source, size))

        with output_file.open("w", encoding="utf-8") as output:
            output.writelines(records)

        if len(records) != size:
            raise ValueError(
                f"Expected {size} records, found {len(records)}"
            )

        print(f"Prepared {size} records.")


def measure(file_path, expected_count):
    start = time.perf_counter()

    df = spark.read.json(str(file_path))
    count = df.count()

    elapsed = time.perf_counter() - start

    if count != expected_count:
        raise ValueError(
            f"Expected {expected_count} records, found {count}"
        )

    return elapsed, count / elapsed


try:
    print("\nPREPARING PERFORMANCE SAMPLES")
    create_sample_files()

    detailed_results = []
    summary_results = []

    print("\nRUNNING PERFORMANCE EXPERIMENTS")
    print("=" * 55)

    for size in SAMPLE_SIZES:
        file_path = SAMPLE_DIR / f"sample_{size}.jsonl"

        print(f"\nDataset size: {size}")

        # Warm-up run: excluded from measured results.
        warmup_time, _ = measure(file_path, size)
        print(f"Warm-up completed: {warmup_time:.4f} seconds")

        times = []
        throughputs = []

        for run_number in range(1, REPEATS + 1):
            elapsed, throughput = measure(file_path, size)

            times.append(elapsed)
            throughputs.append(throughput)

            detailed_results.append([
                size,
                run_number,
                round(elapsed, 4),
                round(throughput, 2)
            ])

            print(
                f"Run {run_number}: {elapsed:.4f} seconds | "
                f"{throughput:.2f} docs/sec"
            )

        median_time = median(times)
        median_throughput = median(throughputs)

        summary_results.append([
            size,
            REPEATS,
            round(median_time, 4),
            round(median_throughput, 2)
        ])

        print(f"Median time: {median_time:.4f} seconds")
        print(f"Median throughput: {median_throughput:.2f} docs/sec")

    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with RESULT_FILE.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "documents",
            "measured_runs",
            "median_execution_time_seconds",
            "median_throughput_docs_per_second"
        ])
        writer.writerows(summary_results)

    detailed_file = Path("results/performance_run_details.csv")

    with detailed_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "documents",
            "run",
            "execution_time_seconds",
            "throughput_docs_per_second"
        ])
        writer.writerows(detailed_results)

    print("\nPERFORMANCE SUMMARY")
    for row in summary_results:
        print(row)

    print("\nSummary saved to:", RESULT_FILE)
    print("Individual runs saved to:", detailed_file)

    print("\nPERFORMANCE EVALUATION COMPLETED!")

finally:
    spark.stop()
