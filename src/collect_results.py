
import csv
from pathlib import Path

# Resolve paths relative to the project directory.
ROOT_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT_DIR / "results"
OUTPUT_FILE = RESULTS_DIR / "pipeline_summary.csv"

# All metrics files to be consolidated.
FILES = {
    "ingestion": "ingestion_metrics.csv",
    "deduplication": "deduplication_metrics.csv",
    "quality_filtering": "quality_filter_metrics.csv",
    "pii_redaction": "pii_metrics.csv",
    "performance": "performance_metrics.csv",
    "pipeline_execution": "pipeline_execution_metrics.csv",
    "cost_estimation": "cost_estimation.csv",
}


def collect_metrics():
    summary = []

    for stage, filename in FILES.items():
        path = RESULTS_DIR / filename

        if not path.exists():
            raise FileNotFoundError(
                f"Missing metrics file: {path}"
            )

        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            if not reader.fieldnames:
                raise ValueError(
                    f"Empty or invalid CSV file: {path}"
                )

            for row in reader:
                # Handle metric,value CSV files.
                if reader.fieldnames == ["metric", "value"]:
                    summary.append([
                        stage,
                        row.get("metric", ""),
                        row.get("value", "")
                    ])

                # Handle multi-column CSV files, such as performance metrics.
                else:
                    for metric, value in row.items():
                        if metric is not None and value is not None:
                            summary.append([
                                stage,
                                metric,
                                value
                            ])

        print(
            f"Collected {filename}: "
            f"{sum(1 for item in summary if item[0] == stage)} metrics"
        )

    # Write consolidated results.
    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:
        writer = csv.writer(file)
        writer.writerow(["stage", "metric", "value"])
        writer.writerows(summary)

    print("\n" + "=" * 55)
    print("CONSOLIDATED RESULTS")
    print("=" * 55)
    print("Output file:", OUTPUT_FILE)
    print("Total metric records:", len(summary))
    print("Stages included:", len(FILES))


if __name__ == "__main__":
    collect_metrics()
