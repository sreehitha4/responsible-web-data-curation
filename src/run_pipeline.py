
import subprocess
import sys
import time
import csv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STAGES = [
    ("Spark Ingestion", "src/ingestion.py"),
    ("Deduplication", "src/deduplication.py"),
    ("Quality Filtering", "src/quality_filter.py"),
    ("PII Detection and Redaction", "src/pii_filter.py"),
]

METRICS_FILE = PROJECT_ROOT / "results" / "pipeline_execution_metrics.csv"


def run_pipeline():
    pipeline_start = time.perf_counter()
    stage_results = []

    print("\n" + "=" * 60)
    print(" RESPONSIBLE WEB-SCALE DATA CURATION PIPELINE")
    print("=" * 60)

    for stage_name, script_path in STAGES:
        print(f"\nStarting stage: {stage_name}")
        print("-" * 60)

        stage_start = time.perf_counter()

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / script_path)],
            cwd=PROJECT_ROOT
        )

        stage_time = time.perf_counter() - stage_start

        if result.returncode != 0:
            print(f"\nERROR: {stage_name} failed.")
            print("Pipeline execution stopped.")
            return 1

        stage_results.append((stage_name, stage_time))

        print(f"\n{stage_name} completed successfully.")
        print(f"Stage wall-clock time: {stage_time:.2f} seconds")

    total_time = time.perf_counter() - pipeline_start

    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)

    with METRICS_FILE.open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])

        for stage_name, elapsed in stage_results:
            metric_name = (
                stage_name.lower()
                .replace(" ", "_")
                .replace("and", "and")
                + "_wall_clock_seconds"
            )
            writer.writerow([metric_name, round(elapsed, 4)])

        writer.writerow([
            "total_pipeline_wall_clock_seconds",
            round(total_time, 4)
        ])

    print("\n" + "=" * 60)
    print(" COMPLETE PIPELINE EXECUTED SUCCESSFULLY!")
    print(f"Total pipeline time: {total_time:.2f} seconds")
    print("Execution metrics saved to:", METRICS_FILE)
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(run_pipeline())
