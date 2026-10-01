#!/usr/bin/env python3
"""
Sprint 1 — Step 3: Download ASLLVD sign videos from BU FTP.

Downloads .mov files for each session/scene in the cleaned metadata.
Videos are at: http://csr.bu.edu/ftp/asl/asllvd/asl-data2/quicktime/{session}/scene{scene}-camera1.mov

We only need camera1 (front-facing) for pose extraction.

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
MAX_WORKERS = 4  # Be nice to BU's server
RETRY_COUNT = 3
TIMEOUT = 120


def download_video(session: str, scene: int, output_dir: Path) -> tuple[str, str, bool, str]:
    """Download a single sign video. Returns (session, scene, success, message)."""
    session_dir = output_dir / session
    filename = f"scene{scene}-camera1.mov"
    filepath = session_dir / filename
    
    if filepath.exists() and filepath.stat().st_size > 1000:
        return (session, scene, True, f"already exists ({filepath.stat().st_size} bytes)")
    
    session_dir.mkdir(parents=True, exist_ok=True)
    url = f"{BASE_URL}/{session}/{filename}"
    
    for attempt in range(RETRY_COUNT):
        try:
            response = requests.get(url, stream=True, timeout=TIMEOUT)
            if response.status_code == 404:
                return (session, scene, False, f"404 not found at {url}")
            response.raise_for_status()
            
            with open(filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    f.write(chunk)
            
            size_mb = filepath.stat().st_size / (1024 * 1024)
            return (session, scene, True, f"downloaded ({size_mb:.1f} MB)")
            
        except Exception as e:
            if attempt < RETRY_COUNT - 1:
                time.sleep(2 ** attempt)
            else:
                return (session, scene, False, f"error: {e}")
    
    return (session, scene, False, "max retries exceeded")


def main():
    if not METADATA_CSV.exists():
        print(f"❌ Metadata CSV not found: {METADATA_CSV}")
        print("   Run 02_clean_metadata.py first.")
        return
    
    df = pd.read_csv(METADATA_CSV)
    
    # Get unique session-scene pairs (many glosses share the same video)
    unique_videos = df[["session", "scene"]].drop_duplicates()
    total = len(unique_videos)
    
    print(f"🎬 ASLLVD Video Downloader")
    print(f"   {total} unique videos to download")
    print(f"   Output: {OUTPUT_DIR}")
    print(f"   Workers: {MAX_WORKERS}")
    print()
    
    # Check what's already downloaded
    existing = 0
    to_download = []
    for _, row in unique_videos.iterrows():
        session = str(row["session"])
        scene = int(row["scene"])
        filepath = OUTPUT_DIR / session / f"scene{scene}-camera1.mov"
        if filepath.exists() and filepath.stat().st_size > 1000:
            existing += 1
        else:
            to_download.append((session, scene))
    
    if existing > 0:
        print(f"   {existing} already downloaded, {len(to_download)} remaining")
    
    if not to_download:
        print("✅ All videos already downloaded!")
        return
    
    # Download with thread pool
    success_count = 0
    fail_count = 0
    failed_list = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(download_video, session, scene, OUTPUT_DIR): (session, scene)
            for session, scene in to_download
        }
        
        for i, future in enumerate(as_completed(futures), 1):
            session, scene = futures[future]
            result = future.result()
            status = "✅" if result[2] else "❌"
            
            if result[2]:
                success_count += 1
            else:
                fail_count += 1
                failed_list.append(f"  {result[0]}/scene{result[1]}: {result[3]}")
            
            if i % 10 == 0 or i == len(to_download):
                print(f"   [{i}/{len(to_download)}] ✅ {success_count} ❌ {fail_count}")
    
    print(f"\n📊 Results: {success_count} downloaded, {fail_count} failed, {existing} already existed")
    
    if failed_list:
        print(f"\n❌ Failed downloads:")
        for f in failed_list[:20]:
            print(f)
        if len(failed_list) > 20:
            print(f"  ... and {len(failed_list) - 20} more")
    
    # Save failed list for retry
    if failed_list:
        fail_file = OUTPUT_DIR / "failed_downloads.txt"
        with open(fail_file, "w") as f:
            for line in failed_list:
                f.write(line + "\n")
        print(f"   Failed list saved to: {fail_file}")


if __name__ == "__main__":
    main()