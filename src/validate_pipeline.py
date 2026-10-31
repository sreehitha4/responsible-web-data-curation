
import os
import sys

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

from pii_patterns import EMAIL_PATTERN, PHONE_PATTERN

DATASETS = {
    "Ingestion": {
        "path": "data/processed/ingested_parquet",
        "expected_count": 10000
    },
    "Deduplication": {
        "path": "data/processed/deduplicated_parquet",
        "expected_count": 9833
    },
    "Quality Filtering": {
        "path": "data/processed/quality_filtered_parquet",
        "expected_count": 6996
    },
    "PII Redaction": {
        "path": "data/processed/pii_redacted_parquet",
        "expected_count": 6996
    }
}

REQUIRED_COLUMNS = {
    "doc_id",
    "domain",
    "crawl_date",
    "text"
}


def main():
    spark = (
        SparkSession.builder
        .appName("PipelineFinalValidation")
        .master("local[2]")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    all_passed = True

    try:
        print("\n" + "=" * 60)
        print("FINAL PIPELINE VALIDATION")
        print("=" * 60)

        for stage, details in DATASETS.items():
            print(f"\nChecking: {stage}")

            df = spark.read.parquet(details["path"])

            actual_count = df.count()
            expected_count = details["expected_count"]

            count_passed = actual_count == expected_count

            print("Expected documents:", expected_count)
            print("Actual documents:", actual_count)
            print("Document count:", "PASS" if count_passed else "FAIL")

            if not count_passed:
                all_passed = False

            missing_columns = REQUIRED_COLUMNS - set(df.columns)

            columns_passed = len(missing_columns) == 0

            print("Available columns:", df.columns)
            print(
                "Required columns:",
                "PASS" if columns_passed else "FAIL"
            )

            if missing_columns:
                print("Missing columns:", sorted(missing_columns))
                all_passed = False

            if stage == "Deduplication":
                if "content_hash" in df.columns:
                    unique_hashes = (
                        df.select("content_hash")
                        .distinct()
                        .count()
                    )

                    duplicate_hashes = actual_count - unique_hashes

                    print("Remaining duplicate hashes:", duplicate_hashes)

                    if duplicate_hashes != 0:
                        all_passed = False
                else:
                    print(
                        "Content hash column unavailable; "
                        "duplicate verification skipped."
                    )

            if stage == "PII Redaction":
                null_texts = df.filter(
                    col("text").isNull()
                ).count()

                remaining_emails = df.filter(
                    col("text").rlike(EMAIL_PATTERN)
                ).count()

                remaining_phones = df.filter(
                    col("text").rlike(PHONE_PATTERN)
                ).count()

                print("Null text documents:", null_texts)
                print("Remaining email-pattern documents:", remaining_emails)
                print("Remaining phone-pattern documents:", remaining_phones)

                pii_passed = (
                    null_texts == 0
                    and remaining_emails == 0
                    and remaining_phones == 0
                )

                print(
                    "PII pattern validation:",
                    "PASS" if pii_passed else "CHECK REQUIRED"
                )

                if not pii_passed:
                    all_passed = False

        print("\n" + "=" * 60)

        if all_passed:
            print("ALL PIPELINE VALIDATION CHECKS PASSED!")
        else:
            print("SOME VALIDATION CHECKS NEED ATTENTION.")

        print("=" * 60)

    finally:
        spark.stop()

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
