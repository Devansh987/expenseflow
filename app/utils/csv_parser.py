"""
CSV Parsing utilities.

Safely reads and standardizes CSV rows before they hit the anomaly engine.
"""

import csv
import io
from typing import Iterator


def parse_csv_file(file_content: bytes) -> list[dict]:
    """
    Decodes a raw CSV file byte stream and parses it into a list of dictionaries.
    Strips whitespace from headers and values to prevent common import errors.
    """
    try:
        text = file_content.decode("utf-8-sig")  # utf-8-sig removes BOM if present
    except UnicodeDecodeError:
        # Fallback to latin-1 if utf-8 fails (common for Excel CSV exports)
        text = file_content.decode("latin-1")

    # Use io.StringIO to treat the string as a file object
    f = io.StringIO(text)
    
    # Use DictReader to automatically map headers to values
    reader = csv.DictReader(f)
    
    if not reader.fieldnames:
        raise ValueError("CSV file appears to be empty or missing headers.")

    # Clean headers: lowercase, strip whitespace, replace spaces with underscores
    cleaned_headers = [str(h).strip().lower().replace(" ", "_") for h in reader.fieldnames]
    reader.fieldnames = cleaned_headers

    parsed_rows = []
    for row in reader:
        # Clean values: strip whitespace, handle empty strings
        cleaned_row = {
            k: (v.strip() if isinstance(v, str) and v.strip() else None)
            for k, v in row.items()
        }
        parsed_rows.append(cleaned_row)

    return parsed_rows
