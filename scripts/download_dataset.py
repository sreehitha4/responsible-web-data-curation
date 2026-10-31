
import requests
from pathlib import Path

# Resolve all paths relative to the project directory.
ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "data" / "raw"

# Selected Common Crawl WET segment from CC-MAIN-2026-43.
SEGMENT_URL = (
    "https://data.commoncrawl.org/crawl-data/"
    "CC-MAIN-2026-43/segments/1791170053823.21/wet/"
    "CC-MAIN-20261005105623-20261005135623-00000.warc.wet.gz"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

filename = SEGMENT_URL.rsplit("/", 1)[-1]
output_file = OUTPUT_DIR / filename
partial_file = OUTPUT_DIR / f"{filename}.part"
metadata_file = OUTPUT_DIR / "dataset_source.txt"

print("Common Crawl WET Dataset Downloader")
print("=" * 55)
print("Collection: CC-MAIN-2026-43")
print("Source:", SEGMENT_URL)

try:
    if output_file.exists() and output_file.stat().st_size > 0:
        print("\nDataset already exists.")
        print("Using:", output_file)

    else:
        print("\nStarting dataset download...")

        downloaded_bytes = 0

        with requests.get(
            SEGMENT_URL,
            stream=True,
            timeout=(30, 120)
        ) as response:

            response.raise_for_status()

            with partial_file.open("wb") as file:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        file.write(chunk)
                        downloaded_bytes += len(chunk)

        # Rename only after the download finishes successfully.
        partial_file.replace(output_file)

        print("\nDownload completed successfully!")
        print(
            f"Downloaded size: "
            f"{downloaded_bytes / (1024 * 1024):.2f} MB"
        )

    # Save local dataset provenance for reference.
    metadata_file.write_text(
        "Dataset: Common Crawl\n"
        "Collection: CC-MAIN-2026-43\n"
        f"Segment URL: {SEGMENT_URL}\n"
        f"Local file: {filename}\n",
        encoding="utf-8"
    )

    print("Dataset file:", output_file)
    print("Metadata file:", metadata_file)
    print("File size:", output_file.stat().st_size, "bytes")

except Exception:
    # Remove an incomplete download if an error occurs.
    if partial_file.exists():
        partial_file.unlink()

    raise
