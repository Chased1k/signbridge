#!/usr/bin/env python3
"""
Sprint 1 — Step 2: Clean ASLLVD metadata Excel → CSV.

Extracts: gloss, variant, consultant (signer), session, scene, start/end frames.
Filters out corrupt entries. Sorts by gloss for easy lookup.

Output: data/processed/asllvd_clean.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

INPUT_FILE = Path(__file__).parent.parent / "data" / "raw" / "asllvd_metadata.xlsx"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_FILE = OUTPUT_DIR / "asllvd_clean.csv"


def clean_metadata(input_path: str, output_path: str) -> pd.DataFrame:
    """Clean ASLLVD Excel metadata to a workable CSV."""
    print(f"📖 Reading: {input_path}")
    df = pd.read_excel(input_path)
    
    # Replace sentinel values with NaN
    df = df.replace("============", np.nan)
    df = df.replace("------------", np.nan)
    df = df.replace("-------------------------", np.nan)
    
    # Drop rows missing critical fields
    required = ["Gloss Variant", "Session", "Scene", "Start", "End"]
    df = df.dropna(axis=0, subset=required, how="all")
    
    # Select and rename columns
    cols = ["Main New Gloss.1", "Gloss Variant", "Consultant", 
            "Session", "Scene", "Start", "End"]
    df = df[cols].copy()
    df.columns = ["gloss", "variant", "signer", "session", "scene", "start_frame", "end_frame"]
    
    # Type conversions
    df["scene"] = df["scene"].astype(int)
    df["start_frame"] = df["start_frame"].astype(int)
    df["end_frame"] = df["end_frame"].astype(int)
    
    # Build session-scene identifier (matches BU FTP URL pattern)
    df["session_scene"] = df["session"].astype(str) + "-" + df["scene"].astype(str)
    
    # Sort
    df = df.sort_values(["gloss", "variant", "signer"]).reset_index(drop=True)
    df["id"] = df.index
    
    # Stats
    unique_glosses = df["gloss"].nunique()
    unique_signers = df["signer"].nunique()
    total_entries = len(df)
    
    print(f"✅ Cleaned: {output_path}")
    print(f"   {total_entries} total entries")
    print(f"   {unique_glosses} unique glosses")
    print(f"   {unique_signers} unique signers: {sorted(df['signer'].dropna().unique().tolist())}")
    
    # Show top signers by entry count
    signer_counts = df["signer"].value_counts().head(10)
    print(f"\n   Top signers by entry count:")
    for signer, count in signer_counts.items():
        print(f"     {signer}: {count} signs")
    
    return df


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not INPUT_FILE.exists():
        print(f"❌ Metadata file not found: {INPUT_FILE}")
        print("   Run 01_download_metadata.py first.")
        return
    
    df = clean_metadata(str(INPUT_FILE), str(OUTPUT_FILE))
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\n💾 Saved: {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size} bytes)")


if __name__ == "__main__":
    main()