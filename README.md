# Responsible Web-Scale Data Curation

A Spark-based data curation pipeline that prepares a sample of Common Crawl text data through deduplication, quality filtering, and PII pattern detection and redaction.

The project also measures processing performance, execution time, and illustrative cloud-equivalent compute cost.

## 1. Project Overview

Web-scale text collections may contain duplicate, low-quality, and potentially sensitive content. Preparing such data for downstream machine learning requires a systematic curation process.

This project implements a reproducible Apache Spark pipeline using a sample of Common Crawl WET data.

### Current pipeline stages

1. **Data ingestion:** Load extracted text records into Spark.
2. **Deduplication:** Identify exact duplicates using normalized text and SHA-256 hashes.
3. **Quality filtering:** Remove empty, short, low-word-count, and low-alphabetic-ratio documents.
4. **PII detection and redaction:** Detect email and phone-like patterns and replace them with redaction placeholders.

The current prototype uses Spark local mode with two worker threads (`local[2]`).

## 2. Technology Stack

- Python 3.11
- Apache Spark 3.5.6
- PySpark
- Java 8 (Temurin JDK)
- Requests
- Warcio
- PyArrow
- Parquet
- JSONL
- CSV

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
|   |-- __init__.py
|   |-- test_pii_patterns.py
|
|-- results/
|-- reports/
|-- notebooks/
|-- requirements.txt
|-- README.md
```

The raw dataset, extracted sample, and generated Parquet datasets are excluded from Git tracking.

## 4. Dataset

The project uses a WET segment from:

- Source: Common Crawl
- Collection: CC-MAIN-2026-43
- Format: WET (Web Extracted Text)
- Extraction limit: 10,000 documents

The selected segment URL is configured in `scripts/download_dataset.py`.

Common Crawl availability does not mean every crawled page has the same copyright or reuse licence.

## 5. Environment Setup

### Prerequisites

- Python 3.11
- Java 8 (the tested environment uses Temurin 8u502)
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

Check Java:

```powershell
java -version
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

Each extracted record contains:

- `doc_id`
- `domain`
- `crawl_date`
- `text`

Full source URLs are not retained in the extracted records.

## 7. Run the Curation Pipeline

After dataset extraction, execute:

```powershell
python src/run_pipeline.py
```

The runner executes the following stages sequentially:

| Stage | Script |
|---|---|
| Ingestion | `src/ingestion.py` |
| Deduplication | `src/deduplication.py` |
| Quality filtering | `src/quality_filter.py` |
| PII redaction | `src/pii_filter.py` |

### Processed outputs

- `data/processed/ingested_parquet`
- `data/processed/deduplicated_parquet`
- `data/processed/quality_filtered_parquet`
- `data/processed/pii_redacted_parquet`

## 8. Validation and Testing

### Validate the processed datasets

```powershell
python src/validate_pipeline.py
```

The validation checks expected document counts, required columns, duplicate hashes, null text, and remaining email and phone-pattern matches.

### Run unit tests

```powershell
python -m unittest discover -s tests -v
```

The current PII test suite contains six tests.

## 9. Performance Benchmarking

Run:

```powershell
python src/performance_test.py
```

The benchmark performs a warm-up run and three measured runs for each input size.

Observed median results:

| Documents | Median execution time | Median throughput |
|---:|---:|---:|
| 2,500 | 0.5165 seconds | 4,840.16 docs/sec |
| 5,000 | 0.6004 seconds | 8,327.47 docs/sec |
| 10,000 | 0.7429 seconds | 13,460.71 docs/sec |

These figures measure a local Spark JSON read-and-count benchmark. They are not full-pipeline or distributed-cluster throughput measurements.

## 10. Runtime and Cost Estimation

The pipeline runner records stage-wise wall-clock execution times in:

`results/pipeline_execution_metrics.csv`

The latest recorded total pipeline wall-clock runtime was approximately **117.1265 seconds**.

Latest stage-wise execution times:

| Stage | Wall-clock time |
|---|---:|
| Ingestion | 25.66 seconds |
| Deduplication | 34.64 seconds |
| Quality filtering | 33.43 seconds |
| PII processing | 23.40 seconds |
| Total | 117.13 seconds |

Generate the illustrative compute cost estimate using:

```powershell
python src/cost_estimation.py
```

Latest cost estimation:

| Metric | Value |
|---|---:|
| Reference instance | t3.medium |
| Reference region | ap-south-1 |
| Assumed hourly rate | USD 0.0448 |
| Estimated compute cost | USD 0.00145757 |
| Estimated cost per 1,000 documents | USD 0.00014576 |

The estimate assumes that the local pipeline runtime remains unchanged on the reference cloud instance. It is an illustrative comparison, not an actual cloud bill.

Storage, network transfer, taxes, and additional cloud services are excluded.

## 11. Consolidated Results

Run:

```powershell
python src/collect_results.py
```

This generates:

`results/pipeline_summary.csv`

The summary combines ingestion, deduplication, quality filtering, PII, performance, runtime, and cost metrics.

## 12. Observed Processing Results

| Stage | Documents |
|---|---:|
| Initial ingestion | 10,000 |
| After deduplication | 9,833 |
| After quality filtering | 6,996 |
| After PII redaction | 6,996 |

Additional observations:

- 167 duplicate copies were removed.
- 2,837 documents were removed by quality filtering.
- 2,046 documents contained email patterns.
- 1,206 documents contained phone-like patterns.

Email and phone counts can overlap because a document may contain both.

## 13. Responsible Data Handling and Limitations

- The extracted dataset retains limited metadata and does not retain full source URLs.
- PII values are replaced with redaction placeholders; raw values are not written to metrics.
- Regular-expression detection cannot guarantee that all personal information is detected.
- Exact normalized-text deduplication does not identify semantic or near-duplicate content.
- The ASCII-based alphabetic-ratio filter may disproportionately exclude non-English or non-Latin-script content.
- The experiment uses a 10,000-document sample from one Common Crawl segment.
- The current Spark implementation runs locally using two worker threads rather than on a distributed cluster.
- Common Crawl access does not establish a uniform licence for all crawled pages.

## 14. Reports and Results

- `reports/dataset_schema.md` — dataset schema and processing details.
- `reports/pipeline_handoff.md` — pipeline execution and handoff instructions.
- `results/` — processing metrics, benchmark results, runtime metrics, and cost estimate.