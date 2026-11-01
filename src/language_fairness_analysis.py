import csv
from collections import defaultdict
from pathlib import Path

from langdetect import DetectorFactory, detect, LangDetectException
from pyspark.sql import SparkSession

DetectorFactory.seed = 42

INPUT_PATH = "data/processed/toxicity_scored_parquet"
OUTPUT_PATH = Path("results/language_fairness_actual.csv")
MIN_TEXT_LENGTH = 100


def detect_language(text):
    if not text or len(text.strip()) < MIN_TEXT_LENGTH:
        return "unknown"

    try:
        return detect(text[:5000])
    except LangDetectException:
        return "unknown"


def main():
    spark = (
        SparkSession.builder
        .appName("LanguageFairnessAnalysis")
        .master("local[2]")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    try:
        df = spark.read.parquet(INPUT_PATH)

        stats = defaultdict(
            lambda: {
                "input_documents": 0,
                "flagged_documents": 0,
                "retained_documents": 0,
            }
        )

        print("Analysing language distribution...", flush=True)

        for row in df.select(
            "text", "retained"
        ).toLocalIterator():

            language = detect_language(row["text"])
            group = stats[language]

            group["input_documents"] += 1

            if row["retained"]:
                group["retained_documents"] += 1
            else:
                group["flagged_documents"] += 1

        results = []

        for language, values in sorted(stats.items()):
            total = values["input_documents"]
            flagged = values["flagged_documents"]
            retained = values["retained_documents"]

            results.append({
                "language": language,
                **values,
                "removal_rate_percent": round(
                    flagged / total * 100, 2
                ) if total else 0,
                "retention_rate_percent": round(
                    retained / total * 100, 2
                ) if total else 0,
            })

        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

        with OUTPUT_PATH.open(
            "w", newline="", encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file, fieldnames=results[0].keys()
            )
            writer.writeheader()
            writer.writerows(results)

        print("\n========== LANGUAGE ANALYSIS ==========")
        for result in results:
            print(result)

        print("\nTotal documents:", sum(
            r["input_documents"] for r in results
        ))
        print("Report saved:", OUTPUT_PATH)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
