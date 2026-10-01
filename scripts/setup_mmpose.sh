#!/usr/bin/env bash
#
# Sprint 1 — Step 4: Set up MMPose/RTMPose on GPU VPS and run batch pose extraction
#
# This script runs ON the GPU VPS (Vast.ai, RunPod, or DO GPU droplet).
# It:
#   1. Installs MMPose, MMEngine, MMCV, MMDet + dependencies
#   2. Downloads the RTMPose whole-body checkpoint
#   3. Receives the ASLLVD videos (rsync from Watchtower)
#   4. Runs batch pose extraction: video → 133-keypoint skeleton overlay video
#   5. Packages results for rsync back
#
# Usage (on GPU VPS):
#   bash setup_mmpose.sh
#
# After setup, run:
#   python3 batch_pose_extraction.py --input /data/videos --output /data/pose_library --map /data/gloss_video_map.csv

set -e

echo "🔧 Installing MMPose/RTMPose dependencies..."

# System deps
apt-get update && apt-get install -y python3-pip python3-dev ffmpeg git

# Python deps — PyTorch with CUDA
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu121

# OpenMMLab stack
pip3 install -U openmim
mim install mmengine
mim install mmcv
mim install mmdet
mim install mmpose

# Other deps
pip3 install pandas opencv-python ffmpeg-python

echo "✅ MMPose installed"

# Download RTMPose whole-body checkpoint
echo "⬇️  Downloading RTMPose checkpoint..."
mkdir -p /data/checkpoints
cd /data/checkpoints

# RTMPose-WholeBody-133 (best general-purpose whole-body pose model)
wget -q https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-wholebody_pt-aic-coco_270e-256x192-ea89636c_20230115.pth -O rtmpose-wholebody.pth
wget -q https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/rtmpose-m_simcc-wholebody_pt-aic-coco_270e-256x192-ea89636c_20230115.json -O rtmpose-wholebody.json

# Also need a detection model for person detection
wget -q https://download.openmmlab.com/mmdetection/v3.0/rtmdet/rtmdet_m_8xb32-300e_coco/rtmdet_m_8xb32-300e_coco_20220719_112220-229f2187.pth -O rtmdet.pth
wget -q https://download.openmmlab.com/mmdetection/v3.0/rtmdet/rtmdet_m_8xb32-300e_coco/rtmdet_m_8xb32-300e_coco_20220719_112220-229f2187.py -O rtmdet.py

echo "✅ Checkpoints downloaded"
echo ""
echo "Setup complete! Next steps:"
echo "  1. rsync videos from Watchtower:"
echo "     rsync -avz --progress watchtower:/Users/watchtower/projects/signbridge/data/raw/videos/ /data/videos/"
echo "     rsync -avz watchtower:/Users/watchtower/projects/signbridge/data/processed/gloss_video_map.csv /data/"
echo ""
echo "  2. Run batch pose extraction:"
echo "     python3 batch_pose_extraction.py --input /data/videos --output /data/pose_library --map /data/gloss_video_map.csv"
echo ""
echo "  3. rsync results back:"
echo "     rsync -avz --progress /data/pose_library/ watchtower:/Users/watchtower/projects/signbridge/data/pose_library/"