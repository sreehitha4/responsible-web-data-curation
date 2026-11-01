import pytest
from src.toxicity_filter import classify_scores, filter_records, retained_records


class FakeScorer:
    model_name = "synthetic-test-scorer"

    def score_batch(self, texts):
        lookup = {
            "A respectful educational sentence.": 0.02,
            "You are an idiot and I hate you.": 0.94,
            "A neutral discussion of public policy.": 0.08,
        }
        return [lookup[text] for text in texts]


def test_threshold_decisions():
    results = classify_scores([0.1, 0.8], threshold=0.5)
    assert results[0].retained is True
    assert results[1].retained is False


def test_invalid_threshold():
    with pytest.raises(ValueError):
        classify_scores([0.2], threshold=1.5)


def test_filter_records_and_statistics():
    records = [
        {"id": 1, "text": "A respectful educational sentence."},
        {"id": 2, "text": "You are an idiot and I hate you."},
        {"id": 3, "text": "A neutral discussion of public policy."},
    ]
    annotated, stats = filter_records(records, scorer=FakeScorer(), threshold=0.5)
    assert len(annotated) == 3
    assert stats["input_documents"] == 3
    assert stats["flagged_documents"] == 1
    assert stats["retained_documents"] == 2
    assert len(retained_records(annotated)) == 2


def test_missing_text_field():
    with pytest.raises(KeyError):
        filter_records([{"id": 1}], scorer=FakeScorer())
