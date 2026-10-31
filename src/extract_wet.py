
import gzip
import json
from pathlib import Path
from urllib.parse import urlsplit
from warcio.archiveiterator import ArchiveIterator

INPUT_DIR = Path("data/raw")
OUTPUT_DIR = Path("data/sample")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "wet_documents.jsonl"

wet_files = list(INPUT_DIR.glob("*.warc.wet.gz"))

if not wet_files:
    raise FileNotFoundError("No Common Crawl WET file found.")

input_file = wet_files[0]

MAX_DOCUMENTS = 10000

total_records = 0
extracted_documents = 0
invalid_records = 0

print("Reading WET archive:", input_file.name)

with gzip.open(input_file, "rb") as stream:
    with OUTPUT_FILE.open("w", encoding="utf-8") as output:

        for record in ArchiveIterator(stream):

            total_records += 1

            if record.rec_type != "conversion":
                continue

            try:
                raw_text = record.content_stream().read()

                text = raw_text.decode(
                    "utf-8", errors="replace"
                ).strip()

                if not text:
                    invalid_records += 1
                    continue

                target_url = record.rec_headers.get_header(
                    "WARC-Target-URI"
                )

                domain = ""

                if target_url:
                    domain = urlsplit(target_url).hostname or ""

                crawl_date = record.rec_headers.get_header(
                    "WARC-Date"
                )

                document = {
                    "doc_id": extracted_documents + 1,
                    "domain": domain,
                    "crawl_date": crawl_date,
                    "text": text
                }

                output.write(
                    json.dumps(document, ensure_ascii=False) + "\n"
                )

                extracted_documents += 1

                if extracted_documents % 1000 == 0:
                    print(
                        f"Extracted {extracted_documents} documents..."
                    )

                if extracted_documents >= MAX_DOCUMENTS:
                    break

            except Exception:
                invalid_records += 1
                continue

print("\n========== EXTRACTION SUMMARY ==========")
print("Total WARC records scanned:", total_records)
print("Documents extracted:", extracted_documents)
print("Invalid or empty records:", invalid_records)
print("Output file:", OUTPUT_FILE)
print("Output file exists:", OUTPUT_FILE.exists())
print("========================================")
