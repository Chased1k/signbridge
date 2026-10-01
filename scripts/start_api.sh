#!/bin/bash
# Start SignBridge API server
lsof -ti:18105 2>/dev/null | xargs kill 2>/dev/null
sleep 1
cd /Users/watchtower/projects/signbridge
python3.14 src/api.py