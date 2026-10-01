#!/usr/bin/env python3
"""
Sprint 1 — Step 5 (CPU): Batch pose extraction using Google MediaPipe.

Runs on Watchtower's CPU (Intel i9-9980HK). No GPU required.
MediaPipe Pose extracts 33 body landmarks + 21 hand landmarks per hand = 75 total.
Runs at 30+ FPS on CPU.

Output: data/pose_library/{gloss}.mp4 — one pose video per gloss
        data/pose_library/pose_lookup.json — gloss → metadata map

Usage:
  python3.11 scripts/mediapipe_pose_extraction.py
"""

import os
import sys
import json
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import mediapipe as mp


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
VIDEO_DIR = PROJECT_ROOT / "data" / "raw" / "videos"
GLOSS_MAP = PROJECT_ROOT / "data" / "processed" / "gloss_video_map.csv"
OUTPUT_DIR = PROJECT_ROOT / "data" / "pose_library"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# MediaPipe drawing utils
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands

# Pose connections (body)
POSE_CONNECTIONS = mp_pose.POSE_CONNECTIONS
HAND_CONNECTIONS = mp_hands.HAND_CONNECTIONS


def draw_landmarks_on_black(frame, pose_results, hands_results):
    """Draw pose + hand landmarks on a black background."""
    black = np.zeros_like(frame)
    h, w = frame.shape[:2]
    
    # Draw body pose
    if pose_results.pose_landmarks:
        # Draw skeleton lines
        for connection in POSE_CONNECTIONS:
            start_idx, end_idx = connection
            start = pose_results.pose_landmarks.landmark[start_idx]
            end = pose_results.pose_landmarks.landmark[end_idx]
            
            # Skip low-visibility points
            if start.visibility < 0.3 or end.visibility < 0.3:
                continue
            
            x1, y1 = int(start.x * w), int(start.y * h)
            x2, y2 = int(end.x * w), int(end.y * h)
            
            # Color: green for body, brighter for high visibility
            vis = (start.visibility + end.visibility) / 2
            color = (0, int(255 * vis), 0)
            cv2.line(black, (x1, y1), (x2, y2), color, 2)
        
        # Draw joints
        for idx, lm in enumerate(pose_results.pose_landmarks.landmark):
            if lm.visibility < 0.3:
                continue
            x, y = int(lm.x * w), int(lm.y * h)
            # Highlight key joints (shoulders, elbows, wrists, hips, knees, ankles)
            key_joints = {11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28, 0}
            if idx in key_joints:
                cv2.circle(black, (x, y), 5, (0, 255, 255), -1)  # yellow dots
            else:
                cv2.circle(black, (x, y), 3, (0, 200, 0), -1)
    
    # Draw hand landmarks
    if hands_results.multi_hand_landmarks:
        for hand_landmarks in hands_results.multi_hand_landmarks:
            # Draw connections
            for connection in HAND_CONNECTIONS:
                start_idx, end_idx = connection
                start = hand_landmarks.landmark[start_idx]
                end = hand_landmarks.landmark[end_idx]
                
                x1, y1 = int(start.x * w), int(start.y * h)
                x2, y2 = int(end.x * w), int(end.y * h)
                
                cv2.line(black, (x1, y1), (x2, y2), (255, 0, 0), 2)  # blue lines
            
            # Draw finger joints
            for lm in hand_landmarks.landmark:
                x, y = int(lm.x * w), int(lm.y * h)
                cv2.circle(black, (x, y), 3, (255, 100, 0), -1)
    
    return black


def extract_pose_video(video_path, output_path, start_frame, end_frame):
    """Extract pose from a video segment using MediaPipe."""
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return False, "cannot open video", 0
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps != fps:  # NaN check
        fps = 30.0
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Seek to start frame
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    # Output video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    frame_count = 0
    target_frames = end_frame - start_frame + 1
    
    with mp_pose.Pose(
        static_image_mode=False,
        model_complexity=1,  # 0=lite, 1=full, 2=heavy
        enable_segmentation=False,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    ) as pose, mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=2,
        min_detection_confidence=0.3,
        min_tracking_confidence=0.3
    ) as hands:
        
        while cap.isOpened() and frame_count < target_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process
            pose_results = pose.process(rgb)
            hands_results = hands.process(rgb)
            
            # Draw on black background
            vis_frame = draw_landmarks_on_black(frame, pose_results, hands_results)
            
            out.write(vis_frame)
            frame_count += 1
    
    cap.release()
    out.release()
    return True, f"{frame_count} frames", frame_count


def main():
    # Load gloss map
    gloss_map = pd.read_csv(str(GLOSS_MAP))
    print(f"📋 Loaded {len(gloss_map)} glosses from {GLOSS_MAP.name}")
    print(f"   Video dir: {VIDEO_DIR}")
    print(f"   Output: {OUTPUT_DIR}")
    print()
    
    # Check existing
    to_process = []
    existing = 0
    for _, row in gloss_map.iterrows():
        gloss = row['gloss']
        output_path = OUTPUT_DIR / f"{gloss}.mp4"
        if output_path.exists() and output_path.stat().st_size > 1000:
            existing += 1
        else:
            to_process.append(row)
    
    print(f"   {existing} already processed, {len(to_process)} to do")
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
        gloss = row['gloss']
        session = str(row['session'])
        scene = int(row['scene'])
        start = int(row['start_frame'])
        end = int(row['end_frame'])
        
        # Try multiple video path patterns
        video_path = VIDEO_DIR / session / f"scene{scene}-camera1.mov"
        if not video_path.exists():
            # Try .mp4
            video_path = VIDEO_DIR / session / f"scene{scene}-camera1.mp4"
        if not video_path.exists():
            # Try without camera suffix
            video_path = VIDEO_DIR / session / f"scene{scene}.mov"
        if not video_path.exists():
            video_path = VIDEO_DIR / session / f"scene{scene}.mp4"
        if not video_path.exists():
            # Try session as direct filename
            video_path = VIDEO_DIR / f"{session}_scene{scene}.mov"
        if not video_path.exists():
            fail_count += 1
            failed_list.append(f"{gloss}: video not found ({session}/scene{scene})")
            continue
        
        output_path = OUTPUT_DIR / f"{gloss}.mp4"
        
        try:
            ok, msg, frames = extract_pose_video(video_path, output_path, start, end)
            if ok:
                success_count += 1
                total_frames += frames
            else:
                fail_count += 1
                failed_list.append(f"{gloss}: {msg}")
        except Exception as e:
            fail_count += 1
            failed_list.append(f"{gloss}: {e}")
        
        if (i + 1) % 10 == 0 or (i + 1) == len(to_process):
            elapsed = time.time() - start_time
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            eta = (len(to_process) - i - 1) / rate if rate > 0 else 0
            print(f"  [{i+1}/{len(to_process)}] ✅{success_count} ❌{fail_count} | "
                  f"{rate:.1f}/s | ETA: {eta:.0f}s ({eta/60:.1f}m)")
    
    elapsed = time.time() - start_time
    print(f"\n📊 Results: {success_count} processed, {fail_count} failed, {existing} already existed")
    print(f"   Total frames: {total_frames}")
    print(f"   Time: {elapsed:.0f}s ({elapsed/60:.1f} min)")
    
    if failed_list:
        fail_file = OUTPUT_DIR / "failed_extractions.txt"
        with open(fail_file, "w") as f:
            for line in failed_list:
                f.write(line + "\n")
        print(f"   Failed list: {fail_file} ({len(failed_list)} entries)")
    
    # Build pose lookup table
    print("\n📋 Building pose lookup table...")
    lookup = {}
    for _, row in gloss_map.iterrows():
        gloss = row['gloss']
        pose_path = OUTPUT_DIR / f"{gloss}.mp4"
        if pose_path.exists() and pose_path.stat().st_size > 1000:
            lookup[gloss] = {
                "pose_video": str(pose_path),
                "signer": row['signer'],
                "start_frame": int(row['start_frame']),
                "end_frame": int(row['end_frame']),
                "session": str(row['session']),
                "scene": int(row['scene'])
            }
    
    lookup_path = OUTPUT_DIR / "pose_lookup.json"
    with open(lookup_path, "w") as f:
        json.dump(lookup, f, indent=2)
    
    print(f"✅ Pose lookup table: {lookup_path} ({len(lookup)} glosses)")
    print(f"   Coverage: {len(lookup)}/{len(gloss_map)} ({100*len(lookup)/len(gloss_map):.1f}%)")


if __name__ == "__main__":
    main()