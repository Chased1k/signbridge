#!/usr/bin/env python3
"""
Sprint 1 — Step 3c: Download SLIM ASLLVD dataset (1 signer per gloss).

Downloads only one video per gloss (best available signer), covering all
2,746 glosses with ~547 unique videos instead of 952.

Preferred signer order: Liz, Brady (most entries, cleanest data).

Output: data/raw/videos/{session}/scene{scene}-camera1.mov
Output: data/processed/gloss_video_map.csv (gloss → video file mapping)
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
MAP_FILE = Path(__file__).parent.parent / "data" / "processed" / "gloss_video_map.csv"
MAX_WORKERS = 4
RETRY_COUNT = 3
TIMEOUT = 120
PREFERRED_SIGNERS = ["Liz", "Brady", "Naomi", "Tyler", "Lana", "Dana"]


def build_gloss_video_map(df: pd.DataFrame) -> pd.DataFrame:
    """One row per gloss, best signer, with video file path."""
    selected = []
    for gloss, group in df.groupby("gloss"):
        for signer in PREFERRED_SIGNERS:
            signer_rows = group[group["signer"] == signer]
            if len(signer_rows) > 0:
                row = signer_rows.iloc[0].copy()
                row["video_file"] = f"data/raw/videos/{row['session']}/scene{int(row['scene'])}-camera1.mov"
                selected.append(row)
                break
    
    result = pd.DataFrame(selected)
    result = result[["gloss", "variant", "signer", "session", "scene", 
                     "start_frame", "end_frame", "video_file"]]
    result = result.sort_values("gloss").reset_index(drop=True)
    return result


def download_video(session: str, scene: int, output_dir: Path) -> tuple:
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
    
    # Build slim gloss→video map
    gloss_map = build_gloss_video_map(df)
    gloss_map.to_csv(MAP_FILE, index=False)
    print(f"📋 Gloss→video map: {MAP_FILE} ({len(gloss_map)} glosses)")
    
    # Get unique videos needed
    unique_videos = gloss_map[["session", "scene"]].drop_duplicates()
    
    # Check existing
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
    
    print(f"🎬 Slim ASLLVD Downloader (1 signer/gloss)")
    print(f"   {len(gloss_map)} glosses → {len(unique_videos)} videos")
    print(f"   {existing} already downloaded, {len(to_download)} remaining")
    print(f"   Est. size: ~{len(unique_videos) * 150 / 1024:.0f} GB total")
    print()
    
    if not to_download:
        print("✅ All videos already downloaded!")
        return
    
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
        fail_file = OUTPUT_DIR / "failed_downloads_slim.txt"
        with open(fail_file, "w") as f:
            for line in failed_list:
                f.write(line + "\n")
        print(f"   Failed list: {fail_file}")


if __name__ == "__main__":
    main()