# Responsible Web-Scale Data Curation

A Spark-based data curation pipeline that prepares a sample of Common Crawl text data through ingestion, deduplication, quality filtering, PII detection and redaction, and transformer-based toxicity screening.

The project also evaluates language-wise removal patterns, measures pipeline performance, and documents responsible AI considerations.

## 1. Project Overview

Web-scale text collections may contain duplicate, low-quality, toxic, and potentially sensitive content. Preparing such data for downstream machine learning requires a systematic and responsible curation process.

This project implements a reproducible Apache Spark pipeline using a 10,000-document sample of Common Crawl WET data.

### Pipeline stages

1. **Data ingestion:** Load extracted text records into Spark and store them in Parquet format.
2. **Deduplication:** Identify exact duplicates using normalized text and SHA-256 hashes.
3. **Quality filtering:** Remove empty, short, low-word-count, and low-alphabetic-ratio documents.
4. **PII detection and redaction:** Detect email and phone-like patterns and replace them with redaction placeholders.
5. **Toxicity detection and filtering:** Apply the pretrained `unitary/toxic-bert` model to score documents and flag potentially toxic content.
6. **Language-wise fairness analysis:** Examine observed toxicity-removal rates across automatically detected languages.

The current prototype uses Spark local mode with two worker threads (`local[2]`).

## 2. Technology Stack

- Python 3.11
- Apache Spark 3.5.6
- PySpark
- Java
- PyTorch
- Hugging Face Transformers
- Toxic-BERT (`unitary/toxic-bert`)
- langdetect
- Requests
- Warcio
- PyArrow
- Parquet
- JSONL
- Pandas
- Matplotlib
- Pytest

## 3. Repository Structure

```text
responsible-web-data-curation/
|
|-- data/
|   |-- raw/
|   |-- sample/
|   |-- processed/
|
|-- src/
|   |-- extract_wet.py
|   |-- ingestion.py
|   |-- deduplication.py
|   |-- quality_filter.py
|   |-- pii_filter.py
|   |-- pii_patterns.py
|   |-- toxicity_filter.py
|   |-- toxicity_pipeline.py
|   |-- language_fairness_analysis.py
|   |-- fairness_analysis.py
|   |-- language_fairness.py
|   |-- run_pipeline.py
|   |-- validate_pipeline.py
|   |-- performance_test.py
|   |-- cost_estimation.py
|   |-- collect_results.py
|
|-- scripts/
|   |-- download_dataset.py
|
|-- tests/
|   |-- test_pii_patterns.py
|   |-- test_toxicity_filter.py
|   |-- test_fairness_analysis.py
|   |-- test_language_fairness.py
|
|-- data/
|-- docs/
|   |-- model_card.md
|   |-- data_card.md
|
|-- notebooks/
|   |-- results_notebook.ipynb
|
|-- reports/
|-- results/
|-- requirements.txt
|-- README.md
```

The raw dataset, extracted sample, generated Parquet datasets, and large intermediate files are excluded from Git tracking.

## 4. Dataset

The project uses a WET segment from:

- Source: Common Crawl
- Collection: CC-MAIN-2026-43
- Format: WET (Web Extracted Text)
- Extraction limit: 10,000 documents

The selected segment URL is configured in `scripts/download_dataset.py`.

Each extracted record contains:

- `doc_id`
- `domain`
- `crawl_date`
- `text`

Common Crawl availability does not mean every crawled page has the same copyright or reuse licence.

## 5. Environment Setup

### Prerequisites

- Python 3.11
- Java runtime compatible with Apache Spark 3.5.6
- Git

### Clone the repository

```powershell
git clone https://github.com/sreehitha4/responsible-web-data-curation.git

cd responsible-web-data-curation
```

### Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv

.venv\Scripts\Activate.ps1
```

### Install dependencies

```powershell
python -m pip install -r requirements.txt
```

Check the Python and Java versions:

```powershell
python --version
java -version
```

For Spark execution on Windows, configure the Python interpreter:

```powershell
$env:PYSPARK_PYTHON = (Get-Command python).Source
$env:PYSPARK_DRIVER_PYTHON = (Get-Command python).Source
```

## 6. Dataset Download and Extraction

### Step 1: Download the Common Crawl segment

```powershell
python scripts/download_dataset.py
```

The compressed WET file is saved under:

`data/raw/`

The download script also creates a local `dataset_source.txt` provenance file.

### Step 2: Extract text documents

```powershell
python src/extract_wet.py
```

The extraction script reads the WET archive and writes up to 10,000 conversion records in JSONL format.

Output:

`data/sample/wet_documents.jsonl`

## 7. Run the Complete Curation Pipeline

After dataset extraction, execute:

```powershell
python src/run_pipeline.py
```

The runner executes these stages sequentially:

| Stage | Script |
|---|---|
| Spark ingestion | `src/ingestion.py` |
| Deduplication | `src/deduplication.py` |
| Quality filtering | `src/quality_filter.py` |
| PII detection and redaction | `src/pii_filter.py` |
| Toxicity detection and filtering | `src/toxicity_pipeline.py` |
| Language-wise fairness analysis | `src/language_fairness_analysis.py` |

### Processed outputs

- `data/processed/ingested_parquet`
- `data/processed/deduplicated_parquet`
- `data/processed/quality_filtered_parquet`
- `data/processed/pii_redacted_parquet`
- `data/processed/toxicity_scored_parquet`

The toxicity stage uses checkpointing so that completed document predictions can be reused if inference is interrupted.

The first execution may take considerably longer because the pretrained model must be downloaded and loaded.

## 8. Toxicity Detection

The project integrates the pretrained `unitary/toxic-bert` transformer model.

The model assigns toxicity scores to document text. Documents scoring at or above the configured threshold of `0.50` are flagged as potentially toxic.

### Observed results

| Metric | Result |
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

These are screening predictions, not verified ground-truth toxicity labels.

## 9. Language-wise Fairness Analysis

The pipeline uses automatic language identification to group documents by detected language and calculate observed toxicity-removal rates.

The analysis is stored in:

`results/language_fairness_actual.csv`

The results notebook visualizes language-wise removal patterns and documents the limitations of this analysis.

Important limitations:

- Automatic language identification may be imperfect.
- Language groups can contain different content distributions.
- Small sample groups are excluded from the comparison chart.
- Language identification does not establish dialect or language variety.
- Observed differences do not independently establish model bias.

Topic-wise fairness analysis and manually labelled language-variety evaluation require validated annotations and remain pending.

## 10. Validation and Testing

### Validate the processed datasets

```powershell
python src/validate_pipeline.py
```

The validation script checks expected document counts, required columns, duplicate hashes, null text, and remaining email and phone-pattern matches.

### Run unit tests

```powershell
python -m pytest tests -v
```

The current integrated test suite contains 20 tests:

| Test module | Tests |
|---|---:|
| Topic fairness analysis | 5 |
| Language fairness analysis | 4 |
| PII detection and redaction | 7 |
| Toxicity filtering | 4 |
| **Total** | **20** |

Latest recorded test result: **20 passed**.

## 11. Results Notebook

Open:

`notebooks/results_notebook.ipynb`

The notebook presents:

- Stage-wise document counts
- Deduplication and quality-filtering results
- PII detection and redaction metrics
- Toxicity filtering results
- Language-wise removal-rate analysis
- Pipeline execution time and throughput
- Responsible AI observations and limitations

Run the notebook using the project's Python 3.11 virtual environment.

## 12. Performance Benchmarking

Run:

```powershell
python src/performance_test.py
```

The benchmark performs a warm-up run and three measured runs for each input size.

Previously recorded median results:

| Documents | Median execution time | Median throughput |
|---:|---:|---:|
| 2,500 | 0.5165 seconds | 4,840.16 docs/sec |
| 5,000 | 0.6004 seconds | 8,327.47 docs/sec |
| 10,000 | 0.7429 seconds | 13,460.71 docs/sec |

These figures measure a local Spark JSON read-and-count benchmark. They are not full-pipeline or distributed-cluster throughput measurements.

The integrated pipeline's measured stage execution times are recorded separately in `results/pipeline_execution_metrics.csv`.

## 13. Runtime and Cost Estimation

Generate the illustrative compute cost estimate using:

```powershell
python src/cost_estimation.py
```

The estimate uses an assumed cloud instance and hourly rate. It is an illustrative comparison, not an actual cloud bill.

Storage, network transfer, taxes, and additional cloud services may not be included.

The pipeline runner records stage-wise wall-clock execution times in:

`results/pipeline_execution_metrics.csv`

## 14. Consolidated Results

Run:

```powershell
python src/collect_results.py
```

This generates:

`results/pipeline_summary.csv`

The summary combines available ingestion, deduplication, quality filtering, PII, performance, runtime, and cost metrics.

## 15. Observed Processing Results

| Stage | Documents |
|---|---:|
| Initial ingestion | 10,000 |
| After deduplication | 9,833 |
| After quality filtering | 6,996 |
| After PII redaction | 6,996 |
| After toxicity filtering | 6,879 |

Additional observations:

- 167 duplicate copies were removed.
- 2,837 documents were removed by quality filtering.
- 2,046 documents contained email patterns.
- 1,206 documents contained phone-like patterns.
- 117 documents were flagged by Toxic-BERT.

Email and phone counts can overlap because a document may contain both.

## 16. Responsible Data Handling and Limitations

- PII values are replaced with redaction placeholders; raw values are not written to metrics.
- Regular-expression detection cannot guarantee that all personal information is detected.
- Exact normalized-text deduplication does not identify semantic or near-duplicate content.
- The ASCII-based alphabetic-ratio filter may disproportionately exclude non-English or non-Latin-script content.
- Toxicity scores are model predictions, not verified labels.
- No manually labelled full-corpus evaluation was available to calculate reliable false-positive and false-negative rates.
- Language-wise differences are descriptive and do not prove discriminatory model behaviour.
- Topic-wise fairness evaluation requires validated topic labels.
- The experiment uses a 10,000-document sample from one Common Crawl segment.
- The current Spark implementation runs locally using two worker threads rather than on a distributed cluster.
- Common Crawl access does not establish a uniform licence for all crawled pages.

## 17. Documentation and Results

- `docs/model_card.md` — Toxic-BERT model details, intended use, evaluation results, and limitations.
- `docs/data_card.md` — dataset source, composition, processing stages, and limitations.
- `reports/dataset_schema.md` — dataset schema and processing details.
- `reports/pipeline_handoff.md` — pipeline execution and handoff information.
- `notebooks/results_notebook.ipynb` — integrated results and fairness analysis.
- `results/` — processing metrics, benchmark results, runtime metrics, and cost estimates.

## 18. Project Conclusion

The project demonstrates a distributed data-curation workflow combining Spark-based processing, exact deduplication, quality filtering, PII redaction, and transformer-based toxicity screening.

The actual experiment retained 6,879 documents from the initial 10,000-document sample. The evaluation also highlights responsible data curation concerns, including potential language-related filtering effects, model limitations, and the computational cost of transformer-based screening.

Further manually labelled fairness evaluation and larger-scale performance testing are required before drawing stronger conclusions.