# Processed Dataset Schema

## Project
Responsible Web-Scale Data Curation

## Dataset source
Common Crawl WET — CC-MAIN-2026-43

## Final processed dataset
`data/processed/pii_redacted_parquet/`

## Dataset description
The dataset contains web text documents extracted from a Common Crawl WET segment. It has undergone exact normalized-text deduplication, heuristic quality filtering, and baseline regex-based PII detection and redaction.

## Schema

| Column | Data type | Description |
|---|---|---|
| doc_id | Integer | Document identifier assigned during extraction |
| domain | String | Hostname associated with the source document |
| crawl_date | String | Crawl timestamp |
| text | String | Processed text after filtering and redaction |

## Processing summary

- Documents extracted: 10,000
- Documents after deduplication: 9,833
- Documents after quality filtering: 6,996
- Documents after PII redaction: 6,996

## Privacy considerations

Email-like and phone-number-like patterns are detected and replaced using regular expressions. This baseline approach does not guarantee complete PII removal.

Raw and intermediate datasets should not be distributed as part of the public repository. The final dataset should be reviewed before external sharing.

## Known limitations

- Exact normalized-text deduplication is used; near-duplicate detection is not implemented.
- Quality filtering uses heuristic thresholds.
- The alphabetic-ratio filter may disproportionately exclude non-English and non-Latin-script content.
- Regex-based PII detection can produce false positives and false negatives.
- Performance measurements were collected using local Spark execution in `local[2]` mode, not a distributed production cluster.