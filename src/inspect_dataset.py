
import gzip
import requests
from pathlib import Path

CRAWL_ID = "CC-MAIN-2026-43"

BASE_URL = "https://data.commoncrawl.org"
INDEX_URL = (
    f"{BASE_URL}/crawl-data/{CRAWL_ID}/wet.paths.gz"
)

OUTPUT_DIR = Path("data/raw")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

INDEX_FILE = OUTPUT_DIR / "wet.paths.gz"

print("Downloading Common Crawl WET file index...")

response = requests.get(INDEX_URL, timeout=60)
response.raise_for_status()

INDEX_FILE.write_bytes(response.content)

print("WET index downloaded successfully.")

# Read the first five WET segment paths
with gzip.open(INDEX_FILE, "rt", encoding="utf-8") as file:
    paths = [line.strip() for _, line in zip(range(5), file)]

print("\nAvailable WET segments:")

for index, path in enumerate(paths, start=1):
    print(f"{index}. {path}")

# Inspect the first segment's size
selected_path = paths[0]
segment_url = f"{BASE_URL}/{selected_path}"

print("\nInspecting first segment...")

head = requests.head(segment_url, timeout=60)
head.raise_for_status()

size_bytes = int(head.headers.get("Content-Length", 0))

print("Selected segment:", selected_path)
print("Download URL:", segment_url)
print(f"Compressed size: {size_bytes / (1024 * 1024):.2f} MB")

# Save selection metadata
metadata = OUTPUT_DIR / "dataset_source.txt"

metadata.write_text(
    f"Crawl ID: {CRAWL_ID}\n"
    f"Dataset: Common Crawl WET\n"
    f"Index URL: {INDEX_URL}\n"
    f"Selected segment: {selected_path}\n"
    f"Segment URL: {segment_url}\n"
    f"Compressed size: {size_bytes} bytes\n",
    encoding="utf-8"
)

print("\nDataset source metadata saved.")
