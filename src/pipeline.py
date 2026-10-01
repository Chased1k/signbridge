#!/usr/bin/env python3
"""
SignBridge Sprint 2 — Core Pipeline: Audio → ASL Signer Video

Hybrid translation: LLM rephrases English → ASL grammar, then deterministic
word-to-gloss matching against our 2569-sign pose library.

Stages:
1. Audio → Whisper transcription (with timestamps)
2. Transcript → LLM rephrase to ASL grammar → deterministic gloss mapping
3. Gloss → pose video lookup + fingerspell fallback
4. Pose videos → stitched skeleton video
5. (Optional) Skeleton video → fal.ai photorealistic render
"""

import argparse
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
POSE_LIBRARY = PROJECT_ROOT / "data" / "pose_library"
POSE_LOOKUP = POSE_LIBRARY / "pose_lookup.json"
OUTPUT_DIR = PROJECT_ROOT / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def log(stage, msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {level} [{stage}] {msg}")


# =============================================================================
# STAGE 1: Audio → Transcript
# =============================================================================

def transcribe_audio(audio_path, model_size="base"):
    log("TRANSCRIBE", f"Loading Whisper {model_size}...")
    from faster_whisper import WhisperModel
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    log("TRANSCRIBE", f"Transcribing {audio_path}...")
    segments, info = model.transcribe(str(audio_path), word_timestamps=True)
    seg_list, full_text = [], []
    for seg in segments:
        seg_list.append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        full_text.append(seg.text.strip())
    result = {"text": " ".join(full_text), "segments": seg_list, "language": info.language, "duration": round(info.duration, 2)}
    log("TRANSCRIBE", f"Done: {len(seg_list)} segments, {result['duration']}s")
    return result


# =============================================================================
# STAGE 2: Transcript → ASL Gloss (hybrid: LLM rephrase + deterministic match)
# =============================================================================

def translate_to_asl_gloss(transcript, available_glosses=None):
    log("TRANSLATE", "Loading pose lookup...")
    with open(POSE_LOOKUP, "r") as f:
        pose_lookup = json.load(f)
    available = set(pose_lookup.keys())
    log("TRANSLATE", f"Available: {len(available)} glosses")

    llm_result = llm_rephrase_and_map(transcript, available)
    glosses = llm_result.get("glosses", [])
    
    # Final coverage check
    resolved, stats = [], {"direct_hit": 0, "fingerspelled": 0}
    for item in glosses:
        g = item["gloss"].upper().strip()
        if g == "FINGERSPELL":
            resolved.append(item)
            stats["fingerspelled"] += 1
        elif g in available:
            resolved.append(item)
            stats["direct_hit"] += 1
        else:
            item["gloss"] = "FINGERSPELL"
            item["text_to_spell"] = g
            resolved.append(item)
            stats["fingerspelled"] += 1
    
    log("TRANSLATE", f"Coverage: {stats}")
    return {"summary": llm_result.get("summary", transcript), "glosses": resolved, "coverage": stats}


def llm_rephrase_and_map(text, available_glosses):
    """
    Hybrid approach:
    1. LLM rephrases English text into ASL grammar (OSV, drop filler)
    2. We deterministically match each word to our pose library
    3. Unmatched words → fingerspell
    """
    from gloss_remaps import remap_gloss, SKIP_WORDS

    # Step 1: LLM rephrase
    asl_text = None
    try:
        import urllib.request
        prompt = f"""You are an ASL expert. Rewrite this English in ASL grammar.
Rules: OSV word order, topic-comment structure, drop filler (the/a/an/is/are/be/um/like/just).
Output ONLY the rewritten words, nothing else. No labels, no explanations.

English: {text}

ASL:"""
        data = json.dumps({"model": "gemma4:cloud", "messages": [{"role": "user", "content": prompt}], "temperature": 0.2, "stream": False}).encode()
        req = urllib.request.Request("http://localhost:11434/api/chat", data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read())
            asl_text = result["message"]["content"].strip()
            # Strip any "ASL:" prefix if LLM echoed it
            if asl_text.upper().startswith("ASL:"):
                asl_text = asl_text[4:].strip()
            log("TRANSLATE", f"LLM rephrased: {asl_text}")
    except Exception as e:
        log("TRANSLATE", f"Ollama failed: {e}", "WARN")

    if not asl_text:
        log("TRANSLATE", "Using original text (no LLM)")
        asl_text = text

    # Step 2: Deterministic word → gloss mapping
    FILLER = {"the", "a", "an", "is", "are", "am", "be", "um", "uh", "like", "just", "really", "so", "very"}
    words = asl_text.split()
    glosses = []
    t = 0.0

    for word in words:
        clean = word.strip(".,!?;:\"'()").upper()
        if not clean or clean.lower() in FILLER or clean in SKIP_WORDS:
            continue

        gloss, source = remap_gloss(clean, available_glosses)
        if gloss is None or source == "skip":
            continue

        expr = "neutral"
        if clean in {"WHAT", "WHO", "WHERE", "WHEN", "WHY", "HOW"}:
            expr = "question"
        elif clean in {"NOT", "NO", "NEVER", "NONE"}:
            expr = "negation"

        if gloss == "FINGERSPELL":
            glosses.append({"gloss": "FINGERSPELL", "text_to_spell": clean, "start": round(t, 2), "end": round(t + 3.0, 2), "expression": expr})
            t += 3.0
        else:
            glosses.append({"gloss": gloss, "start": round(t, 2), "end": round(t + 2.0, 2), "expression": expr})
            t += 2.0

    return {"summary": asl_text, "glosses": glosses}


# =============================================================================
# STAGE 3: Pose Video Assembly
# =============================================================================

def assemble_pose_video(glosses, output_path):
    log("ASSEMBLE", f"Building from {len(glosses)} glosses...")
    with open(POSE_LOOKUP, "r") as f:
        pose_lookup = json.load(f)
    segments, missing = [], []
    for item in glosses:
        g = item["gloss"]
        if g == "FINGERSPELL":
            log("ASSEMBLE", f"  FINGERSPELL: {item.get('text_to_spell','')} (skip POC)", "WARN")
            missing.append(f"FINGERSPELL: {item.get('text_to_spell','')}")
            continue
        if g in pose_lookup:
            p = pose_lookup[g]["pose_video"]
            if os.path.exists(p):
                segments.append(p)
            else:
                missing.append(g)
        else:
            missing.append(g)
    if not segments:
        return False, "no segments", str(output_path)
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, "w") as f:
        for s in segments:
            f.write(f"file '{s}'\n")
    log("ASSEMBLE", f"Concatenating {len(segments)} segments...")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_path)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output_path)]
        r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode == 0:
        log("ASSEMBLE", f"✅ {output_path} ({os.path.getsize(output_path)} bytes, {len(segments)} segs)")
        return True, f"{len(segments)} segments, {len(missing)} missing", str(output_path)
    return False, r.stderr[-200:], str(output_path)


# =============================================================================
# STAGE 4: fal.ai Polish
# =============================================================================

def polish_with_fal(pose_video_path, character_image_url, output_path):
    log("POLISH", "Starting fal.ai render...")
    fal_key = None
    try:
        with open(os.path.expanduser("~/.openclaw/credentials/fal.json")) as f:
            fal_key = json.load(f).get("FAL_KEY", "")
    except:
        pass
    if not fal_key:
        log("POLISH", "No fal.ai key — skipping", "WARN")
        return False, "no fal key", pose_video_path
    try:
        import base64, urllib.request
        with open(pose_video_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode()
        log("POLISH", f"Submitting to fal.ai ({os.path.getsize(pose_video_path)} bytes)...")
        data = json.dumps({"video": f"data:video/mp4;base64,{video_b64}", "character_image": character_image_url, "num_inference_steps": 30, "guidance_scale": 7.5}).encode()
        req = urllib.request.Request("https://fal.run/fal-ai/dreamactor", data=data, headers={"Content-Type": "application/json", "Authorization": f"Key {fal_key}"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            video_url = result.get("video", result.get("output", {}).get("video", ""))
            if video_url:
                urllib.request.urlretrieve(video_url, output_path)
                log("POLISH", f"✅ {output_path}")
                return True, "fal.ai complete", str(output_path)
            return False, "no video URL", pose_video_path
    except Exception as e:
        log("POLISH", f"fal.ai failed: {e}", "ERROR")
        return False, str(e), pose_video_path


# =============================================================================
# MAIN
# =============================================================================

def run_pipeline(audio_path=None, text_input=None, character_url=None, output_name=None):
    job_id = output_name or f"job_{int(time.time())}"
    log("PIPELINE", f"Starting: {job_id}")
    results = {"job_id": job_id, "started_at": datetime.now().isoformat(), "stages": {}}

    if audio_path and os.path.exists(audio_path):
        transcript = transcribe_audio(audio_path)
        results["stages"]["transcribe"] = {"status": "ok", "data": transcript}
        text = transcript["text"]
    else:
        text = text_input or "Hello, my name is Kellen. I want to share something exciting."
        results["stages"]["transcribe"] = {"status": "skipped", "data": {"text": text}}
    log("PIPELINE", f"Text: {text[:100]}...")

    translation = translate_to_asl_gloss(text)
    results["stages"]["translate"] = {"status": "ok", "data": translation}
    log("PIPELINE", f"{len(translation['glosses'])} signs, {translation['coverage']}")

    with open(OUTPUT_DIR / f"{job_id}_intermediate.json", "w") as f:
        json.dump(results, f, indent=2)

    pose_path = OUTPUT_DIR / f"{job_id}_pose.mp4"
    ok, msg, final_path = assemble_pose_video(translation["glosses"], pose_path)
    results["stages"]["assemble"] = {"status": "ok" if ok else "error", "message": msg}
    if not ok:
        results["status"] = "error"
        results["completed_at"] = datetime.now().isoformat()
        return results

    if character_url:
        polished = OUTPUT_DIR / f"{job_id}_final.mp4"
        ok, msg, final_path = polish_with_fal(final_path, character_url, polished)
        results["stages"]["polish"] = {"status": "ok" if ok else "skipped", "message": msg}
    else:
        results["stages"]["polish"] = {"status": "skipped", "message": "no character url"}

    results["final_video"] = str(final_path)
    results["status"] = "ok"
    results["completed_at"] = datetime.now().isoformat()
    with open(OUTPUT_DIR / f"{job_id}_results.json", "w") as f:
        json.dump(results, f, indent=2)
    elapsed = (datetime.now() - datetime.fromisoformat(results["started_at"])).total_seconds()
    log("PIPELINE", f"✅ Done in {elapsed:.1f}s — {final_path}")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SignBridge: Audio → ASL Signer Video")
    parser.add_argument("audio", nargs="?", help="Input audio file")
    parser.add_argument("--text", help="Text input instead of audio")
    parser.add_argument("--character", help="Character image URL for fal.ai polish")
    parser.add_argument("--output", help="Output filename prefix")
    args = parser.parse_args()
    result = run_pipeline(audio_path=args.audio, text_input=args.text, character_url=args.character, output_name=args.output)
    print(f"\n{'='*60}\nJob: {result['job_id']}\nStatus: {result['status']}")
    if result.get("final_video"):
        print(f"Video: {result['final_video']}")
    print(f"{'='*60}")