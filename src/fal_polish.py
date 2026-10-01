#!/usr/bin/env python3
"""
SignBridge Sprint 4 — fal.ai Dreamactor v2 Integration

Takes a skeleton pose video + character reference image → submits to
fal.ai Dreamactor v2 → polls for completion → downloads photorealistic video.

API: fal-ai/bytedance/dreamactor/v2
- image_url: reference image (Fabio character) to animate
- video_url: driving video (skeleton pose) providing motion
- Returns: photorealistic video of character performing the motion
- Max 30 sec driving video, image max 4.7MB

Sprint 4 update: Switched from raw HTTP polling to fal_client SDK
which handles queue SSE streaming properly.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CREDENTIALS = Path(os.path.expanduser("~/.openclaw/credentials/fal.json"))
CHARACTER_SHEET = PROJECT_ROOT / "assets" / "character_sheet" / "fabio_front.png"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DREAMACTOR_ENDPOINT = "fal-ai/bytedance/dreamactor/v2"
FAL_KEY = None


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level} [FAL] {msg}", flush=True)


def load_fal_key():
    global FAL_KEY
    with open(CREDENTIALS) as f:
        FAL_KEY = json.load(f)["FAL_KEY"]
    os.environ["FAL_KEY"] = FAL_KEY
    log(f"Key loaded ({FAL_KEY[:8]}...)")


def upload_to_fal(file_path):
    """Upload a local file to fal.ai CDN and return the public URL."""
    try:
        import fal_client
        log(f"Uploading {file_path.name} ({file_path.stat().st_size:,} bytes)...")
        url = fal_client.upload_file(str(file_path))
        log(f"Uploaded → {url}")
        return url
    except Exception as e:
        log(f"fal_client upload failed: {e}", "ERROR")
        return None


def polish_video(pose_video_path, character_image_path=None, output_path=None):
    """
    Full pipeline: upload files → submit to Dreamactor → wait → download.
    
    Uses fal_client SDK for proper queue handling (SSE-based, not HTTP polling).
    
    Args:
        pose_video_path: Path to skeleton pose video (driving motion)
        character_image_path: Path to character reference image (defaults to Fabio front)
        output_path: Where to save the polished video
    
    Returns:
        Path to the polished video, or None on failure
    """
    load_fal_key()
    
    pose_video = Path(pose_video_path)
    character_img = Path(character_image_path) if character_image_path else CHARACTER_SHEET
    
    if not pose_video.exists():
        log(f"Pose video not found: {pose_video}", "ERROR")
        return None
    if not character_img.exists():
        log(f"Character image not found: {character_img}", "ERROR")
        return None
    
    output = Path(output_path) if output_path else OUTPUT_DIR / f"polished_{pose_video.stem}.mp4"
    
    try:
        import fal_client
        
        # Step 1: Upload both files to fal.ai CDN
        log("=" * 50)
        log("STEP 1: Upload files to fal.ai CDN")
        log("=" * 50)
        image_url = upload_to_fal(character_img)
        video_url = upload_to_fal(pose_video)
        
        if not image_url or not video_url:
            log("Upload failed", "ERROR")
            return None
        
        # Step 2: Submit to Dreamactor v2 via fal_client SDK
        log("=" * 50)
        log("STEP 2: Submit to Dreamactor v2")
        log("=" * 50)
        log(f"Submitting to {DREAMACTOR_ENDPOINT}...")
        log(f"  Image: {image_url[:80]}...")
        log(f"  Video: {video_url[:80]}...")
        
        handler = fal_client.submit(
            DREAMACTOR_ENDPOINT,
            {
                "image_url": image_url,
                "video_url": video_url,
                "trim_first_second": True,
            },
        )
        log(f"Submitted: request_id={handler.request_id}")
        
        # Step 3: Wait for completion (fal_client handles SSE queue polling)
        log("=" * 50)
        log("STEP 3: Waiting for completion...")
        log("=" * 50)
        result = handler.get()
        
        # Step 4: Extract and download video
        log("=" * 50)
        log("STEP 4: Download result")
        log("=" * 50)
        video_file = result.get("video", {})
        video_url = video_file.get("url") if isinstance(video_file, dict) else str(video_file)
        
        if not video_url:
            log(f"No video URL in result: {result}", "ERROR")
            return None
        
        log(f"Downloading video from {video_url[:80]}...")
        import requests
        resp = requests.get(video_url, timeout=120)
        resp.raise_for_status()
        with open(output, "wb") as f:
            f.write(resp.content)
        log(f"✅ Saved: {output} ({len(resp.content):,} bytes)")
        
        log("=" * 50)
        log(f"✅ SUCCESS: {output}")
        log("=" * 50)
        return str(output)
        
    except Exception as e:
        log(f"❌ FAILED: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SignBridge fal.ai Polish — Dreamactor v2")
    parser.add_argument("pose_video", help="Path to skeleton pose video")
    parser.add_argument("--character", help="Path to character reference image", default=str(CHARACTER_SHEET))
    parser.add_argument("--output", help="Output video path", default=None)
    args = parser.parse_args()
    
    result = polish_video(args.pose_video, args.character, args.output)
    if result:
        print(f"\n✅ Polished video: {result}")
        sys.exit(0)
    else:
        print("\n❌ Polish failed")
        sys.exit(1)