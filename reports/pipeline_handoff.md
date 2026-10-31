# Pipeline Handoff Documentation

## 1. Project Overview

This document describes the individual data-curation pipeline implemented for the Responsible Web-Scale Data Curation project.

The pipeline uses Apache Spark to process a Common Crawl WET dataset and performs:

1. Dataset ingestion
2. Exact duplicate detection and removal
3. Content quality filtering
4. PII pattern detection and redaction
5. Pipeline execution measurement
6. Performance benchmarking and cost estimation

The implementation is designed to be reproducible using the documented environment and commands.

## 2. Dataset Information

| Attribute | Details |
|---|---|
| Dataset | Common Crawl |
| Collection | CC-MAIN-2026-43 |
| Dataset format | WET (`.warc.wet.gz`) |
| Source file | `CC-MAIN-20261005105623-20261005135623-00000.warc.wet.gz` |
| Original file size | 64,395,252 bytes |
| Maximum extracted documents | 10,000 |
| Extracted format | JSONL |

The extracted documents contain the following fields:

- `doc_id`: Document identifier.
- `domain`: Website hostname.
- `crawl_date`: Crawl timestamp.
- `text`: Extracted document text.

The pipeline does not retain complete source URLs in its processed records.

## 3. Environment Requirements

The implementation was developed and tested using:

| Component | Version |
|---|---|
| Operating System | Windows |
| Python | 3.11.9 |
| Apache Spark | 3.5.6 |
| Java | Eclipse Temurin JDK 8 (8u502) |
| Requests | 2.34.2 |
| Warcio | 1.8.2 |
| PyArrow | 26.0.0 |
| Pandas | 3.1.0 |
| psutil | 7.2.2 |
| tqdm | 4.70.1 |

Install the required Python dependencies using:

```powershell
python -m pip install -r requirements.txt
```

Verify the installation:

```powershell
python --version
java -version
python -m pip check
```

## 4. Dataset Acquisition and Extraction

The dataset download script is:

`scripts/download_dataset.py`

Run it from the project root:

```powershell
python scripts/download_dataset.py
```

The script downloads the selected Common Crawl WET segment into:

`data/raw/`

If the dataset file already exists, the script skips downloading it again.

The extraction script is:

`src/extract_wet.py`

Run:

```powershell
python src/extract_wet.py
```

The extracted JSONL dataset is stored at:

`data/sample/wet_documents.jsonl`

The extraction is limited to a maximum of 10,000 documents for the initial experiment.

## 5. Pipeline Execution

The complete pipeline is orchestrated through:

`src/run_pipeline.py`

Execute all stages from the project root:

```powershell
python src/run_pipeline.py
```

The pipeline executes the following stages sequentially:

### Stage 1: Data Ingestion

File: `src/ingestion.py`

- Reads the extracted JSONL dataset.
- Uses Apache Spark in local mode with two worker threads (`local[2]`) for data processing.
- Records the ingestion document count and execution metrics.

### Stage 2: Deduplication

File: `src/deduplication.py`

- Normalizes document text.
- Generates content hashes.
- Removes exact duplicate documents.
- Retains one representative document for each duplicate group.

### Stage 3: Quality Filtering

File: `src/quality_filter.py`

- Removes documents that do not satisfy the configured quality criteria.
- Applies minimum character and word-count checks.
- Applies an ASCII alphabetic-character ratio threshold.
- Records document removal statistics.

### Stage 4: PII Detection and Redaction

File: `src/pii_filter.py`

- Detects email-address patterns.
- Detects phone-number-like patterns.
- Replaces detected values with redaction placeholders.
- Records detection statistics without storing the detected raw values in the metrics.

## 6. Output Directories

The pipeline uses the following directories:

| Directory | Purpose |
|---|---|
| `data/raw/` | Downloaded Common Crawl WET file |
| `data/sample/` | Extracted JSONL sample |
| `data/processed/` | Intermediate and final processed datasets |
| `results/` | Pipeline metrics and experiment results |
| `reports/` | Documentation and handoff information |
| `tests/` | Automated unit tests |

The raw, sample, and processed dataset files are kept locally and are not included in the Git repository.

## 7. Pipeline Results

The latest successful execution processed 10,000 extracted documents.

| Stage | Documents |
|---|---:|
| Initial ingestion | 10,000 |
| After deduplication | 9,833 |
| After quality filtering | 6,996 |
| After PII processing | 6,996 |

### Deduplication

- Duplicate copies removed: 167
- Duplicate percentage: 1.67%
- The implementation performs exact normalized-text deduplication, not semantic or near-duplicate detection.

### Quality Filtering

- Documents removed: 2,837
- Removal percentage: 28.85%

The recorded removal categories include:

- Short documents: 335
- Low word-count documents: 35
- Low ASCII alphabetic-ratio documents: 2,467

These are heuristic filters and may disproportionately exclude non-English or non-Latin content.

### PII Processing

The recorded pattern detections include:

- Documents containing email patterns: 2,046
- Documents containing phone-like patterns: 1,206

These categories may overlap. Detected values are replaced with placeholders before the processed output is saved.

## 8. Pipeline Validation and Testing

The validation script is:

`src/validate_pipeline.py`

Run:

```powershell
python src/validate_pipeline.py
```

The latest validation confirmed:

- Ingestion output contains 10,000 documents.
- Deduplication output contains 9,833 documents.
- No duplicate content hashes remain after deduplication.
- Quality-filtered output contains 6,996 documents.
- PII-processed output contains 6,996 documents.
- No null text values were found in the final output.
- No email or phone patterns detected by the configured regex checks remained in the final output.

Automated unit tests are located in:

`tests/test_pii_patterns.py`

Run:

```powershell
python -m unittest discover -s tests -v
```

The six PII pattern tests passed in the latest recorded test run.

## 9. Performance Benchmarking

The performance benchmark is implemented in:

`src/performance_test.py`

It measures local Spark JSON read-and-count performance at different dataset sizes.

The benchmark uses a warm-up run followed by three measured runs for each input size. Median execution time and throughput are recorded.

| Input documents | Median execution time | Throughput |
|---:|---:|---:|
| 2,500 | 0.5165 seconds | 4,840.16 docs/sec |
| 5,000 | 0.6004 seconds | 8,327.47 docs/sec |
| 10,000 | 0.7429 seconds | 13,460.71 docs/sec |

These measurements represent a local Spark read-and-count benchmark. They should not be interpreted as the throughput of the complete curation pipeline or a distributed production cluster.

## 10. Pipeline Runtime and Cost Estimation

The latest recorded pipeline execution times were:

| Stage | Wall-clock time |
|---|---:|
| Ingestion | 25.66 seconds |
| Deduplication | 34.64 seconds |
| Quality filtering | 33.43 seconds |
| PII processing | 23.40 seconds |
| Total | 117.13 seconds |

The runtime measurements are collected by the pipeline orchestrator.

The cost-estimation script is:

`src/cost_estimation.py`

The estimate uses the following reference assumptions:

| Metric | Value |
|---|---|
| Reference instance | t3.medium |
| Reference region | ap-south-1 |
| Assumed hourly rate | USD 0.0448 |
| Pipeline runtime | 117.1265 seconds |
| Pipeline runtime in hours | 0.03253514 |
| Input documents | 10,000 |
| Estimated compute cost | USD 0.00145757 |
| Estimated cost per 1,000 input documents | USD 0.00014576 |

This is an illustrative cloud-equivalent compute estimate, not an actual cloud bill. It assumes the same runtime on the reference instance and excludes storage, network transfer, taxes, and other cloud services.

## 11. Consolidated Results

The consolidated metrics are generated using:

`src/collect_results.py`

Run:

```powershell
python src/collect_results.py
```

The script combines the available metrics into:

`results/pipeline_summary.csv`

The consolidated results include:

- Ingestion metrics
- Deduplication metrics
- Quality-filtering metrics
- PII metrics
- Performance benchmark metrics
- Pipeline execution metrics
- Cost estimation metrics

The latest generated summary contains 51 metric rows across seven categories.

## 12. Limitations and Responsible Data Considerations

The current implementation has the following limitations:

1. The initial experiment uses one Common Crawl WET segment and a maximum of 10,000 extracted documents.
2. Deduplication is based on exact normalized-text matching and does not identify semantic near-duplicates.
3. Quality filtering relies on heuristic thresholds. These may not be suitable for every language or content type.
4. The ASCII alphabetic-ratio filter may disproportionately remove non-English and non-Latin content.
5. PII detection uses regular expressions and cannot guarantee detection of every type or representation of personal information.
6. The validation checks use the configured patterns and do not establish that all possible PII has been removed.
7. Performance results were measured locally and are not distributed-cluster benchmarks.
8. Cost figures are illustrative estimates rather than actual cloud expenditure.
9. Common Crawl availability does not imply that every collected page has the same reuse licence. Source-level licensing must be considered before redistribution or reuse.

## 13. Source Code Reference

| File | Responsibility |
|---|---|
| `scripts/download_dataset.py` | Downloads the selected Common Crawl segment |
| `src/extract_wet.py` | Extracts documents from the WET file |
| `src/ingestion.py` | Spark-based dataset ingestion |
| `src/deduplication.py` | Exact duplicate detection and removal |
| `src/quality_filter.py` | Content quality filtering |
| `src/pii_filter.py` | PII detection and redaction |
| `src/pii_patterns.py` | PII regular expressions and placeholders |
| `src/run_pipeline.py` | Sequential pipeline orchestration |
| `src/validate_pipeline.py` | Output validation |
| `src/performance_test.py` | Local Spark performance benchmarking |
| `src/cost_estimation.py` | Illustrative compute cost estimation |
| `src/collect_results.py` | Consolidation of experiment metrics |
| `tests/test_pii_patterns.py` | Automated PII pattern tests |

---

**End of Pipeline Handoff Documentation**