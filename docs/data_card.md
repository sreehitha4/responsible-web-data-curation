# Data Card – Responsible Web-Scale Data Curation

## 1. Dataset Information

| Field | Description |
|---|---|
| Dataset Name | Responsible Web-Scale Training Corpus |
| Project | Responsible Web-Scale Data Curation |
| Dataset Type | Text-based web dataset |
| Data Source | Common Crawl |
| Crawl Collection | CC-MAIN-2026-43 |
| Input Format | WET archive |
| Intermediate Format | JSONL |
| Processed Format | Apache Parquet |
| Processing Engine | Apache Spark 3.5.6 |
| Evaluation Model | unitary/toxic-bert |
| Responsible Member | Member 1 – Data Collection and Processing |
| Evaluation Member | Member 2 – Toxicity and Fairness Evaluation |

## 2. Dataset Purpose

The dataset supports the preparation of a high-quality, privacy-aware and responsibly filtered web training corpus.

The project applies data processing and filtering techniques to identify and handle duplicate, low-quality, privacy-sensitive and potentially toxic content.

The objective is to retain useful text documents while reducing potentially harmful content and examining possible representation differences introduced by automated filtering.

## 3. Data Source and Collection

The dataset was collected from the Common Crawl web archive.

| Collection Detail | Value |
|---|---|
| Common Crawl collection | CC-MAIN-2026-43 |
| Archive type | WET |
| Maximum documents extracted | 10,000 |
| Extracted documents | 10,000 |
| Invalid or empty records | 0 |
| Extraction output | data/sample/wet_documents.jsonl |

The extraction process uses the `warcio` library to read WET records and extract textual content.

The source metadata includes document identifiers, website domains and crawl timestamps.

## 4. Dataset Schema

The processed dataset contains the following attributes:

| Attribute | Description |
|---|---|
| doc_id | Identifier assigned to each extracted document |
| domain | Source website domain |
| crawl_date | Original crawl timestamp |
| text | Extracted and processed document text |
| content_hash | SHA-256 content hash used during deduplication |
| toxicity_score | Toxic-BERT predicted toxicity score |
| toxicity_label | Classification based on the configured threshold |
| retained | Boolean indicating whether the document passed toxicity filtering |

Topic labels, manually verified toxicity labels and language-variety labels are not present in the original Common Crawl records. Language categories used in descriptive analysis are inferred separately.

## 5. Data Collection and Processing Pipeline

The dataset passes through the following stages:

1. **Data Collection:** Extract up to 10,000 text documents from the Common Crawl WET archive.
2. **Spark Ingestion:** Read the extracted JSONL records and store them in Parquet format.
3. **Deduplication:** Normalize document text, calculate SHA-256 hashes and remove exact duplicates.
4. **Quality Filtering:** Remove empty, short, low-word-count and low-alphabetic-ratio documents.
5. **PII Detection and Redaction:** Identify email addresses and phone-number patterns and redact detected values.
6. **Toxicity Filtering:** Apply the pretrained Toxic-BERT model to generate document-level scores and filtering decisions.
7. **Fairness Analysis:** Examine descriptive toxicity removal and retention rates across detected language groups and, after topic classification, topic categories.

## 6. Actual Dataset Processing Statistics

The following statistics were obtained from the executed processing pipeline.

| Processing Stage | Input Documents | Output Documents | Removed |
|---|---:|---:|---:|
| Extraction | — | 10,000 | — |
| Deduplication | 10,000 | 9,833 | 167 |
| Quality filtering | 9,833 | 6,996 | 2,837 |
| PII redaction | 6,996 | 6,996 | 0 |
| Toxicity filtering | 6,996 | 6,879 | 117 |

### Quality Filtering Details

The quality filtering stage applies the following rules:

- Remove null or empty text.
- Require at least 200 characters.
- Require at least 30 words.
- Require at least 50% ASCII alphabetic characters.

A total of 2,837 documents were removed, representing approximately 28.85% of the deduplicated dataset.

The ASCII alphabetic-character requirement may disproportionately exclude non-Latin scripts. This is an important limitation of the quality-filtering approach.

### PII Processing Details

Regex-based detection identified:

- Documents containing email patterns: 2,046.
- Documents containing phone patterns: 1,206.

These counts may overlap because a document can contain both patterns.

The PII stage redacted detected patterns without removing documents. Regex detection cannot guarantee identification of every instance of personal information.

### Toxicity Filtering Details

| Metric | Result |
|---|---:|
| Model | unitary/toxic-bert |
| Threshold | 0.50 |
| Input documents | 6,996 |
| Flagged documents | 117 |
| Retained documents | 6,879 |
| Removal rate | 1.67% |
| Retention rate | 98.33% |
| Mean toxicity score | 0.04203 |
| Execution time | 3,019.96 seconds |
| Throughput | 2.32 documents/second |

The final toxicity-scored dataset contains all 6,996 input records with their toxicity scores and filtering decisions. The 6,879 retained documents represent the subset passing the configured toxicity threshold.

## 7. Data Quality Considerations

The project considers the following quality dimensions:

- **Completeness:** Checks for missing and empty document content.
- **Uniqueness:** Uses exact text hashing to remove duplicate documents.
- **Consistency:** Maintains a structured schema across processing stages.
- **Relevance:** Applies minimum text-length and word-count requirements.
- **Privacy:** Detects and redacts selected PII patterns.
- **Safety:** Uses a pretrained toxicity classifier to screen potentially harmful content.

The deduplication implementation identifies exact duplicates, not all semantic or near-duplicate documents.

## 8. Privacy and Ethical Considerations

Web-collected text may contain personal information or sensitive content.

The project uses the following safeguards:

- Regex-based email and phone-number detection.
- Redaction of detected patterns.
- Toxicity screening of processed documents.
- Documentation of automated filtering limitations.
- Preservation of filtering decisions for inspection.

PII redaction is not comprehensive, and residual personal information may remain.

The project supports responsible dataset preparation rather than unrestricted collection or reuse of personal information.

## 9. Fairness and Representation Considerations

Automated filtering may affect different topics and language groups differently.

The project examines:

**Topic categories planned for analysis:**
- News and current affairs.
- Education and learning.
- Technology and programming.
- Health and wellbeing.
- Politics and public policy.
- Entertainment and culture.
- General discussion.

**Detected language groups:**

Language identification is performed using the `langdetect` library. Actual removal and retention rates are calculated for detected language groups.

The language identification output represents predicted language categories, not manually verified labels or English dialect classifications.

Language-variety fairness evaluation requires a separate manually labelled sample containing ground-truth toxicity labels.

Removal-rate differences alone do not establish discrimination or model bias.

## 10. Dataset Limitations

The dataset and processing pipeline have several limitations:

- The dataset represents a limited sample of Common Crawl rather than the entire web.
- Web documents may contain incomplete or inaccurate information.
- Exact hashing does not detect every near-duplicate document.
- ASCII-based quality filtering may disadvantage non-Latin scripts.
- Regex-based PII detection may miss some personal information.
- Toxic-BERT may generate false positives and false negatives.
- Toxicity inference is limited to 512 tokens per document in the current implementation.
- Language identification may be inaccurate, particularly for short or multilingual documents.
- Topic labels require a separate classification step.
- Ground-truth toxicity labels are unavailable for the complete corpus.
- Small language-group sample sizes limit reliable comparisons.
- Automated filtering cannot guarantee a completely safe or unbiased dataset.

## 11. Dataset Availability and Reproducibility

The project stores intermediate and final datasets in Parquet format.

Important dataset paths include:

- `data/sample/wet_documents.jsonl`
- `data/processed/ingested_parquet`
- `data/processed/deduplicated_parquet`
- `data/processed/quality_filtered_parquet`
- `data/processed/pii_redacted_parquet`
- `data/processed/toxicity_scored_parquet`

The results directory contains CSV metrics generated by individual pipeline stages.

Raw archives, intermediate datasets and processed Parquet outputs are maintained locally and should not automatically be committed to GitHub.

## 12. Dataset Evaluation Status

| Component | Status |
|---|---|
| Common Crawl extraction | Completed |
| Spark ingestion | Completed |
| Deduplication | Completed |
| Quality filtering | Completed |
| PII detection and redaction | Completed |
| Toxicity filtering | Completed |
| Actual dataset statistics | Recorded |
| Language-wise descriptive analysis | Completed |
| Topic-wise fairness analysis | Pending |
| Manually labelled language-variety evaluation | Pending |
| Final integrated pipeline validation | Pending |

## 13. Conclusion

This Data Card documents the source, structure, processing stages, dataset composition, privacy safeguards, toxicity filtering results and fairness considerations of the Responsible Web-Scale Training Corpus.

The current pipeline processed 10,000 extracted Common Crawl documents and produced 6,879 documents that passed all implemented filtering stages.

Further topic classification, manually labelled fairness evaluation and final integrated pipeline validation are required before making broader claims about dataset representation, model accuracy or fairness.

---

*Data Card Status: Updated preliminary version based on actual Common Crawl processing and toxicity evaluation results.*