import csv
from pathlib import Path

# Project paths
ROOT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT_DIR / "results"

PIPELINE_METRICS_FILE = RESULTS_DIR / "pipeline_execution_metrics.csv"
OUTPUT_FILE = RESULTS_DIR / "cost_estimation.csv"

# Illustrative cloud reference assumptions.
# This is NOT an actual AWS bill or a verified live price.
REFERENCE_INSTANCE = "t3.medium"
REFERENCE_REGION = "ap-south-1"
HOURLY_RATE_USD = 0.0448

# Number of input documents processed by the pipeline.
INPUT_DOCUMENTS = 10000


def read_pipeline_runtime():
    """Read the measured total pipeline wall-clock runtime."""

    if not PIPELINE_METRICS_FILE.exists():
        raise FileNotFoundError(
            f"Pipeline metrics file not found: {PIPELINE_METRICS_FILE}"
        )

    with open(PIPELINE_METRICS_FILE, "r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if row["metric"] == "total_pipeline_wall_clock_seconds":
                return float(row["value"])

    raise ValueError(
        "total_pipeline_wall_clock_seconds was not found "
        "in pipeline_execution_metrics.csv"
    )


def write_cost_estimate():
    runtime_seconds = read_pipeline_runtime()

    runtime_hours = runtime_seconds / 3600
    estimated_cost = runtime_hours * HOURLY_RATE_USD

    cost_per_1000_documents = (
        estimated_cost / INPUT_DOCUMENTS
    ) * 1000

    results = [
        ("reference_instance", REFERENCE_INSTANCE),
        ("reference_region", REFERENCE_REGION),
        ("assumed_hourly_rate_usd", f"{HOURLY_RATE_USD:.6f}"),
        ("pipeline_runtime_seconds", f"{runtime_seconds:.4f}"),
        ("pipeline_runtime_hours", f"{runtime_hours:.8f}"),
        ("input_documents", INPUT_DOCUMENTS),
        ("estimated_compute_cost_usd", f"{estimated_cost:.8f}"),
        (
            "estimated_cost_per_1000_input_documents_usd",
            f"{cost_per_1000_documents:.8f}",
        ),
        (
            "cost_type",
            "Illustrative cloud-equivalent compute estimate",
        ),
        (
            "runtime_basis",
            "Measured local pipeline runtime; assumed unchanged on reference instance",
        ),
        (
            "exclusions",
            "Storage, data transfer, taxes, and additional cloud services",
        ),
    ]

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["metric", "value"])
        writer.writerows(results)

    print("\nCOST ESTIMATION")
    print("=" * 55)

    for metric, value in results:
        print(f"{metric}: {value}")

    print("\nCost estimate saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    write_cost_estimate()