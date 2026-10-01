# SignBridge — Project Passoff Document

> Created: 2026-10-01 07:10 MST
> Purpose: Full context handoff for session continuity

---

## What Is SignBridge

SignBridge takes audio (voice notes, rambles, any spoken content) and produces a video of an ASL signer performing the translation. The pipeline uses open-source tooling for the signing skeleton (GenASL/RTMPose + ASLLVD dataset) and fal.ai video generation for photorealistic polish. On-demand — one audio file in, one video out.

## Project Location

- **Code:** `~/projects/signbridge/`
- **Dashboard:** https://signbridge.wdfab.io (port 18105, Cloudflare tunnel)
- **GitHub:** Chased1k/signbridge — **NOT created yet**, code is local only
- **PRD:** `~/projects/signbridge/docs/prd.md`
- **Tech Debt:** `~/projects/signbridge/docs/tech-debt.md`
- **Promo Script:** `~/projects/signbridge/docs/promo-script.md`
- **Workspace project doc:** `~/projects/Speech-to-Sign-Language-Video.md`

## Sprint Status

### Sprint 1 (Sep 30) — COMPLETE
- ASLLVD metadata downloaded (9,763 entries, 2,746 unique glosses, 6 signers)
- 547 source videos downloaded from BU
- MediaPipe pose extraction: 2,569/2,746 glosses (93.6% coverage)
- PRD written with 5 core features + feature 4b (gloss coverage resolver)
- Dev-workflows templates adapted from `projects/dev-workflows/`
- Colab notebook for GPU pose extraction (DO GPU blocked via API)

### Sprint 2 (Oct 1) — COMPLETE
- **Hybrid translation pipeline**: LLM (Gemma4:cloud via Ollama) rephrases English → ASL grammar, then deterministic word-to-gloss matching
- **Coverage**: 2/18 direct hits (11%) → 13/17 (76%) with hybrid approach
- **20 deictic signs**: Synthetic placeholder videos for pronouns (YOU, HE, SHE, WE, MY, etc.) that ASLLVD doesn't include
- **FastAPI service**: POST /api/jobs, GET /api/jobs/{id}, GET /api/jobs/{id}/video, GET /api/health, GET /api/stats
- **Dashboard**: signbridge.wdfab.io — pipeline diagram, stats, job submission form, Sprint 2 demo with embedded test video, tech debt panel
- **gloss_remaps.py**: Updated to use deictic signs directly, old broken remaps removed, zero-morpheme words (IS/ARE/BE/TO) in SKIP_WORDS

### Sprint 3 (NEXT) — NOT STARTED
**Priorities:**
1. **Kev integration** — Replace LLM rephrasing with Kev-4B (System One model) for constrained gloss matching. Install Kev locally, point at our 2,589 gloss vocabulary. No more "TELL-YOU" hallucinations.
2. **fal.ai polish** — Run skeleton pose video through fal.ai Dreamactor (or similar video-to-video model) with a character sheet image to get photorealistic signer video
3. **Real audio input** — Wire up Whisper transcription (faster-whisper, CPU) for actual voice note input
4. **Constrained decoding exploration** — Kev vs Outlines vs fine-tuned model

## Key Architecture Decisions

1. **Hybrid translation (not pure LLM)**: LLM rephrases to ASL grammar, deterministic code matches against pose library. LLM can't hallucinate glosses it doesn't have.
2. **Deictic signs as synthetic videos**: ASLLVD doesn't include pronouns because they're pointing gestures, not lexical signs. We generate color-placeholder videos. Need proper pose extraction from sample videos later (TD-004).
3. **MediaPipe over RTMPose**: MediaPipe runs on CPU (Watchtower has no GPU). 75 keypoints vs 133. Trade-off: speed over accuracy. Re-evaluate with GPU (TD-002).
4. **ffmpeg concat for video assembly**: Simple, fast (<1s for 13 segments). No transitions or smoothing yet.
5. **fal.ai for polish (not yet implemented)**: Dreamactor v2 or similar video-to-video model. Takes skeleton video + character image → photorealistic output. Chunk videos >30 sec.

## Infrastructure

- **API server**: Python 3.14, FastAPI + uvicorn, port 18105
- **Start script**: `~/projects/signbridge/scripts/start_api.sh`
- **Cloudflare tunnel**: signbridge.wdfab.io → localhost:18105 (in `~/.cloudflared/config.yml`)
- **Cloudflared**: ONE instance running (pid 36335 as of Oct 1 07:10). DO NOT kill cloudflared — it serves ALL wdfab.io subdomains (revenue, health, stt, files, mlb-sep30, bea, buzz-wd, signbridge)
- **Watchtower hardware**: Intel i9-9980HK, 32GB RAM, AMD 5500M 8GB VRAM. No PyTorch. ffmpeg 8.1.2 (no drawtext filter). No GPU acceleration.
- **Ollama**: Running locally, gemma4:cloud model used for ASL rephrasing
- **Python deps installed**: fastapi, uvicorn, python-multipart, pandas, openpyxl, faster-whisper (needs verification)

## Key Files

```
~/projects/signbridge/
├── src/
│   ├── pipeline.py          # Main pipeline: audio → transcript → gloss → pose video → fal.ai
│   ├── api.py               # FastAPI service (port 18105)
│   └── gloss_remaps.py      # English → ASLLVD gloss remapping table + SKIP_WORDS + ALWAYS_FINGERSPELL
├── scripts/
│   ├── 01_download_metadata.py    # ASLLVD metadata download
│   ├── 02_clean_metadata.py       # Clean to CSV
│   ├── 03_download_videos.py      # Download source videos from BU
│   ├── 03b_download_top500.py     # Top 500 glosses
│   ├── 03c_download_slim.py       # Slim download
│   ├── mediapipe_pose_extraction.py  # MediaPipe pose extraction (CPU)
│   ├── batch_pose_extraction.py    # MMPose batch (GPU, not used)
│   ├── setup_mmpose.sh            # MMPose setup script
│   ├── generate_deictic_signs.py  # Generate synthetic pronoun videos
│   ├── start_api.sh               # Start FastAPI server
│   └── test_pipeline_v2.py        # Pipeline test script
├── data/
│   ├── raw/
│   │   └── asllvd_metadata.xlsx   # Original ASLLVD metadata (1.5MB)
│   ├── processed/
│   │   └── asllvd_clean.csv       # Cleaned metadata (9,763 entries)
│   ├── pose_library/
│   │   ├── pose_lookup.json       # 2,589 glosses → pose video paths
│   │   ├── *.mp4                  # 2,569 pose videos
│   │   └── deictic_*.mp4          # 20 synthetic deictic sign videos
│   └── output/
│       ├── test_llm_v2_pose.mp4   # Sprint 2 test output video
│       └── *_results.json         # Job results
├── dashboard/
│   └── static/
│       ├── index.html             # Dashboard HTML
│       └── test_sprint2.mp4       # Embedded test video
├── docs/
│   ├── prd.md                     # Product Requirements Document
│   ├── tech-debt.md               # Tech debt + future work
│   └── promo-script.md            # Promotional script
├── agents/                        # Dev-workflow agent definitions
└── requirements.txt
```

## ASLLVD Dataset Notes

- **Source**: Boston University ASL Lexicon Video Dataset
- **Size**: 3,300+ ASL signs, 6 signers (Brady, Dana, Lana, Liz, Naomi, Tyler)
- **Format**: Citation form (isolated signs, not sentences)
- **Missing**: Pronouns (deictic/indexical — pointing gestures), connector words (IS/ARE/BE/TO/OF), some common words (TELL, VIDEO, GOOD, LOVE, NEED)
- **Why missing**: These are gestural or zero-morpheme in ASL, not lexical signs you'd record in a dictionary
- **Our fix**: 20 synthetic deictic signs (color-placeholder videos) + SKIP_WORDS for zero-morphemes + ALWAYS_FINGERSPELL for proper nouns

## Kev / System One Models Context

Kellen asked about JEV/KEV/Laya for constrained gloss matching. Research done:

- **Jev**: TypeSafe AI's hosted System One model. 70-500ms, can't hallucinate, outputs typed decisions with probabilities. Available via OpenRouter Decisions API (`POST /api/alpha/decisions`). Model ID: `typesafe/jev-1.13`.
- **Kev**: Open-source Jev clone by Jared Palmer. Built on Qwen3.5/3.8. 4 sizes: 0.8B, 4B, 9B, 27B. Drop-in for Jev API. Fine-tunable.
- **Laya**: Open-weight, ModernBERT-based, lighter, less accurate than Kev.

### Installation Attempt (2026-10-01)

**BLOCKED on Watchtower** — PyTorch >= 2.6 has NO Intel macOS wheels. Last torch with Intel Mac support is 2.2.x (cp312 only). Kev requires `torch>=2.6,<2.9`.

**What was installed:**
- Python 3.13.13 via `uv python install 3.13`
- Kev repo cloned to `~/projects/kev/`
- Rust 1.99.0 installed (needed for cbor2 build)
- Modal 1.6.0 installed in `/tmp/modal-env/` (for cloud deployment)
- `uv sync --extra serve` FAILED: torch has no wheels for `macosx_x86_64`

**Decision: Use Jev via OpenRouter**

Kev-4B can't run locally on Watchtower. Jev (TypeSafe's hosted model) is the same architecture, available via OpenRouter Decisions API, cheap, and needs no local install. This is the path forward.

**What's needed:**
- OpenRouter API key (Kellen — sign up at openrouter.ai if not already, add key to `~/.openclaw/credentials/`)
- Model: `typesafe/jev-1.13` (or `~typesafe/jev-latest`)
- Endpoint: `POST https://openrouter.ai/api/alpha/decisions` (Decisions API) or `POST https://openrouter.ai/api/v1/systemone` (System One API)
- Pricing: per input token, output tokens are free. Check openrouter.ai/typesafe/jev-1.13 for current pricing.
- API format: Send `state` (the text to translate) + `questions` (typed: choice, noul, score). Get back calibrated probabilities.

**For SignBridge specifically:**
- Use Jev `choice` questions: "Which ASL gloss matches this English word?" with our 2,589 glosses as criteria
- Or use Jev to validate/rephrase: "Is this ASL gloss translation accurate?" as a `noul` question
- Batch multiple words per call (shared state, multiple questions)

**Local Kev install was attempted but failed:**
- Python 3.13.13 installed via uv
- Kev repo cloned to `~/projects/kev/`
- Rust 1.99.0 installed (needed for cbor2)
- Modal 1.6.0 installed in `/tmp/modal-env/` (not authenticated, not needed anymore)
- `uv sync --extra serve` FAILED: torch has no wheels for `macosx_x86_64` (Intel Mac dropped after 2.2.x, Kev needs >=2.6)
- All of this can be cleaned up if desired — the Modal/Rust/Python 3.13 stuff isn't needed for the Jev path

## Dashboard Update Rule

**Kellen's directive**: Update the dashboard after each sprint. Include test outputs, videos, stats, progress.

## Git Status

- **Local repo**: ~/projects/signbridge/ — initialized, multiple commits, master branch
- **Remote**: github.com/Chased1k/signbridge.git — **DOES NOT EXIST YET**. Need to create on GitHub and push.
- **Workspace repo**: ~/projects/Speech-to-Sign-Language-Video.md committed to main workspace repo

## What To Do Next (Sprint 3)

1. **Get OpenRouter API key** — Kellen check if you already have one (openrouter.ai/settings/keys). Add to `~/.openclaw/credentials/openrouter.json`
2. **Wire Jev into pipeline.py** — Replace `llm_rephrase_and_map()` to call OpenRouter Decisions API with `typesafe/jev-1.13`. Use `choice` questions with our gloss vocabulary as criteria.
3. **Create GitHub repo** and push signbridge code
4. **Test gloss matching accuracy** with Jev vs current 76%
5. **Wire up Whisper** for real audio input (faster-whisper, CPU)
6. **Implement fal.ai polish** step (Dreamactor or similar video-to-video)
7. **Update dashboard** with Sprint 3 results
8. **Commit and push**

## Environment State (as of 2026-10-01 08:04 MST)

- Signbridge API running on port 18105 (may need restart after session change)
- Cloudflared running (pid 36335) — DO NOT KILL
- All wdfab.io subdomains working (revenue, health, stt, files, mlb-sep30, bea, buzz-wd, signbridge)
- Python 3.13, Rust, Modal installed during failed Kev attempt (not needed for Jev path, can clean up)
- Kev repo at `~/projects/kev/` (can keep for reference or remove)
- **NO OpenRouter key yet** — this is the blocker for Sprint 3