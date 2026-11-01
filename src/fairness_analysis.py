
"""
Fairness analysis for toxicity filtering.

Measures document removal rates across topic categories.
"""

from collections import defaultdict
import csv
from pathlib import Path


def analyze_topic_fairness(records):
    """
    Calculate topic-wise toxicity filtering statistics.

    Each record must contain:
        topic
        retained (True or False)
    """

    topic_stats = defaultdict(
        lambda: {
            "input_documents": 0,
            "flagged_documents": 0,
            "retained_documents": 0
        }
    )

    for record in records:

        topic = record.get("topic", "Unknown")

        if "retained" not in record:
            raise ValueError(
                "Each record must contain a retained field"
            )

        if not isinstance(record["retained"], bool):
            raise ValueError(
                "retained must be True or False"
            )

        topic_stats[topic]["input_documents"] += 1

        if record["retained"]:
            topic_stats[topic]["retained_documents"] += 1
        else:
            topic_stats[topic]["flagged_documents"] += 1

    results = []

    for topic, stats in sorted(topic_stats.items()):

        total = stats["input_documents"]
        flagged = stats["flagged_documents"]

        removal_rate = (
            flagged / total * 100 if total else 0
        )

        retention_rate = (
            stats["retained_documents"] / total * 100
            if total else 0
        )

        results.append({
            "topic": topic,
            "input_documents": total,
            "flagged_documents": flagged,
            "retained_documents": stats["retained_documents"],
            "removal_rate_percent": round(removal_rate, 2),
            "retention_rate_percent": round(retention_rate, 2)
        })

    return results


def save_fairness_report(results, output_path):
    """Save topic-wise fairness statistics as CSV."""

    if not results:
        raise ValueError("No fairness results to save")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )

        writer.writeheader()
        writer.writerows(results)


def print_fairness_report(results):

    print("\n========== TOPIC-WISE FAIRNESS REPORT ==========")

    for row in results:

        print(f"\nTopic: {row['topic']}")
        print("Input:", row["input_documents"])
        print("Flagged:", row["flagged_documents"])
        print("Retained:", row["retained_documents"])
        print("Removal rate:", row["removal_rate_percent"], "%")
        print("Retention rate:", row["retention_rate_percent"], "%")


if __name__ == "__main__":

    # Synthetic examples for testing only.
    sample_records = [
        {"topic": "Education", "retained": True},
        {"topic": "Education", "retained": True},
        {"topic": "Education", "retained": False},

        {"topic": "Politics", "retained": False},
        {"topic": "Politics", "retained": False},
        {"topic": "Politics", "retained": True},

        {"topic": "Technology", "retained": True},
        {"topic": "Technology", "retained": True},
        {"topic": "Technology", "retained": True},

        {"topic": "Entertainment", "retained": False},
        {"topic": "Entertainment", "retained": True},
        {"topic": "Entertainment", "retained": True},
    ]

    results = analyze_topic_fairness(sample_records)

    print_fairness_report(results)

    save_fairness_report(
        results,
        "outputs/topic_fairness_report.csv"
    )

    print("\nFairness report saved successfully!")
