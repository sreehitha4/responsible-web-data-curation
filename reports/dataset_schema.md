# Dataset Schema and Processing Details

## 1. Dataset Source

The dataset was obtained from a single WET segment of the
Common Crawl collection CC-MAIN-2026-43.

A sample of 10,000 text documents was extracted for this project.
The extracted records were stored in JSONL format before being
processed using Apache Spark.

The pipeline uses only the extracted text and limited metadata.
Full source URLs are not retained in the extracted records.

## 2. Ingestion Schema

The ingestion stage contains the following fields:

| Column | Description |
|---|---|
| doc_id | Identifier assigned to an extracted document |
| domain | Hostname associated with the source document |
| crawl_date | Crawl date associated with the document |
| text | Extracted textual content |

Initial document count: 10,000.

## 3. Processed Dataset Schema

After deduplication, the processed datasets contain:

| Column | Description |
|---|---|
| doc_id | Document identifier |
| domain | Source hostname |
| crawl_date | Crawl date |
| text | Document text |
| content_hash | SHA-256 hash of normalized text, used for exact deduplication |

The `content_hash` field is retained in subsequent processing stages
to support validation and traceability of duplicate removal.

## 4. Processing Stages and Record Counts

| Processing stage | Documents |
|---|---:|
| Initial ingestion | 10,000 |
| After deduplication | 9,833 |
| After quality filtering | 6,996 |
| After PII detection and redaction | 6,996 |

## 5. Data Handling

- Duplicate documents are identified using normalized text hashes.
- Quality filtering removes empty, short, low-word-count, and
  low-alphabetic-ratio documents.
- Email and phone-like patterns are replaced with redaction
  placeholders.
- Raw PII values are not written to the metrics output.
- The raw Common Crawl segment and intermediate data files are
  excluded from Git tracking.

## 6. Limitations

- Deduplication identifies exact duplicates after normalization;
  it does not perform semantic or near-duplicate detection.
- The alphabetic-ratio filter is based on ASCII characters and may
  disproportionately exclude non-English or non-Latin-script content.
- PII detection uses regular expressions and cannot guarantee
  detection of every possible personal-information pattern.
- The experiment uses a 10,000-document sample from one Common Crawl
  segment. Results should not be interpreted as a full web-scale
  deployment.
- Common Crawl availability does not imply that every crawled page
  has the same copyright or reuse licence.