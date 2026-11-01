"""
Configurable toxicity scoring and filtering module.

Default model: unitary/toxic-bert (multi-label toxicity classifier).
The Hugging Face model is downloaded on first use and cached locally.

Expected input: a sequence of strings, or records containing a text field.
Output: original records plus toxicity_score, toxicity_label, and retained.
This module is deliberately independent of Spark so it can be tested alone
and integrated later through a Spark UDF or pandas batch.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Mapping, Sequence

DEFAULT_MODEL = "unitary/toxic-bert"
DEFAULT_THRESHOLD = 0.50


@dataclass
class ToxicityResult:
    toxicity_score: float
    toxicity_label: str
    retained: bool


class HuggingFaceToxicityScorer:
    """Lazy-loading wrapper; importing this module does not download a model."""

    def __init__(self, model_name: str = DEFAULT_MODEL, device: int = -1):
        self.model_name = model_name
        self.device = device
        self._pipeline = None

    def _load(self):
        if self._pipeline is None:
            try:
                from transformers import pipeline
            except ImportError as exc:
                raise RuntimeError(
                    "Install dependencies with: pip install -r requirements-member2.txt"
                ) from exc
            self._pipeline = pipeline(
                "text-classification",
                model=self.model_name,
                tokenizer=self.model_name,
                device=self.device,
                top_k=None,
                truncation=True,
            )
        return self._pipeline

    def score_batch(self, texts: Sequence[str]) -> list[float]:
        if not texts:
            return []
        predictions = self._load()(list(texts), batch_size=8, truncation=True, max_length=512)
        scores = []
        for item in predictions:
            # Multi-label pipelines return [{label, score}, ...].
            # Use the explicit TOXIC label where available.
            labels = item if isinstance(item, list) else [item]
            toxic = [
                float(p["score"]) for p in labels
                if str(p.get("label", "")).upper() in {"TOXIC", "LABEL_1"}
            ]
            scores.append(max(toxic, default=max(float(p["score"]) for p in labels)))
        return scores


def classify_scores(
    scores: Iterable[float],
    threshold: float = DEFAULT_THRESHOLD,
) -> list[ToxicityResult]:
    """Convert model scores into transparent retain/remove decisions."""
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")
    results = []
    for raw_score in scores:
        score = float(raw_score)
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"toxicity score must be in [0, 1], got {score}")
        flagged = score >= threshold
        results.append(ToxicityResult(
            toxicity_score=score,
            toxicity_label="flagged_toxic" if flagged else "retained",
            retained=not flagged,
        ))
    return results


def filter_records(
    records: Sequence[Mapping[str, Any]],
    text_field: str = "text",
    threshold: float = DEFAULT_THRESHOLD,
    scorer: Any | None = None,
    batch_size: int = 32,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """
    Score records in batches. `scorer` can be injected for deterministic tests.
    Returns (annotated_records, statistics). Does not silently discard records:
    callers can inspect all annotations and then select retained records.
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    for i, record in enumerate(records):
        if text_field not in record:
            raise KeyError(f"record {i} has no {text_field!r} field")

    scorer = scorer or HuggingFaceToxicityScorer()
    output: list[dict[str, Any]] = []
    all_scores: list[float] = []

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]
        texts = [str(row[text_field] or "") for row in batch]
        scores = scorer.score_batch(texts)
        if len(scores) != len(batch):
            raise ValueError("scorer returned a different number of scores than inputs")
        decisions = classify_scores(scores, threshold)
        for row, decision in zip(batch, decisions):
            annotated = dict(row)
            annotated.update({
                "toxicity_score": decision.toxicity_score,
                "toxicity_label": decision.toxicity_label,
                "retained": decision.retained,
            })
            output.append(annotated)
            all_scores.append(decision.toxicity_score)

    flagged = sum(not row["retained"] for row in output)
    total = len(output)
    stats = {
        "input_documents": total,
        "flagged_documents": flagged,
        "retained_documents": total - flagged,
        "removal_rate": flagged / total if total else 0.0,
        "retention_rate": (total - flagged) / total if total else 0.0,
        "threshold": threshold,
        "model": getattr(scorer, "model_name", "injected_test_scorer"),
        "mean_toxicity_score": sum(all_scores) / total if total else 0.0,
    }
    return output, stats


def retained_records(annotated_records: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return copies of records that passed the configured threshold."""
    return [dict(row) for row in annotated_records if row.get("retained") is True]


