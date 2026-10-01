#!/usr/bin/env python3
"""
Sprint 1 — Step 3b: Download TOP-N most common ASL gloss videos only.

Instead of downloading all 952 videos (~143GB), downloads only the videos
needed for the most common N glosses. This covers ~80% of conversational ASL
while keeping disk usage manageable for the POC.

Output: data/raw/videos/{session}/scene{scene}-camera1.mov
"""

import os
import sys
import time
import requests
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "http://csr.bu.edu/ftp/asl/asllvd/asl-data2/quicktime"
METADATA_CSV = Path(__file__).parent.parent / "data" / "processed" / "asllvd_clean.csv"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "videos"
MAX_WORKERS = 4
RETRY_COUNT = 3
TIMEOUT = 120
TOP_N = 500  # Number of most common glosses to download


def download_video(session: str, scene: int, output_dir: Path) -> tuple:
    """Download a single sign video."""
    session_dir = output_dir / session
    filename = f"scene{scene}-camera1.mov"
    filepath = session_dir / filename
    
    if filepath.exists() and filepath.stat().st_size > 1000:
        return (session, scene, True, "exists")
    
    session_dir.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{session}/{filename}"
    
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT)
            if response.status_code == 404:
                return (session, scene, False, "404")
            response.raise_for_status()
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    f.write(chunk)
            
            return (session, scene, True, f"{filepath.stat().st_size / 1024 / 1024:.1f}MB")
        except Exception as e:
            if attempt < RETRY_COUNT - 1:
                time.sleep(2 ** attempt)
            else:
                return (session, scene, False, str(e))
    
    return (session, scene, False, "retries exceeded")


def main():
    df = pd.read_csv(METADATA_CSV)
    
    # Count how many times each gloss appears (more appearances = more common)
    gloss_counts = df["gloss"].value_counts()
    top_glosses = set(gloss_counts.head(TOP_N).index)
    
    # Filter metadata to only top glosses
    top_df = df[df["gloss"].isin(top_glosses)]
    unique_videos = top_df[["session", "scene"]].drop_duplicates()
    
    # Check what's already downloaded
    to_download = []
    existing = 0
    for _, row in unique_videos.iterrows():
        session = str(row["session"])
        scene = int(row["scene"])
        filepath = OUTPUT_DIR / session / f"scene{scene}-camera1.mov"
        if filepath.exists() and filepath.stat().st_size > 1000:
            existing += 1
        else:
            to_download.append((session, scene))
    
    print(f"🎬 ASLLVD Top-{TOP_N} Gloss Video Downloader")
    print(f"   {len(top_glosses)} glosses → {len(unique_videos)} unique videos needed")
    print(f"   {existing} already downloaded, {len(to_download)} remaining")
    print()
    
    if not to_download:
        print("✅ All needed videos already downloaded!")
        return
    
    # Estimate size
    existing_sizes = []
    for _, row in unique_videos.iterrows():
        session = str(row["session"])
        scene = int(row["scene"])
        filepath = OUTPUT_DIR / session / f"scene{scene}-camera1.mov"
        if filepath.exists() and filepath.stat().st_size > 1000:
            existing_sizes.append(filepath.stat().st_size)
    
    if existing_sizes:
        avg_mb = sum(existing_sizes) / len(existing_sizes) / (1024 * 1024)
        est_total_gb = avg_mb * len(unique_videos) / 1024
        est_remaining_gb = avg_mb * len(to_download) / 1024
        print(f"   Avg video size: {avg_mb:.1f} MB")
        print(f"   Est. total size: {est_total_gb:.1f} GB")
        print(f"   Est. remaining: {est_remaining_gb:.1f} GB")
        print()
    
    # Download
    success_count = 0
    fail_count = 0
    failed_list = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_video, session, scene, OUTPUT_DIR): (session, scene)
            for session, scene in to_download
        }
        
        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result[2]:
                success_count += 1
            else:
                fail_count += 1
                failed_list.append(f"  {result[0]}/scene{result[1]}: {result[3]}")
            
            if i % 10 == 0 or i == len(to_download):
                print(f"   [{i}/{len(to_download)}] ✅ {success_count} ❌ {fail_count}")
    
    print(f"\n📊 Results: {success_count} downloaded, {fail_count} failed, {existing} already existed")
    
    if failed_list:
        fail_file = OUTPUT_DIR / "failed_downloads_top500.txt"
        with open(fail_file, "w") as f:
            for line in failed_list:
                f.write(line + "\n")
        print(f"   Failed list: {fail_file}")


if __name__ == "__main__":
    main()