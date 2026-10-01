#!/usr/bin/env python3.11
"""Test the updated pipeline with LLM translation."""
import sys, os, json
os.chdir("/Users/watchtower/projects/signbridge")
sys.path.insert(0, "src")
from pipeline import run_pipeline

result = run_pipeline(
    text_input="Hello. My name is Kellen. I want to tell you about a new project. We are building a tool that translates voice into sign language video. This is important for accessibility.",
    output_name="test_llm_v2"
)

print("\n" + "="*60)
print(json.dumps(result.get("stages", {}).get("translate", {}).get("data", {}).get("coverage", {}), indent=2))
glosses = result.get("stages", {}).get("translate", {}).get("data", {}).get("glosses", [])
print(f"\nGlosses ({len(glosses)}):")
for g in glosses:
    if g["gloss"] == "FINGERSPELL":
        print(f"  🔤 FINGERSPELL: {g.get('text_to_spell', '?')}")
    else:
        print(f"  ✅ {g['gloss']}")
print("="*60)