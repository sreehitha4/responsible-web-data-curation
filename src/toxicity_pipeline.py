
import csv
import json
import time
from pathlib import Path

from pyspark.sql import SparkSession

from toxicity_filter import (
    DEFAULT_THRESHOLD,
    HuggingFaceToxicityScorer,
    filter_records,
)

INPUT_PATH = "data/processed/pii_redacted_parquet"
OUTPUT_PATH = "data/processed/toxicity_scored_parquet"
CHECKPOINT_PATH = Path("results/toxicity_checkpoint.jsonl")
METRICS_PATH = Path("results/toxicity_metrics.csv")

CHECKPOINT_SIZE = 100
INFERENCE_BATCH_SIZE = 8
THRESHOLD = DEFAULT_THRESHOLD


def load_checkpoint():
    completed = {}
    if CHECKPOINT_PATH.exists():
        with CHECKPOINT_PATH.open(encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    record = json.loads(line)
                    completed[record["doc_id"]] = record
    return completed


def save_checkpoint(records):
    with CHECKPOINT_PATH.open("a", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")
        file.flush()


def main():
    start_time = time.time()

    if Path(OUTPUT_PATH).exists() and METRICS_PATH.exists():
        print("Toxicity output already exists.")
        print(f"Reusing existing Parquet: {OUTPUT_PATH}")
        print(f"Existing metrics: {METRICS_PATH}")
        return

    CHECKPOINT_PATH.parent.mkdir(parents=True, exist_ok=True)

    spark = (
        SparkSession.builder
        .appName("ToxicityFiltering")
        .master("local[2]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    try:
        print("Reading PII-redacted dataset...", flush=True)
        df = spark.read.parquet(INPUT_PATH)
        total = df.count()

        completed = load_checkpoint()
        print(f"Total documents: {total}", flush=True)
        print(f"Already checkpointed: {len(completed)}", flush=True)

        scorer = HuggingFaceToxicityScorer()
        pending = []

        iterator = df.select(
            "doc_id", "domain", "crawl_date", "text", "content_hash"
        ).toLocalIterator()

        for row in iterator:
            record = row.asDict(recursive=True)

            if record["doc_id"] in completed:
                continue

            pending.append(record)

            if len(pending) >= CHECKPOINT_SIZE:
                annotated, _ = filter_records(
                    pending,
                    threshold=THRESHOLD,
                    scorer=scorer,
                    batch_size=INFERENCE_BATCH_SIZE,
                )
                save_checkpoint(annotated)
                completed.update(
                    (r["doc_id"], r) for r in annotated
                )
                pending.clear()
                print(
                    f"Progress: {len(completed)}/{total} documents",
                    flush=True,
                )

        if pending:
            annotated, _ = filter_records(
                pending,
                threshold=THRESHOLD,
                scorer=scorer,
                batch_size=INFERENCE_BATCH_SIZE,
            )
            save_checkpoint(annotated)
            completed.update((r["doc_id"], r) for r in annotated)

        if len(completed) != total:
            raise RuntimeError(
                f"Expected {total} records, found {len(completed)}"
            )

        print("Creating final Parquet dataset...", flush=True)
        output_df = spark.read.json(str(CHECKPOINT_PATH))
        output_df.write.mode("overwrite").parquet(OUTPUT_PATH)

        records = list(completed.values())
        flagged = sum(not r["retained"] for r in records)
        retained = total - flagged
        elapsed = time.time() - start_time

        stats = {
            "input_documents": total,
            "flagged_documents": flagged,
            "retained_documents": retained,
            "removal_rate": flagged / total if total else 0,
            "retention_rate": retained / total if total else 0,
            "threshold": THRESHOLD,
            "model": scorer.model_name,
            "mean_toxicity_score": (
                sum(r["toxicity_score"] for r in records) / total
                if total else 0
            ),
            "execution_time_seconds": round(elapsed, 2),
            "throughput_documents_per_second": round(
                total / elapsed, 2
            ) if elapsed else 0,
        }

        with METRICS_PATH.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(file, fieldnames=stats.keys())
            writer.writeheader()
            writer.writerow(stats)

        print("\n========== TOXICITY PIPELINE RESULTS ==========")
        print(json.dumps(stats, indent=2))
        print(f"Parquet: {OUTPUT_PATH}")
        print(f"Metrics: {METRICS_PATH}")

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
