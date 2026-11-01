
import pytest

from src.language_fairness import evaluate_language_fairness


class FakeScorer:
    def score_batch(self, texts):
        scores = {
            "benign": 0.1,
            "toxic": 0.9,
            "false_positive": 0.8,
            "false_negative": 0.1
        }
        return [scores[text] for text in texts]


def test_correct_predictions():

    records = [
        {
            "text": "benign",
            "language_variety": "Standard English",
            "is_toxic": False
        },
        {
            "text": "toxic",
            "language_variety": "Standard English",
            "is_toxic": True
        }
    ]

    results = evaluate_language_fairness(
        records, scorer=FakeScorer()
    )

    assert results[0]["accuracy_percent"] == 100.0


def test_false_positive():

    records = [
        {
            "text": "false_positive",
            "language_variety": "Indian English",
            "is_toxic": False
        }
    ]

    results = evaluate_language_fairness(
        records, scorer=FakeScorer()
    )

    assert results[0]["false_positives"] == 1
    assert results[0]["false_positive_rate"] == 100.0


def test_false_negative():

    records = [
        {
            "text": "false_negative",
            "language_variety": "Informal English",
            "is_toxic": True
        }
    ]

    results = evaluate_language_fairness(
        records, scorer=FakeScorer()
    )

    assert results[0]["false_negatives"] == 1
    assert results[0]["false_negative_rate"] == 100.0


def test_missing_field():

    records = [
        {
            "text": "benign",
            "language_variety": "Standard English"
        }
    ]

    with pytest.raises(ValueError):
        evaluate_language_fairness(
            records, scorer=FakeScorer()
        )


def test_invalid_threshold():

    with pytest.raises(ValueError):
        evaluate_language_fairness(
            [], threshold=1.5
        )
