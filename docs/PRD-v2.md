# SignBridge — Product Requirements Document v2

> **Phase:** USABILITY — Upgrading from 2D MediaPipe POC to 3D SMPL-X/MANO + Blender pipeline
> Created: 2026-10-01
> Status: PLANNING

---

## Executive Summary

SignBridge converts audio into photorealistic ASL sign language video. The POC (Sprints 1–4) proved the end-to-end pipeline works: audio → Whisper → LLM → gloss → 2D pose video → Dreamactor polish. Now we upgrade the pose pipeline from 2D MediaPipe keypoints to 3D SMPL-X/MANO motion data from the SignAvatars dataset, and replace ffmpeg concatenation with Blender headless CLI for animation composition, interpolation, and rendering.

---

## Current State (POC COMPLETE ✅)

### What Works
- **Audio → Whisper** (faster-whisper, CPU int8) → transcript with timestamps
- **Transcript → LLM rephrase** (Gemma4:cloud via Ollama) → ASL grammar gloss
- **Gloss → 2D pose lookup** (2,589 ASLLVD glosses, MediaPipe keypoints, 76% hybrid hit rate)
- **Pose concatenation** (ffmpeg concat, <1s for 13 segments)
- **Dreamactor v2 polish** (fal.ai, skeleton → photorealistic video)
- **FastAPI service** (POST /api/jobs, dashboard at signbridge.wdfab.io)
- **20 synthetic deictic signs** for pronouns (YOU, HE, SHE, WE, MY, etc.)
- **Hybrid gloss matching**: LLM rephrase + deterministic word-to-gloss, SKIP_WORDS for zero-morphemes, ALWAYS_FINGERSPELL for proper nouns

### POC Limitations
1. **2D MediaPipe poses** — 75 keypoints, no depth, poor hand/finger detail
2. **No interpolation** between sign clips — hard cuts via ffmpeg concat
3. **Limited vocabulary** — 2,589 ASLLVD glosses, many common signs missing
4. **No temporal smoothing** — robotic, jerky motion between signs
5. **Dreamactor dependency** — 2D skeleton input limits photorealistic output quality
6. **No facial expressions** — SMPL-X has jaw_pose and expression params we're not using

---

## New Pipeline (USABILITY Phase)

### Architecture

```
Audio → Whisper → LLM/Jev → Gloss Sequence
                                    ↓
                        SignAvatars Word Subset
                        (3D SMPL-X/MANO .pkl files)
                                    ↓
                        Blender Headless CLI
                        ├── Load SMPL-X model
                        ├── Apply pose data per sign
                        ├── NLA strip composition
                        ├── Interpolation between signs
                        ├── Temporal smoothing (Savitzky-Golay)
                        ├── Camera + lighting setup
                        └── Render to video
                                    ↓
                        [Optional] Dreamactor Polish
                        (Blender render → photorealistic pass)
                                    ↓
                        Final ASL Video
```

### Component Details

#### 1. SignAvatars Dataset (Primary Pose Library)

**Source:** SignAvatars (ECCV 2024) — Zhengdi Yu et al., Imperial College London / Tencent AI Lab
**GitHub:** https://github.com/ZhengdiYu/SignAvatars
**Paper:** https://arxiv.org/abs/2310.20436

**Why SignAvatars:**
- First large-scale 3D sign language motion dataset with mesh annotations
- 8.34M precise 3D whole-body SMPL-X annotations
- 70K motion sequences across 4 subsets
- SMPL-X + MANO hand annotations (detailed 3D hand poses)

**Subset: Word (WLASL) — PRIMARY**
- Individual ASL signs, each ~57 frames at 24fps (~2.4 sec avg)
- Signers standing, performing a single sign
- Annotated with word-level English glosses
- ~2,000 unique words from WLASL dataset
- Data format: `.pkl` files per sign, `smplx: (num_frames, 182)` parameters

**SMPL-X Parameter Layout (182 dims per frame):**
| Range | Parameter | Dims |
|-------|-----------|------|
| 0:3 | root_pose | 3 |
| 3:66 | body_pose | 63 (21 joints × 3) |
| 66:111 | left_hand_pose | 45 (15 MANO joints × 3) |
| 111:156 | right_hand_pose | 45 (15 MANO joints × 3) |
| 156:159 | jaw_pose | 3 |
| 159:169 | betas (shape) | 10 |
| 169:179 | expression | 10 |
| 179:182 | cam_trans | 3 |

**Other subsets (future use):**
- **HamNoSys:** 60-frame avg, single signs, HamNoSys glyph annotations
- **ASL (How2Sign):** 162-frame avg, multi-sign sentences, natural language translations
- **GSL:** Greek Sign Language (not relevant for ASL)

**Access:** Google Form required (non-commercial research license)
- Form: https://docs.google.com/forms/d/e/1FAIpQLSc6xQJJMf_R4xJ1sIwDL6FBIYw4HbVVv_HUgCqeiguWX5XGPg/viewform
- License: Non-commercial research only
- **OPEN QUESTION:** Does non-commercial license work for SignBridge? If commercial, need to contact shaolihuang@tencent.com for licensing.

**WLASL vs ASLLVD Comparison:**
| Metric | ASLLVD (current) | SignAvatars Word (new) |
|--------|------------------|------------------------|
| Unique signs | 2,746 glosses (2,589 with poses) | ~2,000 words |
| Data type | 2D video → MediaPipe 2D keypoints | 3D SMPL-X + MANO 3D poses |
| Hand detail | 75 keypoints (limited fingers) | 45-dim per hand (MANO 15-joint) |
| Body detail | 2D pose only | Full 3D body + jaw + expression |
| Frame rate | Source video dependent | 24fps standardized |
| Format | .mp4 pose videos | .pkl SMPL-X parameters |
| Source | Boston University | WLASL → SMPL-X fitting |

**Vocabulary gap analysis:**
- ASLLVD: 2,589 glosses → SignAvatars Word: ~2,000 words
- Overlap likely high (both are ASL), but exact overlap unknown until we get the data
- **OPEN QUESTION:** How many of our 2,589 ASLLVD glosses have a matching entry in SignAvatars Word subset?
- **Fallback strategy:** Retain ASLLVD/MediaPipe poses as fallback for signs not in SignAvatars

#### 2. Blender Headless CLI (Animation Engine)

**Tool:** Blender 3.1+ (or latest LTS), running in background mode
**Add-on:** SMPL-X Blender add-on (zjucxh/smplx_blender_addon or Meshcapade version)

**Blender CLI capabilities confirmed:**

```bash
# Headless mode — no GUI, fully scriptable
blender --background --python script.py

# Or with a scene file
blender --background scene.blend --python render_signs.py -- --gloss-list glosses.json

# Render specific frames
blender -b scene.blend -s 1 -e 240 -a -o //output_ -F FFMPEG

# Use Cycles or Eevee renderer
blender -b scene.blend -E CYCLES -f 1

# GPU acceleration (if available)
blender -b scene.blend -- --cycles-device METAL
```

**Key Blender Python API capabilities:**
- `bpy.ops.smplx.add_smplx_model(gender='NEUTRAL')` — Add SMPL-X model to scene
- Load poses from `.pkl` files (add-on has native .pkl pose loading)
- Create animated bodies from `.npz` files (AMASS or SMPL-X format)
- Keyframe insertion: `pose_bone.keyframe_insert(data_path="rotation_euler", frame=N)`
- Action/Pose management via `bpy.types.Action`, `bpy.types.PoseBone`
- NLA (Non-Linear Animation) tracks for composing multiple actions
- Alembic (.abc) and FBX export
- Full scene control: camera, lighting, materials, renderer settings

**Minimum Viable Blender Scene:**
1. **Human model:** SMPL-X neutral body (from add-on)
   - Shape: neutral or configurable via betas
   - Texture: sample albedo (included with add-on) or plain material
   - Pose correctives: enabled for natural deformation
2. **Hand detail:** SMPL-X includes MANO hand rig (15 joints per hand)
   - 45 pose parameters per hand from SignAvatars data
   - This is the critical upgrade — detailed finger articulation
3. **Camera:** Single static camera, 3/4 front view
   - Framed on upper body (signing area: head to waist)
   - 1920×1080 or 1280×720 resolution
4. **Lighting:** 3-point setup (key, fill, rim)
   - Studio HDRI or simple area lights
5. **Renderer:** Eevee (fast, GPU-accelerated) or Cycles (higher quality)
   - Eevee: ~0.1-0.5 sec/frame on GPU, real-time engine
   - Cycles: ~1-5 sec/frame on GPU, path-traced quality
   - **OPEN QUESTION:** Eevee vs Cycles quality/performance tradeoff for our use case
6. **Background:** Solid color or simple gradient (green screen option for compositing)

**Blender automation script architecture:**

```
blender_render.py
├── init_scene()          # Create scene, camera, lights, renderer
├── load_smplx_model()    # Add SMPL-X mesh + armature via add-on
├── load_pose_data()      # Read .pkl, extract SMPL-X params per frame
├── apply_pose_frame()    # Set bone rotations from SMPL-X params
├── create_action()       # Keyframe all bones per frame → Action
├── compose_nla()         # Stack sign Actions as NLA strips
├── interpolate()         # Add transition keyframes between strips
├── smooth_motion()       # Savitzky-Golay filter on keyframe values
├── render_animation()    # Set output path, render frames, encode video
└── cleanup()             # Remove temp data, save .blend
```

**NLA Composition approach:**
1. Each sign = one Action (keyframed bone rotations from SMPL-X data)
2. Actions placed as NLA strips on a track, sequentially
3. Between strips: interpolation strip (blend from end-pose of sign N to start-pose of sign N+1)
4. Blender NLA supports:
   - Strip blending (action interpolation, hold, replace)
   - Cross-fade transitions between strips
   - Custom blend curves per strip
5. Alternative: direct keyframe approach (no NLA, just one long action with interpolated transitions)

**Temporal Smoothing (Savitzky-Golay):**
- Apply to final keyframe data before rendering
- Window size: 7-15 frames (odd, ~0.3-0.6 sec at 24fps)
- Polynomial order: 3
- Smooths body + hand pose trajectories
- Reduces jitter from SMPL-X fitting noise
- Applied per-joint, per-rotation-axis

#### 3. Gloss → SignAvatars Mapping

**Strategy:**
1. Build mapping table: English gloss → SignAvatars Word video_id
2. Use WLASL_v0.3.json (included in dataset) as the gloss → video index
3. For each gloss in our translation output:
   a. Direct match in SignAvatars Word → use that .pkl
   b. No match → try ASLLVD fallback (2D MediaPipe pose)
   c. No match in either → fingerspell
   d. Deictic signs → retain synthetic placeholder (or generate 3D pointing pose)

**OPEN QUESTION:** Can we use the ASL (How2Sign) subset for signs missing from Word subset? How2Sign has continuous sentences — we'd need to segment them into individual signs.

**OPEN QUESTION:** Should we build a fuzzy matcher (synonym/lemmatization) for gloss → SignAvatars mapping, similar to our current gloss_remaps.py?

#### 4. Dreamactor Polish (Optional)

**Current POC:** 2D skeleton video → Dreamactor → photorealistic signer
**New pipeline:** Blender render → Dreamactor → photorealistic signer (optional)

**Key question: Do we still need Dreamactor?**

Scenarios:
1. **Blender render quality is sufficient** → Skip Dreamactor entirely. Faster, cheaper, no API dependency. Output is 3D-animated signer (clean, consistent, but not photorealistic).
2. **Blender render as Dreamactor input** → Use Blender output as the "skeleton/reference" video for Dreamactor. Better input than 2D MediaPipe (full 3D body, proper depth, hands). Dreamactor adds photorealistic skin, clothing, environment.
3. **Blender render with good materials = good enough for MVP** → Use Cycles with PBR materials for semi-realistic output. Add Dreamactor later for final polish.

**Recommendation:** Start with scenario 1 (Blender only), evaluate quality, add Dreamactor if needed (scenario 2). Blender output with good lighting and materials may be sufficient for the usability phase.

**OPEN QUESTION:** Can Blender render to video format that Dreamactor accepts as input? (Should be yes — standard MP4/H.264)

#### 5. Performance Targets

| Metric | POC (current) | Target (v2) | Stretch |
|--------|---------------|-------------|---------|
| Pose quality | 2D MediaPipe, 75 kpts | 3D SMPL-X, 182 params/frame | + MANO hand detail |
| Render time per sign | <1s (ffmpeg concat) | 5-30s (Blender Eevee) | <5s with GPU |
| Total pipeline (30s audio) | 3.3s | <2 min | <30s |
| Gloss coverage | 76% (2,589 signs) | 85%+ (SignAvatars + fallback) | 95%+ |
| Hand detail | Poor (2D, no fingers) | Good (MANO 15-joint 3D) | Excellent |
| Transitions | Hard cuts | Interpolated + smoothed | Natural motion |
| Output resolution | 640×480 (pose video) | 1920×1080 | 4K capable |

**Render time estimates (Blender headless):**
- Single sign (~57 frames at 24fps = 2.4 sec):
  - Eevee, 720p, CPU: ~30-60 sec
  - Eevee, 720p, GPU (Metal): ~5-15 sec
  - Cycles, 720p, CPU: ~2-5 min
  - Cycles, 720p, GPU (Metal): ~30-90 sec
- 30-second output (~720 frames):
  - Eevee, 720p, CPU: ~6-12 min
  - Eevee, 720p, GPU: ~1-3 min
  - Cycles, 720p, GPU: ~10-30 min

**OPEN QUESTION:** Does Watchtower's AMD 5500M 8GB support Blender GPU rendering via Metal? If not, we need a GPU machine or cloud render.

**OPEN QUESTION:** Should we pre-render individual signs to a cache (like current pose library) and compose at runtime? Or render the full sequence each time?

---

## Feature Breakdown (USABILITY Phase)

### Feature 7: 3D Pose Library (SignAvatars)

- **User story:** As the system, I need 3D SMPL-X pose data for each ASL sign
- **Acceptance criteria:**
  - [ ] SignAvatars dataset downloaded and parsed
  - [ ] WLASL Word subset indexed by gloss
  - [ ] .pkl files loadable by Blender add-on or custom Python loader
  - [ ] Pose data validated: correct dimensions, no NaN, reasonable ranges
  - [ ] Gloss → .pkl mapping table built
  - [ ] Fallback to ASLLVD/MediaPipe for missing signs
  - [ ] Coverage report: how many of our glosses have SignAvatars matches

### Feature 8: Blender Animation Engine

- **User story:** As the system, I need to compose sign animations into a fluid sequence
- **Acceptance criteria:**
  - [ ] Blender installed and running headless on Watchtower
  - [ ] SMPL-X Blender add-on installed and working in --background mode
  - [ ] Python script loads .pkl pose data → applies to SMPL-X rig → keyframes
  - [ ] Multiple signs composed as NLA strips or single action with transitions
  - [ ] Interpolation between sign end-pose and next sign start-pose (5-15 frame blend)
  - [ ] Savitzky-Golay temporal smoothing applied to keyframes
  - [ ] Scene setup: camera, lighting, renderer configured
  - [ ] Render to MP4 (H.264) at 720p minimum
  - [ ] CLI command: `blender --background --python render_pipeline.py -- --glosses [...] --output out.mp4`

### Feature 9: Updated Translation Pipeline

- **User story:** As a user, I submit audio and get a 3D-animated ASL video
- **Acceptance criteria:**
  - [ ] Pipeline: Audio → Whisper → LLM/Jev → Gloss → SignAvatars lookup → Blender render → output
  - [ ] Gloss resolution: SignAvatars primary, ASLLVD fallback, fingerspell last resort
  - [ ] Blender subprocess called from FastAPI service
  - [ ] Async job processing (Blender render is slower than ffmpeg)
  - [ ] Progress updates during render
  - [ ] Output video served at URL
  - [ ] Dashboard updated with 3D render results

### Feature 10: Quality Evaluation

- **User story:** As Kellen, I need to compare SignBridge output to commercial ASL products
- **Acceptance criteria:**
  - [ ] Side-by-side comparison: SignBridge vs commercial ASL translation tools
  - [ ] Eval metrics: hand shape accuracy, motion fluidity, comprehensibility to Deaf users
  - [ ] Render quality comparison: Eevee vs Cycles vs Dreamactor-polished
  - [ ] Coverage comparison: SignAvatars vs ASLLVD gloss hit rates
  - [ ] Speed comparison: old pipeline vs new pipeline

---

## Data Model Updates

### Job (updated)

| Field | Type | Required | Notes |
|---|---|---|---|
| id | uuid | yes | Primary key |
| status | enum | yes | pending, transcribing, translating, posing, rendering, polishing, done, error |
| audio_path | string | yes | Input audio file path |
| transcript | text | no | Whisper output |
| gloss_json | json | no | ASL gloss sequence |
| pose_sources | json | no | Per-gloss: "signavatars" \| "asllvd" \| "fingerspell" \| "deictic" |
| blender_blend_path | string | no | Intermediate .blend file |
| render_video_path | string | no | Blender render output |
| final_video_path | string | no | Final video (after optional Dreamactor) |
| render_engine | string | no | "eevee" \| "cycles" |
| render_time_sec | float | no | Time spent in Blender render |
| error | text | no | Error message if failed |
| created_at | datetime | yes | Job creation time |
| completed_at | datetime | no | Job completion time |

### SignAvatars Pose Index

| Field | Type | Notes |
|---|---|---|
| gloss | string | English word/phrase |
| video_id | string | SignAvatars video identifier |
| pkl_path | string | Path to .pkl SMPL-X file |
| num_frames | int | Number of animation frames |
| fps | int | 24 (standard for SignAvatars) |
| signer | string | Signer identifier (if available) |

---

## Technical Constraints (Updated)

- **Stack:** Python 3.10+, FastAPI, faster-whisper, Blender 3.1+ (CLI), SMPL-X Blender add-on
- **Platform:** macOS (Watchtower) for dev — Intel i9-9980HK, 32GB RAM, AMD 5500M 8GB
- **Blender:** Headless mode (`--background --python`), no GUI required
- **GPU:** AMD 5500M may support Metal rendering in Blender — **OPEN QUESTION**
- **SignAvatars:** Non-commercial research license — **OPEN QUESTION** re commercial use
- **Performance:** <2 min for 30 sec audio (Blender render is the bottleneck)
- **Fallback:** ASLLVD/MediaPipe 2D poses retained for signs not in SignAvatars

---

## Open Questions for Kellen

1. **SignAvatars license:** Non-commercial research license — is this acceptable for SignBridge? If we go commercial, need to contact Tencent (shaolihuang@tencent.com). Alternative: find or create open-license 3D ASL pose data.
2. **GPU rendering:** Does Watchtower's AMD 5500M support Blender Metal rendering? If not, need cloud GPU (RunPod, Lambda, etc.) or accept CPU render times.
3. **Eevee vs Cycles:** Eevee is faster but lower quality. Cycles is photoreal but slow. Which for MVP?
4. **Dreamactor necessity:** If Blender render quality is good enough, do we drop Dreamactor? Saves cost + complexity. Can always add later.
5. **Pre-render cache:** Pre-render individual signs to video clips (like current pose library) and compose at runtime? Or render full sequence each time?
6. **WLASL coverage overlap:** How many of our 2,589 ASLLVD glosses exist in WLASL's 2,000 words? Need to evaluate after dataset access.
7. **How2Sign for gaps:** Use ASL subset (How2Sign continuous sentences) for signs missing from Word subset? Requires sentence segmentation.
8. **Jev timing:** Should Jev integration happen in Sprint 10 as planned, or earlier? Jev could improve gloss matching before we build the SignAvatars mapping.
9. **Blender version:** Latest LTS (4.2+) or stable 3.x? SMPL-X add-on tested on 3.1.0. Need to verify compatibility with newer Blender.

---

## Non-Goals (USABILITY Phase)

- Real-time/streaming translation
- Multi-language sign languages (ASL only)
- Custom signer appearance (single neutral avatar)
- User authentication
- Mobile app
- Batch processing
- Fine-tuning SMPL-X model on additional ASL data

---

## Success Criteria (USABILITY Phase)

1. **3D pose quality:** Hand shapes are recognizable to ASL-literate viewers (MANO 15-joint articulation)
2. **Motion fluidity:** Transitions between signs are smooth, no hard cuts
3. **Coverage:** 85%+ gloss hit rate with SignAvatars + ASLLVD fallback
4. **Speed:** <2 min total pipeline for 30 sec audio
5. **Visual quality:** Output is presentable — clean 3D avatar, good lighting, readable at 720p
6. **Comparison:** Comparable or better than at least one commercial ASL translation product