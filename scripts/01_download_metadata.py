#!/usr/bin/env python3
"""
Sprint 1 — Step 1: Download ASLLVD metadata from Boston University.

Downloads the Excel metadata file containing all ASL sign annotations:
gloss labels, session/scene info, frame boundaries, handshapes, etc.

Output: data/raw/asllvd_metadata.xlsx
"""

import os
import sys
import requests
from pathlib import Path

METADATA_URL = "http://www.bu.edu/asllrp/dai-asllvd-BU_glossing_with_variations_HS_information-extended-urls-RU.xlsx"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "asllvd_metadata.xlsx"


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if OUTPUT_FILE.exists():
        print(f"✅ Metadata already exists: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size} bytes)")
        return
    
    print(f"⬇️  Downloading ASLLVD metadata from BU...")
    print(f"   URL: {METADATA_URL}")
    
    response = requests.get(METADATA_URL, stream=True, timeout=60)
    response.raise_for_status()
    
    total = int(response.headers.get("content-length", 0))
    downloaded = 0
    
    with open(OUTPUT_FILE, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                pct = (downloaded / total) * 100
                sys.stdout.write(f"\r   {downloaded}/{total} bytes ({pct:.1f}%)")
                sys.stdout.flush()
    
    print(f"\n✅ Downloaded: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size} bytes)")


if __name__ == "__main__":
    main()