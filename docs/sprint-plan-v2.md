# SignBridge — Sprint Plan v2 (Sprints 5–10)

> **Phase:** USABILITY — 3D SMPL-X/MANO + Blender pipeline
> Created: 2026-10-01
> Status: PLANNING

---

## Sprint 5: SignAvatars Access + Data Evaluation + Blender Install

**Goal:** Get the data, evaluate it, and prove Blender headless works on Watchtower.

### Tasks

1. **Request SignAvatars access**
   - Fill out Google Form: https://docs.google.com/forms/d/e/1FAIpQLSc6xQJJMf_R4xJ1sIwDL6FBIYw4HbVVv_HUgCqeiguWX5XGPg/viewform
   - Wait for email with download links
   - Download Word subset (WLASL) annotations + WLASL_v0.3.json
   - Download human_model_files (SMPL-X, MANO model files)

2. **Download and install Blender**
   - Install Blender 3.1+ (LTS preferred) on Watchtower
   - Verify CLI: `blender --version`
   - Test headless mode: `blender --background --python-expr "import bpy; print(bpy.app.version)"`
   - **OPEN QUESTION:** Check AMD 5500M Metal support for GPU rendering

3. **Install SMPL-X Blender add-on**
   - Download from: https://github.com/zjucxh/smplx_blender_addon (or Meshcapade version)
   - Install via Blender preferences (or copy to addons folder)
   - Test in headless mode: load add-on, add SMPL-X model, verify mesh created
   - Script: `blender --background --python test_smplx_addon.py`

4. **Parse SignAvatars Word data**
   - Load WLASL_v0.3.json — index words → video_ids
   - Load sample .pkl files — verify SMPL-X param dimensions (182,)
   - Extract parameter breakdown: root_pose, body_pose, hand_poses, jaw, betas, expression, cam_trans
   - Build initial gloss → pkl_path mapping table
   - Statistics: how many unique words, average frames per sign, any missing/corrupt files

5. **Coverage analysis: ASLLVD glosses vs WLASL words**
   - Load our 2,589 ASLLVD glosses
   - Load WLASL 2,000 words
   - Compute overlap: exact match, case-insensitive match, lemma match
   - Report: X% of our glosses found in SignAvatars Word subset
   - Identify high-frequency missing signs (common words not in WLASL)

6. **Blender headless render test**
   - Create minimal scene: camera, light, default cube
   - Render single frame via CLI: `blender -b test.blend -f 1 -o //test_ -F PNG`
   - Verify output PNG created
   - Test with SMPL-X model: add model, set T-pose, render single frame
   - Measure render time (CPU vs GPU if available)

### Deliverables
- SignAvatars dataset downloaded and parsed
- WLASL → gloss mapping table (initial)
- Coverage analysis report (ASLLVD vs WLASL overlap)
- Blender installed, headless mode verified, SMPL-X add-on working
- Single-frame SMPL-X render test completed

### Estimated Time: 3-5 days

---

## Sprint 6: SMPL-X to Blender Rig Pipeline + Minimal Scene Setup

**Goal:** Load SignAvatars .pkl pose data into Blender, apply to SMPL-X rig, and render a single sign animation.

### Tasks

1. **Build SMPL-X pose loader (Python)**
   - Function: `load_smplx_pkl(pkl_path) → dict of param arrays`
   - Parse 182-dim SMPL-X params into components (root, body, hands, jaw, betas, expr, cam)
   - Handle both `smplx` (smooth) and `unsmooth_smplx` keys
   - Validate: check dimensions, NaN check, range check

2. **Build Blender pose applicator (Python)**
   - Function: `apply_smplx_to_rig(armature, smplx_params, frame)`
   - Map SMPL-X body_pose (63-dim, 21 joints × 3) to Blender bone rotations
   - Map MANO hand_pose (45-dim, 15 joints × 3) to hand bone rotations
   - Set root_pose, jaw_pose, betas, expression
   - Insert keyframes for all bones at the given frame

3. **Build sign-to-action converter**
   - Input: .pkl file for one sign
   - Output: Blender Action with keyframes for all frames in the sign
   - Process: for each frame in .pkl, apply pose and insert keyframes
   - Save Action to Blender data (named by gloss)

4. **Set up minimal Blender scene**
   - Scene file: `signbridge_scene.blend`
   - SMPL-X neutral model added and positioned (feet on ground, facing camera)
   - Camera: 3/4 front view, upper body framing, 1280×720
   - Lighting: 3-point setup (key area light, fill area light, rim area light)
   - Background: solid neutral color (or green screen plane)
   - Renderer: Eevee (for speed) with ambient occlusion + soft shadows
   - World: simple HDRI or uniform color

5. **Render single sign test**
   - Pick a common sign from SignAvatars (e.g., "HELLO" or "MY")
   - Load .pkl → apply to rig → create Action → render to MP4
   - CLI: `blender --background signbridge_scene.blend --python render_sign.py -- --pkl hello.pkl --output hello.mp4`
   - Verify output: correct pose, hands visible, smooth motion
   - Measure render time per frame and total

6. **Batch render test (5 signs)**
   - Render 5 different signs individually
   - Verify each produces correct output
   - Measure average render time per sign
   - Save individual sign Actions to .blend library file

### Deliverables
- `smplx_loader.py` — Python module to load and parse .pkl files
- `blender_pose_applicator.py` — Blender Python script to apply SMPL-X params to rig
- `signbridge_scene.blend` — Minimal Blender scene with SMPL-X model, camera, lights
- `render_sign.py` — CLI script: load .pkl, apply pose, render single sign to video
- 5 test sign videos rendered
- Render time benchmarks (per-frame, per-sign)

### Estimated Time: 5-7 days

---

## Sprint 7: Gloss to SignAvatars Mapping + Pose Library Rebuild

**Goal:** Build the complete gloss → 3D pose mapping table, with fallbacks.

### Tasks

1. **Build gloss → SignAvatars mapping**
   - Parse WLASL_v0.3.json: extract all words → video_ids
   - Match against our 2,589 ASLLVD glosses:
     - Exact match (case-insensitive)
     - Lemma match (run → RUN, running → RUN)
     - Synonym match (using existing gloss_remaps.py logic)
   - For matched glosses: record video_id, pkl_path, num_frames
   - For unmatched glosses: mark as "needs fallback"

2. **Build fallback chain**
   - Tier 1: SignAvatars Word subset (3D SMPL-X)
   - Tier 2: ASLLVD/MediaPipe 2D poses (existing pose library)
   - Tier 3: Deictic synthetic signs (existing 20 pronouns)
   - Tier 4: Fingerspelling (letter-by-letter)
   - Track source per gloss in pose_lookup_v2.json

3. **Pre-process SignAvatars .pkl files**
   - For each matched gloss, load .pkl and validate
   - Convert to standardized format if needed (ensure 182-dim smplx key)
   - Cache processed pose data for fast loading
   - Build index file: `signavatars_pose_index.json`

4. **Update gloss_remaps.py**
   - Add SignAvatars-specific remaps (WLASL word variations)
   - Update SKIP_WORDS, ALWAYS_FINGERSPELL if WLASL coverage differs
   - Add synonym mapping for WLASL words not in ASLLVD

5. **Coverage report**
   - Total glosses: 2,589
   - SignAvatars matches: X (X%)
   - ASLLVD fallback: Y (Y%)
   - Deictic: 20 (0.8%)
   - Fingerspell: Z (Z%)
   - Target: 85%+ covered by Tier 1+2

6. **Update FastAPI stats endpoint**
   - Report pose source distribution
   - Report coverage by tier
   - Update dashboard with 3D library stats

### Deliverables
- `signavatars_pose_index.json` — Gloss → .pkl mapping
- `pose_lookup_v2.json` — Updated pose lookup with source tiers
- Updated `gloss_remaps.py` with SignAvatars remaps
- Coverage report with tier breakdown
- Updated dashboard stats

### Estimated Time: 3-5 days

---

## Sprint 8: Blender NLA Composition + Interpolation + Render Pipeline

**Goal:** Compose multiple signs into a fluid animation with transitions, and render the full sequence.

### Tasks

1. **Build NLA composition system**
   - Function: `compose_signs_nla(armature, sign_actions, transitions)`
   - For each sign Action: add as NLA strip on a track
   - Between strips: add transition (blend) — 10-15 frame cross-fade
   - Use Blender NLA API: `bpy.context.object.animation_data.nla_tracks`
   - Strip blending mode: `action_blend_type='LINEAR'` or custom curve
   - Alternative approach: single Action with all keyframes + interpolated transitions

2. **Build interpolation engine**
   - Between sign N end-pose and sign N+1 start-pose:
     - Extract end-frame pose (all bone rotations) from sign N
     - Extract start-frame pose from sign N+1
     - Generate 10-15 frame interpolation (linear, ease-in-out, or slerp for rotations)
     - Insert as keyframes between sign clips
   - Handle rest pose: signs start/end from a neutral rest pose, so transitions go: sign → rest → sign (more natural than sign → sign directly)

3. **Implement Savitzky-Golay temporal smoothing**
   - Apply to full keyframe sequence after composition
   - Per-bone, per-rotation-axis: smooth the keyframe value sequence
   - Window: 7-15 frames (odd), polynomial order 3
   - Use `scipy.signal.savgol_filter` on extracted keyframe arrays
   - Re-insert smoothed keyframes
   - Verify: motion is smooth, no jitter, hands still readable

4. **Build full pipeline render script**
   - `render_pipeline.py`:
     ```
     Input: gloss list + output path
     1. Init scene (load signbridge_scene.blend)
     2. For each gloss:
        a. Look up pose source (SignAvatars / ASLLVD / fingerspell)
        b. Load pose data
        c. Create Action (keyframes from pose data)
     3. Compose all Actions as NLA strips
     4. Add interpolation transitions
     5. Apply Savitzky-Golay smoothing
     6. Set render settings (fps, resolution, output format)
     7. Render animation to MP4
     8. Save .blend (optional, for debugging)
     9. Return output path
     ```
   - CLI: `blender --background signbridge_scene.blend --python render_pipeline.py -- --glosses HELLO MY NAME KELLEN --output out.mp4`

5. **Handle fallback signs in Blender**
   - For ASLLVD 2D fallback: render 2D pose video as plane texture in Blender? Or just concat 2D video after Blender render?
   - **OPEN QUESTION:** How to handle mixed 3D/2D signs in output? Options:
     a. Render only 3D signs in Blender, concat 2D signs via ffmpeg
     b. Project 2D poses onto a plane in Blender scene
     c. Generate 3D SMPL-X poses from 2D MediaPipe data (uplifting)
   - For fingerspelling: generate letter-by-letter 3D hand poses (or use pre-rendered clips)
   - For deictic signs: generate 3D pointing poses (index finger point)

6. **Performance optimization**
   - Pre-render common signs to cache (sign video clips)
   - Compose cached clips + render only transitions
   - This could reduce render time dramatically (render 10-15 transition frames vs 57 frames per sign)
   - **OPEN QUESTION:** Cache strategy — per-sign video clips or per-sign .blend Actions?

7. **End-to-end Blender render test**
   - Input: "Hello, my name is Kellen, I want to tell you about something exciting"
   - Gloss: HELLO MY NAME K-E-L-L-E-N I WANT TELL YOU ABOUT SOMETHING EXCITING
   - Render full sequence with transitions and smoothing
   - Measure total render time
   - Evaluate output quality

### Deliverables
- `render_pipeline.py` — Full Blender CLI render script
- `nla_composer.py` — NLA strip composition module
- `interpolation.py` — Transition interpolation between signs
- `smoothing.py` — Savitzky-Golay temporal smoothing
- Full sequence test render (8+ signs with transitions)
- Render time benchmarks (per-sign and full-sequence)
- Quality evaluation: hand shapes, motion fluidity, transition naturalness

### Estimated Time: 7-10 days

---

## Sprint 9: End-to-End Integration + Quality Evaluation

**Goal:** Wire the new Blender pipeline into the FastAPI service, evaluate quality against commercial products.

### Tasks

1. **Integrate Blender pipeline into FastAPI**
   - Update `pipeline.py`:
     - Audio → Whisper → LLM → Gloss (unchanged)
     - Gloss → pose source resolution (SignAvatars / ASLLVD / fingerspell)
     - Pose data → Blender subprocess → render video
     - Optional: Blender render → Dreamactor polish
   - Blender called as subprocess: `subprocess.run(["blender", "--background", ...])`
   - Async processing with progress updates
   - Job status: ...rendering... (new status)
   - Handle Blender errors (crash, timeout, missing .pkl)

2. **Update API endpoints**
   - POST /api/jobs — accept audio, start pipeline
   - GET /api/jobs/{id} — include render progress, pose sources
   - GET /api/jobs/{id}/video — serve rendered video
   - GET /api/stats — include 3D library stats, render time averages
   - New: GET /api/jobs/{id}/blend — download .blend file (debugging)

3. **Update dashboard**
   - New pipeline diagram (3D flow)
   - Render progress indicator
   - 3D vs 2D pose source distribution chart
   - Sample 3D render videos
   - Sprint 9 demo section
   - Comparison: old pipeline vs new pipeline

4. **Quality evaluation**
   - Render same test sentences with both pipelines (2D vs 3D)
   - Compare:
     - Hand shape accuracy (can ASL-literate viewer read the signs?)
     - Motion fluidity (transitions, smoothing)
     - Visual quality (lighting, materials, framing)
     - Render time
   - Compare against commercial ASL products:
     - **OPEN QUESTION:** Which commercial products to compare against? (e.g., SignAll, OmniBridge, Avatar ASL)
   - Gather feedback from ASL-literate reviewers if possible

5. **Dreamactor evaluation (optional)**
   - Take best Blender render → run through Dreamactor
   - Compare: Blender-only vs Blender+Dreamactor
   - Decide: is Dreamactor worth the cost + time?
   - If yes: wire Dreamactor as optional post-processing step
   - If no: mark Dreamactor as deprecated for v2 pipeline

6. **Performance optimization pass**
   - Profile render pipeline: where is time spent?
   - Optimize: reduce samples, simplify materials, lower resolution if needed
   - Test cache strategy: pre-rendered sign clips vs full render
   - Target: <2 min for 30 sec audio

### Deliverables
- Updated `pipeline.py` with Blender integration
- Updated API + dashboard
- Quality evaluation report (2D vs 3D vs commercial)
- Performance benchmarks (optimized pipeline)
- Decision document: Dreamactor yes/no
- Sprint 9 demo on dashboard

### Estimated Time: 5-7 days

---

## Sprint 10: Jev Integration for Constrained Gloss Decoding

**Goal:** Replace LLM rephrasing with Jev (TypeSafe AI) for constrained, hallucination-free gloss matching.

### Tasks

1. **Set up OpenRouter Decisions API**
   - Verify OpenRouter API key in `~/.openclaw/credentials/`
   - Test Jev endpoint: `POST https://openrouter.ai/api/alpha/decisions`
   - Model: `typesafe/jev-1.13`
   - Format: `state` (text to translate) + `questions` (typed: choice, noul, score)

2. **Design Jev question schema for gloss matching**
   - **Choice question:** "Which ASL gloss matches this English word?"
     - Criteria: list of available glosses (or subset for vocabulary)
     - Returns: probability distribution over glosses
   - **Noul question:** "Translate this sentence to ASL gloss sequence"
     - Returns: structured gloss output
   - **Score question:** "Is this gloss translation accurate? (0-1)"
     - Returns: confidence score for validation

3. **Build Jev gloss matcher**
   - Input: English word/phrase + available glosses
   - Output: best-matching gloss + confidence
   - Batch: send multiple words per call (shared state, multiple questions)
   - Cache: store results to avoid repeat API calls
   - Fallback: if Jev confidence < threshold, use LLM rephrase or fingerspell

4. **Integrate Jev into pipeline**
   - Replace `llm_rephrase_and_map()` in `pipeline.py`
   - Jev handles: English → ASL grammar rephrase → gloss selection
   - Constrained: Jev can only output glosses from our vocabulary (no hallucinations)
   - Track: Jev confidence per gloss, low-confidence glosses flagged

5. **Accuracy comparison: Jev vs LLM**
   - Test with same sentences used in Sprint 2
   - Compare gloss match rates:
     - LLM (Gemma4:cloud): 76% (current baseline)
     - Jev: target 85%+
   - Test with edge cases:
     - Proper nouns (should fingerspell)
     - Idioms (should rephrase to available signs)
     - ASL-specific grammar (topic-comment structure, wh-questions)

6. **Update pipeline configuration**
   - Config: `GLOSS_MATCHER = "jev" | "llm" | "hybrid"`
   - Hybrid mode: Jev primary, LLM fallback for low-confidence
   - Log: matcher used per gloss, confidence, time taken

7. **Update dashboard**
   - Show matcher type (Jev/LLM/hybrid) in job details
   - Gloss match accuracy stats
   - Jev vs LLM comparison chart

### Deliverables
- `jev_gloss_matcher.py` — Jev integration module
- Updated `pipeline.py` with Jev/hybrid matcher
- Accuracy comparison report (Jev vs LLM)
- Updated dashboard with matcher stats
- Sprint 10 demo

### Estimated Time: 5-7 days

---

## Sprint Summary

| Sprint | Goal | Est. Time | Key Deliverable |
|--------|------|-----------|-----------------|
| 5 | Data access + Blender install | 3-5 days | SignAvatars data + Blender headless working |
| 6 | SMPL-X → Blender rig pipeline | 5-7 days | Single sign 3D render |
| 7 | Gloss mapping + pose library | 3-5 days | 85%+ coverage with 3D poses |
| 8 | NLA composition + render pipeline | 7-10 days | Full sequence 3D render with transitions |
| 9 | E2E integration + quality eval | 5-7 days | Updated API + quality report |
| 10 | Jev integration | 5-7 days | Constrained gloss matching, 85%+ accuracy |

**Total estimated time: 28-41 days (4-6 weeks)**

---

## Dependencies & Blockers

1. **SignAvatars access** (Sprint 5) — Google Form approval required. Could take days.
2. **Blender GPU support** (Sprint 5) — AMD 5500M Metal support unknown. If no GPU, CPU render times acceptable but slower.
3. **SMPL-X model files** (Sprint 5) — Need SMPL-X model files from smpl-x.is.tue.mpg.de (free academic license) or Dropbox link in SignAvatars repo.
4. **OpenRouter key** (Sprint 10) — Kellen needs to verify/add API key.
5. **Watchtower performance** — Intel i9, 32GB RAM. Blender CPU rendering should work but may be slow. GPU uncertain.

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| SignAvatars access denied | Fall back to ASLLVD + uplift 2D to pseudo-3D, or find alternative 3D ASL datasets |
| No GPU rendering on Watchtower | Use cloud GPU (RunPod, Modal) for rendering, or accept CPU render times |
| WLASL coverage too low | Use How2Sign subset for additional signs, or retain ASLLVD 2D for larger coverage |
| Blender too slow for production | Pre-render sign library to video clips, compose only transitions |
| SMPL-X add-on incompatible with Blender version | Use tested Blender 3.1.0, or patch add-on for newer versions |
| Non-commercial license blocks commercial use | Contact Tencent for commercial license, or use only open-license data |