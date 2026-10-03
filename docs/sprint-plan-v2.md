# SignBridge — Sprint Plan v2 (Sprints 5–10)

> **Phase:** USABILITY — 3D motion capture + Blender pipeline
> Created: 2026-10-01
> Updated: 2026-10-02
> Status: SPRINT 6 COMPLETE
> Dataset: StudioGalt Sign Language Mocap Archive (CC0)

---

## Sprint 5: StudioGalt Download + Blender Install + Headless Test + FBX Import Test

**Goal:** Get the data, install Blender, and prove the headless FBX import pipeline works on Watchtower.

### Tasks

1. **Download StudioGalt repository**
   - `git clone https://github.com/StudioGalt/Sign-Language-Mocap-Archive.git` (or selective download — repo is large)
   - Verify structure: `SG ASL Dictionary/`, `SG ASL Fingerspelling/`, `Rigs/`, `Documentation/`
   - Count signs per letter, total count = 2,587
   - Spot-check a few sign directories: verify FBX files, .mkv preview, ReadMe.txt present
   - Download `Rigs/Galtis 8 20260401.blend` (32MB) — this is our base scene

2. **Install Blender on Watchtower**
   - Download Blender LTS (3.6 LTS or 4.2 LTS) for macOS (Intel)
   - Install to /Applications/Blender.app
   - Verify CLI: `blender --version`
   - Test headless mode: `blender --background --python-expr "import bpy; print(bpy.app.version)"`
   - **CHECK:** Metal support for Eevee on AMD 5500M (macOS Metal backend)
   - **CHECK:** Does Blender see the AMD GPU? `blender --background --python-expr "import bpy; print(bpy.app.devices)"`

3. **Blender headless render test (minimal)**
   - Create minimal scene via Python: camera, light, default cube
   - Render single frame: `blender --background --python test_minimal_render.py`
   - Verify output PNG created
   - Measure render time (CPU vs Metal GPU if available)
   - Test Eevee vs Cycles: compare render time and quality

4. **Load Galtis rig .blend headless**
   - Script: `blender --background Galtis_8_20260401.blend --python test_rig_load.py`
   - Verify: armature found, mesh found, shapekeys present
   - List bones in armature, count them
   - List available shapekeys (FACS expressions)
   - Render Galtis in T-pose — verify character renders correctly
   - Measure load time and render time

5. **FBX import test**
   - Pick a simple sign (e.g., "HELLO" or "MOTHER")
   - Import FBX (No Mesh Full variant) into Galtis scene via Python
   - Verify: armature imported, animation data present
   - Check: does imported armature match Galtis rig bone naming?
   - Render a frame from the imported animation
   - Document: import time, bone mapping differences, any errors

6. **Build initial sign index**
   - Script: walk `SG ASL Dictionary/` directory tree
   - Extract: sign name, alt number, date, FBX file paths
   - Output: `sign_index.json` — mapping of sign names to FBX paths
   - Statistics: total signs, signs with multiple alts, date range
   - This becomes the foundation for the gloss → sign lookup table

### Deliverables
- StudioGalt repository cloned and verified
- Blender installed, headless mode working, GPU/Metal status confirmed
- Galtis rig loads and renders in headless mode
- FBX import works via Python script
- `sign_index.json` — all 2,587 signs indexed with paths
- Render time benchmarks (Eevee vs Cycles, single frame)

### Estimated Time: 3–5 days

---

## Sprint 6: Galtis Rig Scene Setup + Camera + Lighting + First Render Test — ✅ DONE (2026-10-02)

**Goal:** Build the base Blender scene with camera, lighting, and render configuration. Produce the first animated sign render.

### Tasks

1. **Build base scene script (`setup_scene.py`)**
   - Load Galtis 8 .blend as base
   - Set camera position: front-facing, medium shot (waist up)
   - Configure camera: focal length, depth of field (optional)
   - 3-point lighting setup: key, fill, backlight (scriptable via Python)
   - Background: solid color or simple gradient (green screen option for later compositing)
   - Set render settings: resolution (720p target), frame rate (30fps), output format (PNG sequence or MP4)
   - Set render engine: Cycles CPU only (32-sample dev, 64-sample standard)

2. **Build FBX import + retarget script (`sign_importer.py`)**
   - Function: `import_sign_fbx(filepath) → armature, action`
   - Import FBX (No Mesh Full) into scene
   - Map imported armature bones → Galtis armature bones
   - **Key challenge:** bone name matching between FBX armature and Galtis rig
   - Test with 5+ different signs to verify mapping is consistent
   - If bone names differ: build bone mapping dictionary
   - If rigs are identical (same source): direct transfer should work

3. **Build animation transfer script**
   - Function: `transfer_animation(target_armature, retargeted_action, frame_range)`
   - Copy animation data from imported FBX armature to Galtis deform rig
   - Handle: root motion, body joints, hand bones, facial shapekeys
   - Test: import "HELLO" FBX, transfer to Galtis, render animation
   - Verify: Galtis performs the correct motion

4. **First animated sign render**
   - Full pipeline: load Galtis → import FBX → transfer animation → render
   - Render "HELLO" sign as MP4 (or PNG sequence → ffmpeg)
   - Target: 2-3 second animation at 30fps (60-90 frames)
   - Measure total pipeline time: import + transfer + render
   - Quality check: does the motion look correct? Compare to .mkv preview

5. **Render optimization**
   - Test Cycles CPU at 32/64/128 samples and 50%/100% resolution
   - Compare development, standard, and quality render costs
   - Determine: fastest acceptable render config for development
   - Determine: quality render config for final output
   - Record: render time per frame, per second of animation

6. **Batch render test (3 signs)**
   - Import and render 3 different signs independently
   - Verify each renders correctly
   - Measure: does load time dominate? Can we reuse the base scene across signs?
   - Strategy: load base scene once, import/sign/render sequentially

### Deliverables
- `setup_scene.py` — camera, lighting, render config
- `sign_importer.py` — FBX import + bone retargeting
- `render_sign.py` — orchestrator: load → import → transfer → render
- First animated sign render (MP4)
- Render time benchmarks and recommended settings
- Batch render test (3 signs)

### Estimated Time: 5–7 days

---

## Sprint 7: Gloss → StudioGalt Sign Mapping + Pose Library Build

**Goal:** Build the lookup table that maps ASL glosses to StudioGalt FBX files. Maximize coverage.

### Tasks

1. **Build gloss → sign name mapping**
   - Load ASLLVD gloss list (2,589 glosses from POC)
   - Load StudioGalt sign index (from Sprint 5: `sign_index.json`)
   - **Matching strategy (cascade):**
     1. Direct match (case-insensitive): "MOTHER" → "MOTHER"
     2. Synonym match: "MOM" → "MOTHER" (use synonym dictionary)
     3. Lemma match: "running" → "RUN" (stemming)
     4. LLM fuzzy match: use LLM to suggest closest sign for unmatched glosses
     5. Fingerspell fallback: proper nouns and unmatched → `SG ASL Fingerspelling/`
   - Output: `gloss_to_sign_map.json` — gloss → StudioGalt directory name + FBX path
   - Report: coverage %, unmatched glosses (sorted by frequency)

2. **Handle multiple versions (Alt selection)**
   - For signs with Alt 1, Alt 2, etc.: always select latest date
   - Logic: parse date from directory name, sort by date descending, pick first
   - Document: which signs have multiple versions, which is "best"

3. **Build fingerspelling lookup**
   - Index `SG ASL Fingerspelling/Letters/` — A through Z
   - Index `SG ASL Fingerspelling/Numbers/` — 0 through 9 (and common number patterns)
   - Build: `fingerspell_map.json` — letter/number → FBX path
   - Test: render "A", "B", "C" as individual signs

4. **Coverage analysis**
   - Compare: POC vocabulary (2,589 ASLLVD glosses) vs StudioGalt (2,587 signs)
   - Compute overlap: exact, synonym, lemma matches
   - Identify: high-frequency missing signs (common words not in StudioGalt)
   - Identify: StudioGalt signs not in our gloss list (potential vocabulary expansion)
   - Target: 85%+ coverage with StudioGalt + fingerspelling fallback

5. **Build pose library module (`pose_library.py`)**
   - Class: `StudioGaltLibrary`
   - Methods:
     - `lookup(gloss) → fbx_path or None`
     - `lookup_fingerspell(letter) → fbx_path`
     - `get_sign_versions(sign_name) → list of (date, fbx_path)`
     - `resolve_sign(gloss) → (fbx_path, type)` where type = "sign" or "fingerspell"
   - Load `gloss_to_sign_map.json` and `fingerspell_map.json` on init
   - Cache: keep frequently used paths in memory

6. **Integration test: gloss sequence → FBX paths**
   - Take 10 sample sentences from POC test set
   - Run through: LLM gloss → pose library lookup → FBX paths
   - Verify: all glosses resolve (sign or fingerspell fallback)
   - Report: hit rate, fingerspell rate, missing signs

### Deliverables
- `gloss_to_sign_map.json` — complete gloss → StudioGalt mapping
- `fingerspell_map.json` — letter/number → FBX mapping
- `pose_library.py` — Python module for sign lookup
- Coverage analysis report
- Integration test results (10 sentences)

### Estimated Time: 3–5 days

---

## Sprint 8: NLA Composition + Interpolation + Multi-Sign Render

**Goal:** Compose multiple signs into a single continuous animation with smooth transitions. Render a full sentence.

### Tasks

1. **Build NLA composition script (`nla_composer.py`)**
   - Function: `compose_signs(sign_list) → blended_animation`
   - For each sign:
     - Import FBX, transfer animation to Galtis rig
     - Create Action from animation data
     - Add as NLA strip on Galtis armature
   - Place strips sequentially on timeline with overlap for blending
   - Handle: strip start/end frames, blend in/out, repeat modes

2. **Interpolation between signs**
   - **Challenge:** signs end and start at different poses — need smooth transition
   - Strategy 1: Linear interpolation in blend zone (10-15 frames)
   - Strategy 2: Savitzky-Golay smoothing across sign boundaries
   - Strategy 3: Use NLA strip blend settings (Blender built-in)
   - Test all three, compare visually
   - **Key:** hands should return to neutral/rest position between signs where natural
   - Build: `interpolate_strips(strip_a_end, strip_b_start, blend_frames) → keyframes`

3. **Neutral pose handling**
   - Define: Galtis neutral/rest pose (arms down, hands at sides)
   - Strategy: insert 5-10 frame neutral pose between signs that end far from next sign's start
   - Build: `insert_neutral_pose(armature, frame, duration) → keyframes`
   - This prevents unnatural arm jumps between very different signs

4. **Multi-sign render test**
   - Test sentence: "HELLO MY NAME KELLEN" (4 signs)
   - Pipeline: gloss lookup → FBX import × 4 → NLA composition → interpolation → render
   - Target: 8-12 second animation at 30fps (240-360 frames)
   - Render with Cycles CPU at the 32-sample development setting
   - Quality check: smooth transitions, no popping, natural motion
   - Measure: total pipeline time (import + compose + render)

5. **Longer sequence test**
   - Test sentence: 8-10 signs (full sentence from POC test set)
   - Verify: pipeline scales linearly (not exponentially)
   - Measure: per-sign import time, composition time, render time
   - Identify: bottlenecks (likely: FBX import per sign, render time)

6. **Temporal smoothing pass**
   - Apply Savitzky-Golay filter across full animation for joint angles
   - Window size: 5-7 frames (tunable)
   - Target: eliminate any remaining jitter from interpolation
   - Compare: smoothed vs unsmoothed render

### Deliverables
- `nla_composer.py` — NLA strip composition with interpolation
- `interpolate_strips()` — smooth blend between sign clips
- Multi-sign render (4-sign sentence) — MP4
- Longer sequence render (8-10 signs) — MP4
- Temporal smoothing integration
- Pipeline timing report

### Estimated Time: 5–7 days

---

## Sprint 9: End-to-End Pipeline Integration + Quality Eval

**Goal:** Wire everything together. Audio in → ASL video out. Full automated pipeline.

### Tasks

1. **Build pipeline orchestrator (`signbridge_pipeline.py`)**
   - Input: audio file path
   - Steps:
     1. Whisper transcription (reuse POC module)
     2. LLM gloss translation (reuse POC module)
     3. Gloss → StudioGalt FBX lookup (Sprint 7 module)
     4. Blender headless render (Sprint 6+8 modules)
     5. Optional: Dreamactor polish (reuse POC module)
   - Output: final MP4 video
   - CLI: `python signbridge_pipeline.py --input audio.mp3 --output video.mp4`
   - API: integrate with existing FastAPI service

2. **FastAPI integration**
   - Update `/api/jobs` endpoint to use new Blender pipeline
   - Add: Blender render job status (importing, composing, rendering, done)
   - Add: render progress (frame X of Y)
   - Update dashboard: show Blender render preview/thumbnail
   - Handle: Blender process management (subprocess, timeout, error handling)

3. **Quality evaluation**
   - Test set: 20 audio clips (varying length, vocabulary)
   - For each:
     - Run full pipeline
     - Record: gloss hit rate, render time, output quality
     - Manual review: does the signing look correct? (Kellen or ASL-literate reviewer)
   - Metrics:
     - End-to-end time: target <60s for 10-second clip
     - Coverage: target 85%+ gloss hit rate
     - Quality: subjective 1-5 scale (motion, transitions, expressions)
     - Failure modes: what breaks? missing signs? render errors?

4. **Optimization pass**
   - Identify: slowest pipeline steps
   - Optimize: FBX import (cache imported actions? pre-import common signs?)
   - Optimize: render settings (lower samples for dev, higher for final)
   - Optimize: scene loading (load base scene once, reuse across renders)
   - Target: <60s total for 10-second clip at dev quality

5. **Error handling + edge cases**
   - Missing FBX file → graceful fallback to fingerspell
   - Blender crash → retry with simpler scene, log error
   - Empty gloss sequence → return error message
   - Very long audio (>30s) → chunk and concatenate renders
   - Signs with no animation data → skip with warning

6. **Documentation**
   - Update `passoff.md` with final pipeline state
   - Update README with setup + run instructions
   - Document: Blender install, StudioGalt download, config settings
   - Document: known limitations, future improvements

### Deliverables
- `signbridge_pipeline.py` — full pipeline orchestrator
- Updated FastAPI service with Blender integration
- Quality evaluation report (20 clips)
- Optimized pipeline (<60s target)
- Updated documentation

### Estimated Time: 5–7 days

---

## Sprint 10: Jev Constrained Decoding + Polish

**Goal:** Integrate Jev for structured gloss output. Polish the pipeline for production use.

### Tasks

1. **Jev constrained decoding integration**
   - Jev: structured output decoder for LLMs
   - Configure: grammar/constraint file for ASL gloss format
   - Target: eliminate invalid gloss outputs from LLM
   - Integration: replace free-form LLM gloss with Jev-constrained gloss
   - Test: does Jev work with Gemma4:cloud via Ollama? Check Ollama structured output support
   - Fallback: if Jev not compatible, use JSON mode or regex-based post-processing

2. **Gloss format standardization**
   - Define: canonical gloss format (e.g., "MOTHER^1", "IX-1p", "POSS-1p")
   - Update: gloss → StudioGalt mapping to handle canonical format
   - Update: LLM prompt to output canonical glosses
   - Test: improved gloss accuracy and lookup hit rate

3. **Facial expressions (FACS shapekeys)**
   - StudioGalt includes FACS shapekeys on Galtis rig
   - Map: ASL non-manual markers → FACS shapekey activation
   - Examples: raised eyebrows for yes/no questions, furrowed brows for WH-questions
   - Implement: keyframe shapekey values based on sentence type
   - This is a first pass — full non-manual grammar is future work

4. **Avatar consideration (OPEN)**
   - Decision needed: keep Galtis (female) or create/find male avatar?
   - If male needed: explore Mixamo-compatible rig variant, or find male character model that works with Galtis armature
   - For now: proceed with Galtis, revisit if needed

5. **Render quality polish**
   - Final render settings: Cycles, higher samples, better lighting
   - Optional: ambient occlusion, subsurface scattering on skin
   - Optional: background environment (simple studio backdrop)
   - Render: 1080p final output (up from 720p dev)

6. **Dreamactor integration test**
   - Take 3 best Blender renders
   - Run through Dreamactor v2 polish
   - Compare: Blender-only vs Blender + Dreamactor
   - Decision: is Dreamactor still needed? Blender quality may be sufficient
   - If yes: integrate as optional post-processing step

7. **Final pipeline test**
   - 5 diverse audio clips (different lengths, vocabulary, sentence types)
   - Full pipeline: audio → final video
   - Record: timing, quality, failures
   - Get Kellen's review: is this usable for real content?

### Deliverables
- Jev constrained decoding integrated (or alternative structured output)
- Canonical gloss format defined and working
- FACS facial expression first pass
- Final render quality settings
- Dreamactor integration decision
- 5-clip final pipeline test results
- Kellen review: GO / NO-GO for production use

### Estimated Time: 5–7 days

---

## Sprint Summary

| Sprint | Goal | Est. Time | Status |
|--------|------|-----------|--------|
| 5 | StudioGalt download + Blender install + headless test + FBX import | 3–5 days | ✅ DONE |
| 6 | Galtis rig scene setup + camera + lighting + first render | 5–7 days | ✅ DONE |
| 7 | Gloss → StudioGalt mapping + pose library build | 3–5 days | NEXT |
| 8 | NLA composition + interpolation + multi-sign render | 5–7 days | PLANNING |
| 9 | End-to-end pipeline integration + quality eval | 5–7 days | PLANNING |
| 10 | Jev constrained decoding + polish | 5–7 days | PLANNING |

**Total estimated time:** 26–38 days (4–7 weeks)
**Target:** Working SignBridge USABILITY pipeline by end of Sprint 10

---

## Dependencies

- **Sprint 5 → 6:** Need Blender installed + FBX import working before scene setup
- **Sprint 6 → 7:** Need render pipeline working before building lookup (can start mapping in parallel)
- **Sprint 7 → 8:** Need pose library before multi-sign composition
- **Sprint 8 → 9:** Need NLA composition before end-to-end integration
- **Sprint 9 → 10:** Need working pipeline before polish

**Parallelizable:** Sprint 7 (gloss mapping) can start during Sprint 6 (scene setup) since it's mostly data work, not Blender work.