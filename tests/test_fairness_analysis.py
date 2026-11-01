
import pytest

from src.fairness_analysis import (
    analyze_topic_fairness,
    save_fairness_report
)


def test_topic_removal_rate():

    records = [
        {"topic": "Education", "retained": True},
        {"topic": "Education", "retained": False},
        {"topic": "Education", "retained": True}
    ]

    results = analyze_topic_fairness(records)

    education = results[0]

    assert education["input_documents"] == 3
    assert education["flagged_documents"] == 1
    assert education["removal_rate_percent"] == 33.33


def test_all_documents_retained():

    records = [
        {"topic": "Technology", "retained": True},
        {"topic": "Technology", "retained": True}
    ]

    results = analyze_topic_fairness(records)

    assert results[0]["removal_rate_percent"] == 0.0
    assert results[0]["retention_rate_percent"] == 100.0


def test_all_documents_flagged():

    records = [
        {"topic": "Politics", "retained": False},
        {"topic": "Politics", "retained": False}
    ]

    results = analyze_topic_fairness(records)

    assert results[0]["removal_rate_percent"] == 100.0
    assert results[0]["retention_rate_percent"] == 0.0


def test_missing_retained_field():

    records = [
        {"topic": "Education"}
    ]

    with pytest.raises(ValueError):
        analyze_topic_fairness(records)


def test_csv_report_creation(tmp_path):

    records = [
        {"topic": "Education", "retained": True},
        {"topic": "Education", "retained": False}
    ]

    results = analyze_topic_fairness(records)

    output = tmp_path / "fairness.csv"

    save_fairness_report(results, output)

    assert output.exists()
    assert output.stat().st_size > 0
