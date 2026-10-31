
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

STAGES = [
    ("Spark Ingestion", "src/ingestion.py"),
    ("Deduplication", "src/deduplication.py"),
    ("Quality Filtering", "src/quality_filter.py"),
    ("PII Detection and Redaction", "src/pii_filter.py"),
]

def run_pipeline():
    pipeline_start = time.perf_counter()

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
            print("Pipeline stopped. Please check the error above.")
            return

        print(f"\n{stage_name} completed successfully.")
        print(f"Stage execution time: {stage_time:.2f} seconds")

    total_time = time.perf_counter() - pipeline_start

    print("\n" + "=" * 60)
    print(" COMPLETE PIPELINE EXECUTED SUCCESSFULLY!")
    print(f"Total pipeline execution time: {total_time:.2f} seconds")
    print("=" * 60)


if __name__ == "__main__":
    run_pipeline()
