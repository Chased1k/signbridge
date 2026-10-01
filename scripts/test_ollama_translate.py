#!/usr/bin/env python3.11
"""Test Ollama ASL gloss translation."""
import json
import urllib.request

with open("/Users/watchtower/projects/signbridge/data/pose_library/pose_lookup.json") as f:
    lookup = json.load(f)

available = sorted(list(lookup.keys()))[:100]

text = "Hello. My name is Kellen. I want to tell you about a new project we are building. It translates voice into sign language video."

prompt = f"""You are an ASL (American Sign Language) translation expert.

Translate the following English text into ASL gloss. ASL gloss uses uppercase words for signs.

Rules:
1. ASL has different grammar (OSV word order, topic-comment structure)
2. Use ONLY signs from this vocabulary when possible: {', '.join(available[:80])}
3. If a word doesn't have a direct sign, use a synonym from the vocabulary
4. For proper nouns (names, places), mark as FINGERSPELL
5. Keep it concise — remove filler words

Return ONLY valid JSON:
{{"summary": "condensed english", "glosses": [{{"gloss": "SIGN", "start": 0.0, "end": 2.0, "expression": "neutral"}}]}}

English text:
{text}
"""

data = json.dumps({
    "model": "gemma4:cloud",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3,
    "stream": False,
    "format": "json"
}).encode()

req = urllib.request.Request(
    "http://localhost:11434/api/chat",
    data=data,
    headers={"Content-Type": "application/json"}
)

print("Sending to Ollama...")
with urllib.request.urlopen(req, timeout=60) as resp:
    result = json.loads(resp.read())
    content = result["message"]["content"]
    print(f"Raw response ({len(content)} chars):")
    print(content[:500])
    print("...")
    
    # Try to parse JSON
    try:
        parsed = json.loads(content)
        print(f"\n✅ Parsed! {len(parsed.get('glosses', []))} glosses")
        for g in parsed.get("glosses", []):
            print(f"  {g}")
    except:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            print(f"\n✅ Extracted! {len(parsed.get('glosses', []))} glosses")
            for g in parsed.get("glosses", []):
                print(f"  {g}")
        else:
            print("\n❌ Could not parse JSON")