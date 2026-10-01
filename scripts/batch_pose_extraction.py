#!/usr/bin/env python3
"""
Sprint 1 — Step 5: Batch pose extraction using RTMPose.

Runs on GPU VPS. Takes each ASLLVD video, extracts the signer's pose
at each frame using RTMPose whole-body (133 keypoints), and renders
a pose overlay video (skeleton on black background).

Output: data/pose_library/{gloss}.mp4 — one pose video per gloss

Usage:
  python3 batch_pose_extraction.py --input /data/videos --output /data/pose_library --map /data/gloss_video_map.csv
"""

import argparse
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

import cv2
import numpy as np
import pandas as pd


def extract_pose_video(video_path: str, output_path: str, 
                       start_frame: int, end_frame: int,
                       det_config: str, det_ckpt: str,
                       pose_config: str, pose_ckpt: str) -> tuple:
    """
    Extract pose from a video segment and render skeleton overlay.
    
    Returns (gloss, success, message, num_frames)
    """
    try:
        from mmpose.apis import init_model as init_pose_model
        from mmpose.apis import inference_topdown
        from mmdet.apis import init_detector
        from mmdet.apis import inference_detector
        from mmpose.apis import visualize_pose_prediction
        from mmpose.structures import PoseDataSample
        
        # Initialize models (once per process)
        det_model = init_detector(det_config, det_ckpt, device="cuda:0")
        pose_model = init_pose_model(pose_config, pose_ckpt, device="cuda:0")
        
        # Open video
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return (None, False, f"Cannot open {video_path}", 0)
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # Seek to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        
        # Output video
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        frame_count = 0
        target_frames = end_frame - start_frame + 1
        
        while cap.isOpened() and frame_count < target_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Run person detection
            det_result = inference_detector(det_model, frame)
            pred_instance = det_result.pred_instances
            # Get the largest bounding box (the signer)
            scores = pred_instance.scores
            bboxes = pred_instance.bboxes
            if len(scores) == 0:
                # No person detected — write black frame
                out.write(np.zeros_like(frame))
                frame_count += 1
                continue
            
            # Pick the highest confidence detection
            best_idx = scores.argmax().item()
            bbox = bboxes[best_idx].cpu().numpy()
            
            # Run pose estimation
            pose_results = inference_topdown(
                pose_model, frame, [bbox]
            )
            
            # Visualize — skeleton on black background
            black_bg = np.zeros_like(frame)
            vis_frame = visualize_pose_prediction(
                pose_model, black_bg, pose_results, radius=4, thickness=2
            )
            
            out.write(vis_frame)
            frame_count += 1
        
        cap.release()
        out.release()
        
        return (None, True, f"{frame_count} frames", frame_count)
    
    except Exception as e:
        return (None, False, str(e), 0)


def process_single_gloss(row: dict, video_dir: str, output_dir: str,
                         det_config: str, det_ckpt: str,
                         pose_config: str, pose_ckpt: str) -> tuple:
    """Process a single gloss entry."""
    gloss = row["gloss"]
    session = str(row["session"])
    scene = int(row["scene"])
    start = int(row["start_frame"])
    end = int(row["end_frame"])
    
    video_path = Path(video_dir) / session / f"scene{scene}-camera1.mov"
    output_path = Path(output_dir) / f"{gloss}.mp4"
    
    if output_path.exists() and output_path.stat().st_size > 1000:
        return (gloss, True, "exists", 0)
    
    if not video_path.exists():
        return (gloss, False, f"video not found: {video_path}", 0)
    
    result = extract_pose_video(
        str(video_path), str(output_path), start, end,
        det_config, det_ckpt, pose_config, pose_ckpt
    )
    return (gloss, result[1], result[2], result[3])


def main():
    parser = argparse.ArgumentParser(description="Batch pose extraction from ASLLVD videos")
    parser.add_argument("--input", required=True, help="Input video directory")
    parser.add_argument("--output", required=True, help="Output pose library directory")
    parser.add_argument("--map", required=True, help="Gloss→video CSV map")
    parser.add_argument("--det-config", default="/data/checkpoints/rtmdet.py")
    parser.add_argument("--det-ckpt", default="/data/checkpoints/rtmdet.pth")
    parser.add_argument("--pose-config", default="/data/checkpoints/rtmpose-wholebody.json")
    parser.add_argument("--pose-ckpt", default="/data/checkpoints/rtmpose-wholebody.pth")
    parser.add_argument("--workers", type=int, default=1, help="Parallel processes (1 per GPU)")
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load gloss map
    gloss_map = pd.read_csv(args.map)
    print(f"📋 Loaded {len(gloss_map)} glosses from {args.map}")
    
    # Check existing
    to_process = []
    existing = 0
    for _, row in gloss_map.iterrows():
        output_path = output_dir / f"{row['gloss']}.mp4"
        if output_path.exists() and output_path.stat().st_size > 1000:
            existing += 1
        else:
            to_process.append(row.to_dict())
    
    print(f"   {existing} already processed, {len(to_process)} remaining")
    print(f"   Output: {args.output}")
    print()
    
    if not to_process:
        print("✅ All glosses already processed!")
        return
    
    # Process
    success_count = 0
    fail_count = 0
    total_frames = 0
    failed_list = []
    
    start_time = time.time()
    
    for i, row in enumerate(to_process):
        gloss, success, msg, frames = process_single_gloss(
            row, args.input, args.output,
            args.det_config, args.det_ckpt,
            args.pose_config, args.pose_ckpt
        )
        
        if success:
            success_count += 1
            total_frames += frames
        else:
            fail_count += 1
            failed_list.append(f"  {gloss}: {msg}")
        
        if (i + 1) % 10 == 0 or (i + 1) == len(to_process):
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(to_process) - i - 1) / rate if rate > 0 else 0
            print(f"   [{i+1}/{len(to_process)}] ✅ {success_count} ❌ {fail_count} | "
                  f"{rate:.1f} gloss/s | ETA: {eta:.0f}s")
    
    elapsed = time.time() - start_time
    print(f"\n📊 Results: {success_count} processed, {fail_count} failed, {existing} already existed")
    print(f"   Total frames: {total_frames}")
    print(f"   Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    
    if failed_list:
        fail_file = output_dir / "failed_extractions.txt"
        with open(fail_file, "w") as f:
            for line in failed_list:
                f.write(line + "\n")
        print(f"   Failed list: {fail_file}")
    
    # Build lookup table
    print("\n📋 Building pose lookup table...")
    lookup = {}
    for _, row in gloss_map.iterrows():
        gloss = row["gloss"]
        pose_path = output_dir / f"{gloss}.mp4"
        if pose_path.exists() and pose_path.stat().st_size > 1000:
            lookup[gloss] = {
                "pose_video": str(pose_path),
                "signer": row["signer"],
                "start_frame": int(row["start_frame"]),
                "end_frame": int(row["end_frame"]),
                "session": str(row["session"]),
                "scene": int(row["scene"])
            }
    
    lookup_path = output_dir / "pose_lookup.json"
    with open(lookup_path, "w") as f:
        json.dump(lookup, f, indent=2)
    
    print(f"✅ Pose lookup table: {lookup_path} ({len(lookup)} glosses)")


if __name__ == "__main__":
    main()