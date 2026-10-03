# SignBridge — Project Passoff Document

> Created: 2026-10-01 07:10 MST
> Updated: 2026-10-02 21:12 MST
> Purpose: Full context handoff for session continuity

---

## What Is SignBridge

SignBridge takes audio (voice notes, rambles, any spoken content) and produces a video of an ASL signer performing the translation. The pipeline uses open-source tooling for the signing animation and optional video generation for photorealistic polish. On-demand — one audio file in, one video out.

## Project Location

- **Code:** `~/projects/signbridge/`
- **Dashboard:** https://signbridge.wdfab.io (port 18105, Cloudflare tunnel)
- **GitHub:** https://github.com/Chased1k/signbridge — created and pushed
- **PRD v1:** `~/projects/signbridge/docs/prd.md` (POC phase)
- **PRD v2:** `~/projects/signbridge/docs/PRD-v2.md` ← USABILITY phase plan (StudioGalt)
- **Sprint Plan v2:** `~/projects/signbridge/docs/sprint-plan-v2.md` ← Sprints 5-10
- **SignAvatars future work:** `~/projects/signbridge/docs/future-work-signavatars.md`
- **Tech Debt:** `~/projects/signbridge/docs/tech-debt.md`
- **Promo Script:** `~/projects/signbridge/docs/promo-script.md`
- **Workspace project doc:** `~/projects/Speech-to-Sign-Language-Video.md`

---

## POC Status: COMPLETE ✅

The POC is fully functional end-to-end:

```
Audio → Whisper (CPU) → LLM (Gemma4:cloud) → ASL Gloss → 2D MediaPipe poses → ffmpeg concat → Dreamactor polish (optional)
```

### POC Achievements (Sprints 1-4)
- **Sprint 1:** ASLLVD metadata (9,763 entries, 2,746 glosses), 547 videos downloaded, 2,569 MediaPipe pose extractions (93.6% coverage)
- **Sprint 2:** Hybrid LLM+deterministic translation (76% gloss hit rate), 20 deictic signs, FastAPI service + dashboard at signbridge.wdfab.io
- **Sprint 3:** faster-whisper integration, end-to-end test (3.3s total), GitHub repo pushed, Jev readiness confirmed
- **Sprint 4:** POC declared complete, Dreamactor v2 tested, moving to USABILITY phase

### POC Metrics
- 2,589 ASLLVD glosses in pose library
- 76% gloss hit rate with hybrid LLM+deterministic matching
- 3.3s total pipeline time for test sentence
- 938KB pose video output
- Working FastAPI service + web dashboard

---

## USABILITY Phase: StudioGalt + Blender Pipeline

### CRITICAL DECISION: StudioGalt is our primary dataset (NOT SignAvatars)

**Why StudioGalt:**
- **CC0 license** — public domain, commercially safe, no restrictions
- **Available NOW** — `git clone`, no Google Form, no waiting
- **Real motion capture** — Xsens Link suits + StretchSense finger gloves (not estimated/annotated)
- **Blender-native** — their primary software is Blender, .blend rig files, Python scripts
- **2,587 signs** — comprehensive ASL dictionary
- **FBX format** — universal, works with Blender/Unity/Unreal
- **FACS shapekeys** — facial expressions included

**Why NOT SignAvatars (for now):**
- Non-commercial license (not commercially safe)
- Google Form access gate (waiting period)
- Estimated/annotated motion (not direct mocap)
- SMPL-X format requires additional Blender add-on
- 24fps (vs StudioGalt's 60fps posted / 240fps recorded)
- **Saved as future work:** see `future-work-signavatars.md`

### New Pipeline Architecture

```
Audio → Whisper → LLM/Jev → Gloss Sequence
                                    ↓
                        StudioGalt FBX Lookup
                        (2,587 signs, real mocap, CC0)
                                    ↓
                        Blender Headless CLI
                        ├── Load Galtis rig .blend (base scene)
                        ├── Import FBX per sign, retarget to Galtis armature
                        ├── NLA strip composition (sequential signs)
                        ├── Interpolation between sign clips (10-15 frame blends)
                        ├── Camera + 3-point lighting setup
                        └── Render to MP4 (Cycles CPU; 32-sample dev / 64-sample standard)
                                    ↓
                        [Optional] Dreamactor Polish
                        (Blender render → photorealistic pass)
                                    ↓
                        Final ASL Video (720p+)
```

### Key Changes from POC

| Component | POC (Sprints 1-4) | USABILITY (Sprints 5-10) |
|-----------|--------------------|--------------------------|
| Pose data | 2D MediaPipe (75 keypoints) | 3D mocap FBX (Xsens + StretchSense) |
| Dataset | ASLLVD (2,589 glosses) | StudioGalt (2,587 signs, CC0) |
| Composition | ffmpeg concat (hard cuts) | Blender NLA + interpolation (smooth) |
| Rendering | ffmpeg (2D skeleton) | Blender Cycles CPU (3D character) |
| Facial | None | FACS shapekeys (Galtis rig) |
| Hands | 2D keypoints | StretchSense mocap (3D finger data) |
| Quality | 2D stick figure | 3D animated character |
| License | ASLLVD (research use) | CC0 (commercial safe) |

### StudioGalt Dataset Details

**Repository:** https://github.com/StudioGalt/Sign-Language-Mocap-Archive
- `SG ASL Dictionary/` — 2,587 signs, FBX files (Mesh, No Mesh Full/Mini/Mixamo), .mkv previews
- `SG ASL Fingerspelling/` — Letters and Numbers
- `Rigs/` — Galtis 8 20260401.blend (32MB, includes mesh, armature, FACS shapekeys)
- `Documentation/Scripts/` — Blender Python scripts (Importer, Baker, Exporter, etc.)
- Naming: `SG ASL {SignName} {Alt#} {YYYY-M-D} Upload/`
- Multiple versions per sign (Alt 1, Alt 2) — newer dates = more accurate

---

## Sprint Status

| Sprint | Goal | Status | Notes |
|--------|------|--------|-------|
| 1 | ASLLVD metadata + video download + pose extraction | ✅ DONE | 9,763 entries, 2,569 poses |
| 2 | Translation pipeline + FastAPI service | ✅ DONE | 76% hit rate, dashboard live |
| 3 | Whisper + end-to-end + GitHub | ✅ DONE | 3.3s pipeline, repo pushed |
| 4 | POC complete + Dreamactor test | ✅ DONE | POC declared complete |
| 5 | StudioGalt download + Blender install + headless test + FBX import + sign index | ✅ DONE | 2,586 signs indexed, 145GB, Blender 4.5.14 LTS, Cycles CPU working, 114/116 bones mapped, 3 test renders |
| 6 | Galtis rig scene setup + camera + lighting + first render | ✅ DONE | 720p Hello MP4, three render benchmarks, five-FBX importer test, three-sign batch |
| 7 | Gloss → StudioGalt mapping + pose library | 🔲 NEXT | Build direct/synonym/lemma mapping and fingerspelling fallback |
| 8 | NLA composition + interpolation + multi-sign render | 🔲 PLANNING | |
| 9 | End-to-end pipeline integration + quality eval | 🔲 PLANNING | |
| 10 | Jev constrained decoding + polish | 🔲 PLANNING | |

**Total USABILITY estimate:** 26–38 days (4–7 weeks)

---

## Open Questions

1. **Galtis gender** — Galtis is female. Fabio (target signer) is male. Need male avatar swap?
2. **Gloss → sign name mapping** — StudioGalt uses English words, not glosses. How to bridge?
3. **Missing signs** — Signs not in StudioGalt? Fallback: fingerspell. Later: SignAvatars supplement.
4. **FBX retargeting automation** — Can bone mapping be fully scripted? Per-sign or uniform?
5. **Render scaling** — Cycles CPU is confirmed; Sprint 6 measured 1.884s/still at dev settings and 9.983s/animated frame at standard settings.
6. **Galtis rig complexity** — FK/IK + intermediate + deform + correction bones. Simplify for speed?
7. **Frame rate** — 240fps recorded / 60fps posted. Output at 30fps or 60fps?
8. **Animation retargeting** — Is FBX armature identical across all signs? Or per-sign mapping needed?

---

## Tech Stack

### POC (Working)
- faster-whisper (CPU int8)
- Ollama / Gemma4:cloud
- Python + FastAPI
- ffmpeg
- fal.ai Dreamactor v2
- Cloudflare Tunnel (dashboard)

### USABILITY (Building)
- Blender 3.6+ LTS (headless CLI, macOS Intel)
- StudioGalt Sign Language Mocap Archive (CC0)
- Blender Python API (bpy)
- NLA composition + interpolation
- Cycles CPU (32-sample dev / 64-sample standard / 128-sample quality)
- Same: Whisper, Ollama, FastAPI, Cloudflare Tunnel

### Hardware
- **Watchtower:** Intel i9, AMD 5500M, macOS Sonoma
- **Eevee:** disabled; AMD Metal initialization stalls on this host
- **Cycles:** CPU-only (stable; no NVIDIA/OptiX on macOS)

---

## Key Files

| File | Purpose |
|------|---------|
| `docs/PRD-v2.md` | USABILITY phase PRD (StudioGalt pipeline) |
| `docs/sprint-plan-v2.md` | Sprints 5-10 detailed plan |
| `docs/passoff.md` | This file — full project context |
| `docs/future-work-signavatars.md` | SignAvatars research (saved for later) |
| `docs/PRD-v2.md` → Future Research sections | Video-to-3D pose extraction + BJJ skeleton tracking (Kellen's side quest) |
| `docs/prd.md` | Original POC PRD (Sprints 1-4) |
| `docs/tech-debt.md` | Technical debt tracker |
| `docs/promo-script.md` | Promo/marketing script |

---

## Sprint 5 Results (Completed Oct 2, 2026)

- **StudioGalt cloned:** 145GB, 2,586 signs, 4 FBX variants per sign
- **Sign index built:** 2.4MB JSON, 257 signs with multiple variants, date-sorted (newest = best quality)
- **Blender 4.5.14 LTS** installed via `brew install --cask blender`
- **Cycles CPU rendering** confirmed working (AMD Metal driver crashes bypassed — CPU-only is stable)
- **Bone mapping:** 114/116 FBX bones mapped to Galtis rig (2 minor finger bones unmapped — non-blocking)
- **Test renders:**
  - Minimal cube test (512², 32 samples, 1.5s) — Cycles CPU baseline
  - Galtis rig T-pose (512², 64 samples, 2.5s) — character renders correctly
  - "Anymore" sign FBX animation (512², 64 samples, 2.5s) — motion capture retargeted and rendered
- **Dashboard:** signbridge.wdfab.io updated with Sprint 5 section (needs cleanup — Sprint 4 content stale)
- **Key discovery:** Blender CLI `--background --python` works well. Each sign FBX imports, retargets to Galtis armature via bone mapping, and renders in ~2.5s/frame at 512² on CPU.

### Sprint 5 Stats
- Signs indexed: 2,586
- FBX variants: 4 per sign (Mesh, No Mesh Full, No Mesh Mini, No Mesh Mixamo)
- Galtis rig: 405 bones, 71 FACS shapekeys
- Bone mapping: 114/116 (98.3%)
- Render time: 2.5s/frame at 512², 64 samples, Cycles CPU
- Archive size: 145GB on disk

---

## Sprint 6 Results (Completed Oct 2, 2026)

- Added reusable scene setup with a 50 mm medium camera, three-point area lighting, dark-gray background, and `--greenscreen`.
- Added reusable No Mesh Full importer, bone remapping, Blender action-slot binding, constraint-aware transfer, and 60→30 fps action retiming.
- Validated five different signs: Hello, Biological Mother, Please, Anymore, and Born Again.
- Rendered `output/first_sign_render.mp4`: Hello, H.264, 1280×720, 30 fps, 67 frames/2.233s.
- Standard full-animation render: 668.860s, 9.983s/frame, 672.999s total pipeline time.
- Still benchmarks: 1.884s at 360p/32 samples, 5.322s at 720p/64, and 9.261s at 720p/128.
- Batch rendered Hello, Biological Mother, and Please after one base-scene load: 237 frames in 686.311s.
- Cycles CPU remains the only supported renderer on this Mac; Eevee/AMD Metal is not used.
- Detailed reports: `docs/sprint6-results.md`, `docs/sprint6-render-benchmarks.md`, and `docs/sprint6-batch-test.md`.

---

## Next Action

**Sprint 7:** Build the gloss → StudioGalt mapping and pose-library layer, including alt selection, coverage analysis, and fingerspelling fallback.