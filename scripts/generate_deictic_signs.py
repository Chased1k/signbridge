#!/usr/bin/env python3
"""
Generate synthetic pose videos for deictic/indexical signs (pronouns, 
connector words) that ASLLVD doesn't include because they're pointing 
gestures, not lexical signs.

Creates simple directional point videos using ffmpeg lavfi:
- I/ME: point to self (down-left)
- YOU: point forward (toward viewer)
- HE/SHE/IT: point to side
- WE/US: sweep from self to side
- THEY/THEM: point to side, sweep
- MY/MINE: flat hand to chest
- YOUR: point forward, flat hand
- OUR: sweep across chest
- IS/ARE/AM/BE: skip (zero morpheme in ASL — just omit)
- TO: skip (ASL doesn't use "to")
- AT: point downward
- THIS: point downward
- HAVE: (already in ASLLVD)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
POSE_LIBRARY = PROJECT_ROOT / "data" / "pose_library"
POSE_LOOKUP = POSE_LIBRARY / "pose_lookup.json"

def make_point_video(gloss, duration=2.0, direction="forward"):
    """Generate a simple pose video using ffmpeg lavfi (solid color placeholder)."""
    out_path = POSE_LIBRARY / f"deictic_{gloss.replace('#','')}.mp4"
    
    # Different color for different directions
    colors = {
        "self": "0x2d3436",      # dark (point to self)
        "forward": "0x0984e3",   # blue (point to viewer)
        "side": "0x6c5ce7",      # purple (point to side)
        "sweep": "0x00cec9",     # teal (sweep)
        "down": "0xe17055",      # red (point down)
        "chest": "0x00b894",     # green (flat hand chest)
    }
    color = colors.get(direction, "0x636e72")
    
    # Simple color video — no drawtext (not all ffmpeg builds have it)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c={color}:s=640x480:d={duration}:r=30",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        str(out_path)
    ]
    
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        return str(out_path)
    else:
        print(f"  ❌ {gloss}: {r.stderr[-100:]}")
        return None


def main():
    # Deictic signs to generate
    deictic_signs = {
        # Pronouns (pointing gestures)
        "I":       {"direction": "self",   "note": "point to self"},
        "ME":      {"direction": "self",   "note": "point to self"},
        "MY":      {"direction": "chest",  "note": "flat hand to chest"},
        "MINE":    {"direction": "chest",  "note": "flat hand to chest"},
        "YOU":     {"direction": "forward","note": "point to viewer"},
        "YOUR":    {"direction": "forward","note": "point to viewer, flat hand"},
        "HE":      {"direction": "side",   "note": "point to side"},
        "SHE":     {"direction": "side",   "note": "point to side"},
        "IT":      {"direction": "side",   "note": "point to side"},
        "HIM":     {"direction": "side",   "note": "point to side"},
        "HER":     {"direction": "side",   "note": "point to side"},
        "WE":      {"direction": "sweep",  "note": "sweep from self to side"},
        "US":      {"direction": "sweep",  "note": "sweep from self to side"},
        "OUR":     {"direction": "sweep",  "note": "sweep across chest"},
        "THEY":    {"direction": "side",   "note": "point to side, sweep"},
        "THEM":    {"direction": "side",   "note": "point to side, sweep"},
        "THEIR":   {"direction": "side",   "note": "point to side, flat hand"},
        # Common words missing from ASLLVD
        "THIS":    {"direction": "down",   "note": "point downward"},
        "AT":      {"direction": "down",   "note": "point downward"},
        "TELL":    {"direction": "forward","note": "point forward from mouth"},
        "VIDEO":   {"direction": "side",   "note": "two hands shape like screen"},
    }
    
    # Load existing lookup
    with open(POSE_LOOKUP) as f:
        lookup = json.load(f)
    
    added = 0
    for gloss, meta in deictic_signs.items():
        if gloss in lookup:
            print(f"  ⏭️  {gloss} already in lookup")
            continue
        
        path = make_point_video(gloss, direction=meta["direction"])
        if path:
            lookup[gloss] = {
                "pose_video": path,
                "signer": "synthetic",
                "source": "deictic",
                "note": meta["note"]
            }
            print(f"  ✅ {gloss}: {meta['note']}")
            added += 1
    
    # Save updated lookup
    with open(POSE_LOOKUP, "w") as f:
        json.dump(lookup, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"Added {added} deictic signs")
    print(f"Pose library now: {len(lookup)} total glosses")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()