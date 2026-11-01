
"""
Language-variety fairness evaluation.

Evaluates false positives and false negatives across
different varieties of English using Toxic-BERT.
"""

import csv
from pathlib import Path

from src.toxicity_filter import (
    HuggingFaceToxicityScorer,
    DEFAULT_THRESHOLD
)


def evaluate_language_fairness(
    records,
    scorer=None,
    threshold=DEFAULT_THRESHOLD
):
    """
    Each record contains:
        text
        language_variety
        is_toxic (manually assigned ground truth)
    """

    if not 0 <= threshold <= 1:
        raise ValueError("Threshold must be between 0 and 1")

    scorer = scorer or HuggingFaceToxicityScorer()

    # Validate input records
    for record in records:
        for field in ("text", "language_variety", "is_toxic"):
            if field not in record:
                raise ValueError(f"Missing field: {field}")

        if not isinstance(record["is_toxic"], bool):
            raise ValueError("is_toxic must be True or False")

    # Obtain real model predictions
    texts = [record["text"] for record in records]
    scores = []

    batch_size = 32

    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        scores.extend(scorer.score_batch(batch))

    if len(scores) != len(records):
        raise ValueError("Number of predictions does not match inputs")

    groups = {}

    for record, score in zip(records, scores):

        variety = record["language_variety"]

        if variety not in groups:
            groups[variety] = {
                "total": 0,
                "benign": 0,
                "toxic": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "correct_predictions": 0
            }

        stats = groups[variety]

        predicted_toxic = float(score) >= threshold
        actual_toxic = record["is_toxic"]

        stats["total"] += 1

        if actual_toxic:
            stats["toxic"] += 1
        else:
            stats["benign"] += 1

        if predicted_toxic and not actual_toxic:
            stats["false_positives"] += 1

        elif not predicted_toxic and actual_toxic:
            stats["false_negatives"] += 1

        else:
            stats["correct_predictions"] += 1

    results = []

    for variety, stats in sorted(groups.items()):

        benign = stats["benign"]
        toxic = stats["toxic"]
        total = stats["total"]

        fpr = (
            stats["false_positives"] / benign * 100
            if benign else None
        )

        fnr = (
            stats["false_negatives"] / toxic * 100
            if toxic else None
        )

        accuracy = (
            stats["correct_predictions"] / total * 100
            if total else 0
        )

        results.append({
            "language_variety": variety,
            "total_documents": total,
            "benign_documents": benign,
            "toxic_documents": toxic,
            "false_positives": stats["false_positives"],
            "false_negatives": stats["false_negatives"],
            "false_positive_rate": (
                round(fpr, 2) if fpr is not None else "N/A"
            ),
            "false_negative_rate": (
                round(fnr, 2) if fnr is not None else "N/A"
            ),
            "accuracy_percent": round(accuracy, 2)
        })

    return results


def save_language_report(results, output_path):

    if not results:
        raise ValueError("No evaluation results to save")

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


def print_language_report(results):

    print("\n========== LANGUAGE FAIRNESS REPORT ==========")

    for row in results:

        print(f"\nLanguage variety: {row['language_variety']}")
        print("Total:", row["total_documents"])
        print("False positives:", row["false_positives"])
        print("False negatives:", row["false_negatives"])
        print("False positive rate:", row["false_positive_rate"])
        print("False negative rate:", row["false_negative_rate"])
        print("Accuracy:", row["accuracy_percent"], "%")


if __name__ == "__main__":

    # Small synthetic, manually labelled evaluation set.
    # These are test examples, NOT representative language samples.

    sample_records = [

        # Standard English
        {
            "text": "Thank you for sharing this useful information.",
            "language_variety": "Standard English",
            "is_toxic": False
        },
        {
            "text": "You are an idiot and nobody likes you.",
            "language_variety": "Standard English",
            "is_toxic": True
        },

        # Indian English
        {
            "text": "Please do the needful and share the document.",
            "language_variety": "Indian English",
            "is_toxic": False
        },
        {
            "text": "You are stupid and completely useless.",
            "language_variety": "Indian English",
            "is_toxic": True
        },

        # Informal internet English
        {
            "text": "That movie was amazing lol.",
            "language_variety": "Informal English",
            "is_toxic": False
        },
        {
            "text": "Shut up, you pathetic loser.",
            "language_variety": "Informal English",
            "is_toxic": True
        },

        # Dialectal / non-standard English
        {
            "text": "I ain't agree with that, but respect your view.",
            "language_variety": "Dialectal English",
            "is_toxic": False
        },
        {
            "text": "You are a worthless fool.",
            "language_variety": "Dialectal English",
            "is_toxic": True
        }
    ]

    results = evaluate_language_fairness(sample_records)

    print_language_report(results)

    save_language_report(
        results,
        "outputs/language_fairness_report.csv"
    )

    print("\nLanguage fairness report saved successfully!")
