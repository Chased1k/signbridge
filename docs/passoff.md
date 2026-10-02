# SignBridge — Project Passoff Document

> Created: 2026-10-01 07:10 MST
> Updated: 2026-10-01 17:23 MST
> Purpose: Full context handoff for session continuity

---

## What Is SignBridge

SignBridge takes audio (voice notes, rambles, any spoken content) and produces a video of an ASL signer performing the translation. The pipeline uses open-source tooling for the signing skeleton and video generation for photorealistic polish. On-demand — one audio file in, one video out.

## Project Location

- **Code:** `~/projects/signbridge/`
- **Dashboard:** https://signbridge.wdfab.io (port 18105, Cloudflare tunnel)
- **GitHub:** https://github.com/Chased1k/signbridge — created and pushed
- **PRD v1:** `~/projects/signbridge/docs/prd.md`
- **PRD v2:** `~/projects/signbridge/docs/PRD-v2.md` ← **NEW: USABILITY phase plan**
- **Sprint Plan v2:** `~/projects/signbridge/docs/sprint-plan-v2.md` ← **NEW: Sprints 5-10**
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

## NEW: USABILITY Phase Pipeline

We're upgrading from 2D MediaPipe to 3D SMPL-X/MANO poses using the SignAvatars dataset, with Blender headless CLI for animation composition and rendering.

### New Pipeline Architecture

```
Audio → Whisper → LLM/Jev → Gloss Sequence
                                    ↓
                        SignAvatars Word Subset
                        (3D SMPL-X/MANO .pkl files, ~2,000 words)
                                    ↓
                        Blender Headless CLI
                        ├── Load SMPL-X model (via add-on)
                        ├── Apply pose data per sign (from .pkl)
                        ├── NLA strip composition (sequential signs)
                        ├── Interpolation between sign clips (10-15 frame blends)
                        ├── Temporal smoothing (Savitzky-Golay)
                        ├── Camera + 3-point lighting + scene
                        └── Render to MP4 (Eevee or Cycles)
                                    ↓
                        [Optional] Dreamactor Polish
                        (if Blender render quality insufficient)
                                    ↓
                        Final ASL Video (720p+)
```

### Key Changes from POC
| Component | POC (Sprints 1-4) | USABILITY (Sprints 5-10) |
|-----------|--------------------|--------------------------|
| Pose data | 2D MediaPipe (75 keypoints) | 3D SMPL-X + MANO (182 params/frame) |
| Pose source | ASLLVD (2,589 glosses) | SignAvatars Word/WLASL (~2,000 words) + ASLLVD fallback |
| Video assembly | ffmpeg concat (hard cuts) | Blender NLA composition + interpolation + smoothing |
| Rendering | None (pose videos pre-rendered) | Blender headless CLI (Eevee/Cycles) |
| Hand detail | Poor (2D, limited fingers) | Good (MANO 15-joint 3D per hand) |
| Transitions | None | Interpolated 10-15 frame blends + Savitzky-Golay smoothing |
| Facial expr | None | SMPL-X jaw_pose + expression params available |
| Gloss matching | LLM (Gemma4:cloud) 76% | Jev (typesafe/jev-1.13) via OpenRouter, target 85%+ |
| Output | 640×480 pose video | 1280×720+ 3D rendered video |

### Research Findings

#### Blender CLI (CONFIRMED FEASIBLE)
- `blender --background --python script.py` — fully headless, no GUI
- Full Python API: `bpy.ops`, `bpy.data`, `bpy.context` for all scene operations
- SMPL-X Blender add-on (zjucxh/smplx_blender_addon): adds SMPL-X model, loads .pkl poses, creates animations
- Render: `-f` (single frame), `-a` (animation), `-E CYCLES|BLENDER_EEVEE`, `-- --cycles-device METAL`
- Output: PNG, JPEG, FFMPEG (MP4/H.264), and more
- **OPEN QUESTION:** AMD 5500M Metal GPU support — untested

#### SignAvatars Dataset
- ECCV 2024, Imperial College London / Tencent AI Lab
- 8.34M 3D SMPL-X annotations, 70K motion sequences
- Word subset (WLASL): ~2,000 ASL words, ~57 frames/sign at 24fps
- .pkl format: `smplx: (num_frames, 182)` — root_pose(3) + body_pose(63) + L_hand(45) + R_hand(45) + jaw(3) + betas(10) + expression(10) + cam_trans(3)
- Access: Google Form, non-commercial research license
- **OPEN QUESTION:** Commercial use license needed? Contact shaolihuang@tencent.com

#### SMPL-X Blender Add-on
- Two versions: zjucxh/smplx_blender_addon (free, open) and Meshcapade (discontinued, moved to GitLab)
- Features: add SMPL-X model, load .pkl poses, create animated bodies, Alembic/FBX export
- Works in headless mode (Python API accessible via `bpy.ops`)
- Requires SMPL-X model files (SMPLX_NEUTRAL.pkl etc.) — available from smpl-x.is.tue.mpg.de or Dropbox

#### WLASL vs ASLLVD
- WLASL: ~2,000 words (word-level ASL recognition dataset)
- ASLLVD: 2,746 glosses (ASL lexicon video dataset)
- Both are ASL, high expected overlap, but exact overlap unknown until data is downloaded
- WLASL has C-UDA license (computational use, no commercial)
- **OPEN QUESTION:** Coverage overlap analysis needed in Sprint 5

---

## Sprint Status

### Completed Sprints

| Sprint | Status | Summary |
|--------|--------|---------|
| Sprint 1 | ✅ COMPLETE | ASLLVD metadata + video download + MediaPipe pose extraction (2,569/2,746) |
| Sprint 2 | ✅ COMPLETE | Hybrid translation pipeline, 76% gloss hit rate, FastAPI + dashboard |
| Sprint 3 | ✅ COMPLETE | faster-whisper, end-to-end test (3.3s), GitHub push, Jev readiness |
| Sprint 4 | ✅ COMPLETE | POC declared complete, Dreamactor tested, moving to USABILITY |

### Upcoming Sprints (Plan v2)

| Sprint | Goal | Est. Time | Status |
|--------|------|-----------|--------|
| Sprint 5 | SignAvatars access + Blender install + headless test | 3-5 days | NEXT |
| Sprint 6 | SMPL-X → Blender rig pipeline + scene setup | 5-7 days | PLANNED |
| Sprint 7 | Gloss → SignAvatars mapping + pose library rebuild | 3-5 days | PLANNED |
| Sprint 8 | Blender NLA composition + interpolation + render | 7-10 days | PLANNED |
| Sprint 9 | E2E integration + quality evaluation | 5-7 days | PLANNED |
| Sprint 10 | Jev integration for constrained gloss decoding | 5-7 days | PLANNED |

**Total estimated: 28-41 days (4-6 weeks)**

See `~/projects/signbridge/docs/sprint-plan-v2.md` for detailed sprint plans.

---

## Next Steps (Immediate)

1. **Sprint 5 kickoff:**
   - Fill out SignAvatars Google Form for dataset access
   - Download Blender + SMPL-X Blender add-on
   - Test Blender headless mode on Watchtower
   - Parse SignAvatars Word subset data
   - Run coverage analysis: ASLLVD glosses vs WLASL words

2. **Kellen decisions needed (OPEN QUESTIONS):**
   - SignAvatars non-commercial license acceptable? Or need commercial license?
   - Blender version: 3.1 (tested with SMPL-X add-on) or latest LTS?
   - Eevee (fast) vs Cycles (quality) renderer for MVP?
   - Dreamactor: keep as optional polish or drop entirely?
   - Pre-render sign clips to cache or render full sequence each time?
   - Jev timing: Sprint 10 as planned, or pull earlier?

---

## Key Architecture Decisions (All Sprints)

1. **Hybrid translation (not pure LLM)** — LLM rephrases to ASL grammar, deterministic code matches against pose library. LLM can't hallucinate glosses it doesn't have. *(Sprint 2)*
2. **Deictic signs as synthetic videos** — ASLLVD doesn't include pronouns (pointing gestures). 20 synthetic placeholder videos generated. *(Sprint 2)*
3. **MediaPipe over RTMPose** — MediaPipe runs on CPU (Watchtower has no GPU). 75 keypoints vs 133. *(Sprint 1)*
4. **ffmpeg concat for video assembly** — Simple, fast (<1s for 13 segments). No transitions or smoothing yet. *(Sprint 2, replaced in Sprint 8)*
5. **fal.ai Dreamactor for polish** — Video-to-video model for photorealistic output. *(Sprint 4, optional in v2)*
6. **SignAvatars Word subset as primary 3D pose library** — Replaces ASLLVD/MediaPipe 2D poses. ~2,000 words with SMPL-X 3D annotations. *(Sprint 5-7)*
7. **Blender headless CLI for animation + rendering** — `blender --background --python` for NLA composition, interpolation, and render. *(Sprint 6-8)*
8. **Fallback chain: SignAvatars → ASLLVD → Deictic → Fingerspell** — Tiered pose source resolution. *(Sprint 7)*
9. **Jev for constrained gloss matching** — Replace LLM rephrasing with TypeSafe AI's Jev model via OpenRouter. No hallucinations. *(Sprint 10)*

---

## Infrastructure

- **API server:** Python 3.14, FastAPI + uvicorn, port 18105
- **Start script:** `~/projects/signbridge/scripts/start_api.sh`
- **Cloudflare tunnel:** signbridge.wdfab.io → localhost:18105 (in `~/.cloudflared/config.yml`)
- **Cloudflared:** ONE instance running (pid 36335 as of Oct 1). DO NOT KILL — serves ALL wdfab.io subdomains.
- **Watchtower hardware:** Intel i9-9980HK, 32GB RAM, AMD 5500M 8GB VRAM. No PyTorch. ffmpeg 8.1.2.
- **Ollama:** Running locally, gemma4:cloud model for ASL rephrasing
- **Blender:** NOT YET INSTALLED — Sprint 5 task

## Key Files

```
~/projects/signbridge/
├── src/
│   ├── pipeline.py          # Main pipeline: audio → transcript → gloss → pose video → polish
│   ├── api.py               # FastAPI service (port 18105)
│   └── gloss_remaps.py      # English → ASLLVD gloss remapping + SKIP_WORDS + ALWAYS_FINGERSPELL
├── scripts/
│   ├── 01_download_metadata.py
│   ├── 02_clean_metadata.py
│   ├── 03_download_videos.py
│   ├── 03b_download_top500.py
│   ├── 03c_download_slim.py
│   ├── mediapipe_pose_extraction.py
│   ├── batch_pose_extraction.py
│   ├── setup_mmpose.sh
│   ├── generate_deictic_signs.py
│   ├── start_api.sh
│   └── test_pipeline_v2.py
├── data/
│   ├── raw/
│   │   └── asllvd_metadata.xlsx
│   ├── processed/
│   │   └── asllvd_clean.csv
│   ├── pose_library/
│   │   ├── pose_lookup.json       # 2,589 glosses → pose video paths
│   │   ├── *.mp4                  # 2,569 pose videos
│   │   └── deictic_*.mp4          # 20 synthetic deictic sign videos
│   └── output/
├── dashboard/
│   └── static/
│       ├── index.html
│       └── test_sprint2.mp4
├── docs/
│   ├── prd.md                     # PRD v1 (POC)
│   ├── PRD-v2.md                  # PRD v2 (USABILITY) ← NEW
│   ├── sprint-plan-v2.md          # Sprint plan v2 (Sprints 5-10) ← NEW
│   ├── passoff.md                 # THIS FILE
│   ├── tech-debt.md
│   └── promo-script.md
├── agents/
└── requirements.txt
```

---

## ASLLVD Dataset Notes

- **Source:** Boston University ASL Lexicon Video Dataset
- **Size:** 3,300+ ASL signs, 6 signers (Brady, Dana, Lana, Liz, Naomi, Tyler)
- **Format:** Citation form (isolated signs, not sentences)
- **Missing:** Pronouns (deictic), connector words (IS/ARE/BE/TO/OF), some common words
- **Our fix:** 20 synthetic deictic signs + SKIP_WORDS + ALWAYS_FINGERSPELL

## SignAvatars Dataset Notes (NEW)

- **Source:** ECCV 2024, Imperial College London / Tencent AI Lab
- **Size:** 8.34M SMPL-X annotations, 70K sequences, 4 subsets
- **Word subset (WLASL):** ~2,000 words, ~57 frames/sign at 24fps
- **Format:** .pkl files, `smplx: (num_frames, 182)` parameters
- **Hands:** MANO 15-joint 3D per hand (45-dim each)
- **Access:** Google Form, non-commercial research license
- **Model files:** SMPL-X models from smpl-x.is.tue.mpg.de (free academic) or Dropbox

---

## Jev / System One Context

- **Jev:** TypeSafe AI's hosted System One model. 70-500ms, can't hallucinate, outputs typed decisions with probabilities.
- **Access:** OpenRouter Decisions API, `POST /api/alpha/decisions`, model `typesafe/jev-1.13`
- **For SignBridge:** Use `choice` questions with our gloss vocabulary as criteria. No more "TELL-YOU" hallucinations.
- **Status:** OpenRouter key works, Jev responds. Ready for integration in Sprint 10.
- **Kev (local):** BLOCKED on Watchtower — PyTorch >= 2.6 has no Intel macOS wheels. Using Jev via OpenRouter instead.

---

## Environment State (as of 2026-10-01 17:23 MST)

- Signbridge API may need restart (check port 18105)
- Cloudflared running (pid 36335) — DO NOT KILL
- All wdfab.io subdomains working
- Python 3.13, Rust, Modal installed during failed Kev attempt (not needed, can clean up)
- Kev repo at `~/projects/kev/` (can keep for reference or remove)
- **NO OpenRouter key verified yet** — needed for Sprint 10
- **Blender NOT YET installed** — Sprint 5 task
- **SignAvatars NOT YET downloaded** — Sprint 5 task (Google Form pending)

---

## Dashboard Update Rule

**Kellen's directive:** Update the dashboard after each sprint. Include test outputs, videos, stats, progress.