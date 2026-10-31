
import csv
from pathlib import Path

RESULTS_DIR = Path("results")
OUTPUT_FILE = RESULTS_DIR / "pipeline_summary.csv"

FILES = {
    "ingestion": "ingestion_metrics.csv",
    "deduplication": "deduplication_metrics.csv",
    "quality_filtering": "quality_filter_metrics.csv",
    "pii_redaction": "pii_metrics.csv",
    "performance": "performance_metrics.csv",
}

summary = []

for stage, filename in FILES.items():
    path = RESULTS_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing metrics file: {path}")

    with path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if reader.fieldnames == ["metric", "value"]:
                summary.append([
                    stage,
                    row["metric"],
                    row["value"]
                ])
            else:
                for metric, value in row.items():
                    if metric is not None and value is not None:
                        summary.append([stage, metric, value])

with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["stage", "metric", "value"])
    writer.writerows(summary)

print("Consolidated metrics saved to:", OUTPUT_FILE)
print("Total metric records:", len(summary))
