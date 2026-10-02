# SignBridge — Product Requirements Document v2

> **Phase:** USABILITY — Upgrading from 2D MediaPipe POC to 3D motion capture + Blender pipeline
> Created: 2026-10-01
> Updated: 2026-10-01
> Status: PLANNING

---

## Executive Summary

SignBridge converts audio into photorealistic ASL sign language video. The POC (Sprints 1–4) proved the end-to-end pipeline works: audio → Whisper → LLM → gloss → 2D pose video → Dreamactor polish. Now we upgrade the pose pipeline from 2D MediaPipe keypoints to 3D motion capture data from the **StudioGalt Sign Language Mocap Archive**, and replace ffmpeg concatenation with **Blender headless CLI** for animation composition, interpolation, and rendering.

**Key decision:** StudioGalt is our primary dataset, not SignAvatars. StudioGalt offers CC0 licensing (commercially safe), immediate availability (no Google Form gatekeeping), real motion capture data (Xsens Link suits + StretchSense finger gloves), and a Blender-native workflow that directly matches our rendering pipeline.

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
6. **No facial expressions** — StudioGalt includes FACS shapekeys for facial expressions

---

## New Pipeline (USABILITY Phase)

### Architecture

```
Audio → Whisper → LLM/Jev → Gloss Sequence
                                    ↓
                        StudioGalt FBX Lookup
                        (2,587 signs, real mocap)
                                    ↓
                        Blender Headless CLI
                        ├── Load Galtis rig .blend (base scene)
                        ├── Import FBX per sign
                        ├── Retarget motion to Galtis armature
                        ├── NLA strip composition (sequential signs)
                        ├── Interpolation between sign clips
                        ├── Camera + lighting setup
                        └── Render to video (Eevee or Cycles)
                                    ↓
                        [Optional] Dreamactor Polish
                        (Blender render → photorealistic pass)
                                    ↓
                        Final ASL Video
```

### Component Details

#### 1. StudioGalt Sign Language Mocap Archive (Primary Pose Library)

**Source:** StudioGalt — https://github.com/StudioGalt/Sign-Language-Mocap-Archive
**License:** CC0 (Public Domain) — no restrictions, commercially safe
**Availability:** Available NOW — no Google Form, no waiting, no gatekeeping

**Why StudioGalt:**
- 2,587 ASL signs with real motion capture (not estimated/annotated)
- Professional equipment: Xsens Link suits + StretchSense finger gloves
- Recorded at 240fps, posted at 60fps — high temporal precision
- Blender-native workflow (their primary software is Blender)
- FBX format with mesh + armature — directly importable
- FACS facial expression shapekeys included
- CC0 license — commercially safe, no restrictions

**Dataset Structure:**
- `SG ASL Dictionary/` — 2,587 sign directories organized by first letter (A through Y)
  - Each sign directory: FBX files (Mesh, No Mesh Full, No Mesh Mini, No Mesh Mixamo), .mkv preview, ReadMe.txt, ShapeKeys.txt, CC.gif
  - Naming: `SG ASL {SignName} {Alt#} {YYYY-M-D} Upload/`
  - Multiple versions per sign (Alt 1, Alt 2, etc.) — newer dates = more accurate
- `SG ASL Fingerspelling/` — Letters and Numbers subdirectories
- `Rigs/` — Blender .blend files with Galtis avatar rig
  - Latest: `Galtis 8 20260401.blend` (32MB)
  - Includes mesh, armature, shapekeys (FACS facial expressions), correction bones
  - Rig flow: FK/IK → intermediate rig → deform rig
- `Documentation/Scripts/` — Blender Python scripts for import/export pipeline
  - Importer (Xsens 240fps, Rokoko 30fps), SuperSet, Baker, Layer Update, Pose Magic
  - Archive, Exporter, Triple 6, Bundler
- `Documentation/Workflows/` — Video and docx tutorials

**FBX Variants per Sign:**
- **Mesh** — Full character with mesh (for rendering)
- **No Mesh Full** — Armature only, full data (for retargeting)
- **No Mesh Mini** — Compact armature (for pipeline use)
- **No Mesh Mixamo** — Mixamo-compatible rig (for alternative avatars)

#### 2. Whisper (Unchanged from POC)

- faster-whisper, CPU int8 quantization
- Transcript with word-level timestamps
- Runs on Watchtower (Intel i9)

#### 3. LLM Gloss Translation (Unchanged from POC, Jev Later)

- Gemma4:cloud via Ollama for rephrasing English → ASL grammar gloss
- Hybrid matching: LLM rephrase + deterministic word-to-gloss
- SKIP_WORDS for zero-morphemes, ALWAYS_FINGERSPELL for proper nouns
- **Sprint 10:** Jev constrained decoding for structured gloss output

#### 4. Gloss → StudioGalt Sign Mapping (NEW)

- Build mapping table: ASL gloss → StudioGalt sign directory name
- StudioGalt naming uses English words (e.g., "MOTHER", "HELLO"), not glosses
- Strategy: direct match → synonym match → lemma match → fingerspell fallback
- Handle multiple versions (Alt 1, Alt 2) — always use latest date
- Signs not in StudioGalt: fallback to fingerspelling using `SG ASL Fingerspelling/`

#### 5. Blender Headless Pipeline (NEW — Core Upgrade)

**Runtime:** `blender --background --python render_pipeline.py`

**Pipeline steps:**
1. **Load base scene** — Open Galtis rig .blend (Galtis 8 20260401.blend)
2. **Import FBX per sign** — Load FBX (No Mesh Full) for each sign in gloss sequence
3. **Retarget motion** — Map imported armature animation to Galtis deform rig
4. **NLA composition** — Create NLA strips for each sign, place sequentially on timeline
5. **Interpolation** — Blend between end-of-sign and start-of-next-sign (10-15 frame blends)
6. **Camera + lighting** — Scriptable 3-point lighting, fixed camera angle (front-facing signer)
7. **Render** — Eevee (fast, GPU-friendly) or Cycles (quality, slower)
8. **Export** — Render to MP4/PNG sequence

**Blender Python Scripts (from StudioGalt Documentation):**
- StudioGalt provides import/export scripts we can adapt:
  - Importer (Xsens 240fps, Rokoko 30fps) — for raw mocap data
  - Baker — bake animation to keyframes
  - Exporter — FBX export
  - Pose Magic — pose correction utilities
- We write our own: `render_pipeline.py` (orchestrator), `sign_importer.py` (FBX → Galtis retarget), `nla_composer.py` (NLA strip assembly + interpolation)

**Hardware considerations (Watchtower):**
- Intel i9, AMD 5500M (no NVIDIA CUDA)
- Eevee: GPU-accelerated via Metal (macOS), fast preview rendering
- Cycles: CPU-only on macOS (no OptiX), slower but higher quality
- Target: Eevee for development, Cycles for final quality renders

#### 6. Dreamactor Polish (Optional, Unchanged)

- fal.ai Dreamactor v2 — skeleton/video → photorealistic
- Input: Blender render (much higher quality than POC 2D skeletons)
- Expected improvement: 3D-rendered input → significantly better photorealistic output
- Can be disabled for faster turnaround if Blender render quality is sufficient

---

## Open Questions

1. **Galtis gender** — Galtis is a female avatar. Fabio (the target signer character) is male. Do we need a male avatar swap? Options: (a) use Galtis as-is for now, (b) find/create male variant, (c) use Mixamo-compatible rig with a male character model.

2. **Gloss → StudioGalt sign name mapping** — StudioGalt directories use English words ("MOTHER", "HELLO"), not ASL glosses ("MOTHER^1", "IX-1p"). How do we bridge this? Build a lookup table? Use LLM for fuzzy matching? Manual curation for top-N signs?

3. **Signs not in StudioGalt** — 2,587 signs is a good start but won't cover everything. Fallback strategy: fingerspell using `SG ASL Fingerspelling/` letters. Later: supplement with SignAvatars (future work).

4. **FBX import + retargeting automation** — Can we fully automate FBX import and retargeting via Python script? StudioGalt provides import scripts but we need to adapt them for headless pipeline. Their rig has FK/IK → intermediate → deform layers — how much of this is scriptable?

5. **Render quality vs speed on Watchtower** — Intel i9 + AMD 5500M. Eevee should work via Metal. Cycles CPU-only may be too slow for iterative dev. What's the render time per frame? Per second of animation? Need benchmarks.

6. **Galtis rig complexity** — The Galtis 8 rig has FK/IK switching, intermediate rig, correction bones, FACS shapekeys. Can we use it as-is for headless rendering, or do we need a simplified version for speed? The complexity may slow down evaluation/iteration cycles.

7. **Animation retargeting** — StudioGalt FBX files contain animation on their armature. We need to transfer this to the Galtis rig. Is the armature structure identical across all FBX files? Do we need per-sign retargeting or is it uniform?

8. **Frame rate handling** — StudioGalt records at 240fps, posts at 60fps. Our pipeline should output at 30fps (standard video) or 60fps (smooth). What's the right target? Does downsampling lose motion quality?

---

## Success Criteria (USABILITY Phase)

1. **Vocabulary:** 2,000+ signs from StudioGalt mapped and renderable
2. **Quality:** Smooth interpolation between signs (no hard cuts)
3. **Render:** Blender headless produces viewable ASL video at 720p+
4. **Speed:** Full pipeline (audio → video) completes in <60 seconds for a 10-second clip
5. **Coverage:** 85%+ gloss hit rate (up from 76% with StudioGalt + fingerspelling fallback)
6. **Facial expressions:** FACS shapekeys utilized for non-manual markers
7. **End-to-end:** Single command produces final video from audio input

---

## Non-Goals (This Phase)

- Real-time translation (batch/on-demand is fine)
- Multi-signer support (single avatar for now)
- Mobile app (web dashboard is sufficient)
- SignAvatars integration (future work — see `future-work-signavatars.md`)
- Video-to-3D pose extraction from YouTube (future research — see Future Research section below)
- Custom avatar creation (use Galtis or available alternatives)
- Full ASL grammar (gloss-level translation, not full linguistic accuracy)

---

## Dependencies

- **Blender 3.1+** (LTS preferred) — headless CLI on macOS
- **StudioGalt repository** — git clone or selective download
- **Whisper** (faster-whisper) — already installed from POC
- **Ollama** (Gemma4:cloud) — already configured from POC
- **fal.ai API** (Dreamactor) — already configured, optional in new pipeline
- **Python 3.10+** — for Blender scripting and pipeline orchestration

---

## License Considerations

- **StudioGalt:** CC0 (Public Domain) — no restrictions, commercially safe ✅
- **SignAvatars:** Non-commercial only — saved as future work ⏸️
- **Blender:** GPL — fine for our use case (output is not copyleft)
- **Our code:** Kellen's choice (proprietary or open source)

---

## Future Research: Video-to-3D Pose Extraction

**Goal:** Extract 3D pose/motion data directly from 2D video (YouTube ASL interpreters, etc.) to expand the lexicon beyond StudioGalt's 2,587 signs.

**Why it matters:** StudioGalt has ~2,587 signs. ASL has 5,000+ signs. Video-to-3D would let us mine YouTube content for new signs and grow the library continuously.

**Approaches to evaluate:**
- MediaPipe Holistic 3D (estimates 3D from 2D video — lower quality but free)
- SMPL-X regression models (video → 3D mesh, e.g., PIXIE, SMPLer-X)
- MotionBERT / PoseFormer (2D-to-3D lift from video)
- Unreal Engine ML Deformer (game pipeline, potentially relevant)
- Open-source: VIBE, MEVA, GLEE (temporal 3D pose from video)

**ASL-specific challenges:**
- Fine handshapes (finger spelling, hand positions) need high-fidelity hand tracking
- Facial expressions (non-manual markers) need FACS-compatible capture
- Two-handed signs need separate tracking of both hands
- Signers in YouTube videos are often full-body with varying camera angles

**Status:** Research only. Not in current sprints. Revisit after USABILITY phase proves the Blender pipeline.

---

## Future Research: Grappling/BJJ Skeleton Tracking (Side Quest)

**Goal:** 2D video → skeleton tracking for jiu jitsu/grappling analysis, maintaining fidelity between two players (not mixing up athletes or picking up the referee).

**Why it matters:** Kellen's jiu jitsu practice — technique analysis, match breakdown.

**Challenges:**
- Two-person tracking without identity bleed (most pose trackers lose person identity during close contact)
- Referee interference (third body in frame)
- Gi vs no-gi changes visual appearance significantly
- Close contact / tangled positions break standard pose estimators

**Potential approaches:**
- ByteTrack / BoT-SORT (multi-object tracking with pose)
- MMPose with person re-identification
- Custom fine-tuning on grappling footage

**Status:** Side quest. Not in current sprints. Save for when SignBridge pipeline is stable.