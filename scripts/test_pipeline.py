#!/usr/bin/env python3.11
"""Quick test runner for SignBridge pipeline."""
import sys
import os

os.chdir("/Users/watchtower/projects/signbridge")
sys.path.insert(0, "src")
sys.argv = ["pipeline.py", "--text", "Hello. My name is Kellen. I want to tell you about a new project. We are building a tool that translates voice into sign language video. This is important for accessibility."]

from pipeline import run_pipeline

result = run_pipeline(text_input="Hello. My name is Kellen. I want to tell you about a new project. We are building a tool that translates voice into sign language video. This is important for accessibility.")

import json
print("\n" + "="*60)
print(json.dumps(result, indent=2, default=str))
print("="*60)