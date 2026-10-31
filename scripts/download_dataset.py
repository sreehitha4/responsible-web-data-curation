
import requests
from pathlib import Path

# Read the selected segment from our saved metadata
metadata_file = Path("data/raw/dataset_source.txt")

metadata = metadata_file.read_text(encoding="utf-8")

segment_url = next(
    line.split(": ", 1)[1]
    for line in metadata.splitlines()
    if line.startswith("Segment URL:")
)

output_dir = Path("data/raw")
output_dir.mkdir(parents=True, exist_ok=True)

filename = segment_url.rsplit("/", 1)[-1]
output_file = output_dir / filename

print("Starting Common Crawl WET download...")
print("Source:", segment_url)

response = requests.get(
    segment_url,
    stream=True,
    timeout=(30, 120)
)
response.raise_for_status()

downloaded_bytes = 0

try:
    with output_file.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                file.write(chunk)
                downloaded_bytes += len(chunk)

finally:
    response.close()

print("\nDownload completed successfully!")
print("Saved at:", output_file)
print(f"Downloaded size: {downloaded_bytes / (1024 * 1024):.2f} MB")
print("File exists:", output_file.exists())
