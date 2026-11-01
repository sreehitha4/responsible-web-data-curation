# Model Card – Toxicity Detection Model

## 1. Model Information

| Field | Description |
|---|---|
| Model Name | unitary/toxic-bert |
| Model Type | Pretrained Transformer-based text classification model |
| Provider | Unitary |
| Platform | Hugging Face |
| Model Identifier | `unitary/toxic-bert` |
| Framework | PyTorch |
| Library | Hugging Face Transformers |
| Project | Responsible Web-Scale Data Curation |
| Responsible Member | Member 2 – Evaluation and Integration |

## 2. Model Description

The `unitary/toxic-bert` model is a pretrained language classification model designed to identify potentially toxic text.

It generates a toxicity score for each input document. In this project, the model is integrated into a data curation pipeline to screen web documents before they are considered for inclusion in the final training corpus.

The model is used without training from scratch.

## 3. Intended Use

- Automated toxicity screening of web documents.
- Identification of potentially harmful language.
- Supporting responsible training dataset preparation.
- Generating document-level toxicity scores.
- Assisting human reviewers in identifying content requiring further inspection.

The model is not intended to independently determine whether a document is legally or ethically unacceptable.

## 4. Input and Output

**Input:** Text documents from the Common Crawl dataset after PII redaction.

**Output:**
- `toxicity_score`
- `toxicity_label`
- `retained`

### Filtering Configuration

| Parameter | Value |
|---|---|
| Model | unitary/toxic-bert |
| Threshold | 0.50 |
| Score below 0.50 | Retained |
| Score equal to or above 0.50 | Flagged as potentially toxic |
| Inference device | CPU |
| Inference batch size | 8 |
| Maximum input length | 512 tokens |

## 5. Implementation Details

The implementation is maintained in:

- `src/toxicity_filter.py`
- `src/toxicity_pipeline.py`

The pipeline:

1. Reads PII-redacted Parquet documents.
2. Loads the pretrained Toxic-BERT model.
3. Processes documents in batches.
4. Generates toxicity scores.
5. Assigns filtering decisions using the configured threshold.
6. Saves annotated documents to Parquet.
7. Records corpus-level metrics and checkpoints.

## 6. Actual Corpus Evaluation

The model was evaluated on 6,996 documents from the Common Crawl WET dataset.

| Metric | Observed result |
|---|---:|
| Input documents | 6,996 |
| Flagged documents | 117 |
| Retained documents | 6,879 |
| Removal rate | 1.67% |
| Retention rate | 98.33% |
| Mean toxicity score | 0.04203 |
| Threshold | 0.50 |
| Execution time | 3,019.96 seconds |
| Throughput | 2.32 documents/second |

The results represent automated model predictions and filtering decisions. They do not establish classification accuracy because the corpus does not contain manually verified toxicity labels.

## 7. Automated Testing

The independent Member 2 test suite reported:

| Test module | Passed |
|---|---:|
| Toxicity filter | 4 |
| Topic fairness | 5 |
| Language fairness | 5 |
| Total | 14 |

The tests validate the implemented filtering and evaluation logic. They do not establish real-world model accuracy.

## 8. Limitations and Potential Biases

- Harmless discussions may be incorrectly flagged.
- Indirect harmful language may not be identified.
- Sarcasm and context-dependent language may affect predictions.
- Dialectal, informal and culturally specific expressions may be interpreted incorrectly.
- Language detection errors can affect group-level analysis.
- A toxicity score is a model prediction, not a definitive measure of harmfulness.
- Inputs are limited to 512 tokens, so longer documents are truncated during inference.

Particular attention is required when evaluating Indian English, dialectal English and informal language.

## 9. Responsible AI Considerations

The model is used as a screening component rather than an independent decision-maker.

Safeguards include:

- Documenting the filtering threshold.
- Recording toxicity scores and decisions.
- Measuring removal rates across detected language groups.
- Investigating potential false positives and false negatives using manually labelled data.
- Reporting limitations and sample sizes.
- Avoiding unsupported fairness claims.

Flagged documents should be treated as potentially toxic, not automatically assumed to be harmful in every context.

## 10. Final Evaluation Status

| Evaluation component | Status |
|---|---|
| Model selection | Completed |
| Dependency installation | Completed |
| Model integration | Completed |
| Synthetic example testing | Completed |
| Automated unit tests | 14 passed |
| Actual corpus inference | Completed |
| Language-wise descriptive analysis | Completed |
| Topic-wise fairness analysis | Pending |
| Manually labelled language-variety evaluation | Pending |
| Ground-truth accuracy and fairness validation | Pending |

**Model Card Status:** Updated preliminary version. Further validation using manually reviewed samples is required before making real-world fairness or accuracy claims.