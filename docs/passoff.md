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

**Options for Sprint 3:**
1. **Modal deploy** (RECOMMENDED): `modal setup` (needs browser auth from Kellen) → `modal deploy kev_serve.py` → get HTTPS endpoint. L40S GPU, scales to zero. Free tier has T4.
   - Deploy script: `~/projects/kev/skills/kev-deploy/scripts/kev_serve.py`
   - Command: `source /tmp/modal-env/bin/activate && modal setup && KEV_MODEL=jaredpalmer/kev-4b modal deploy ~/projects/kev/skills/kev-deploy/scripts/kev_serve.py`
   - Result: `https://<workspace>--kev-api.modal.run` endpoint
2. **OpenRouter Jev**: Sign up at openrouter.ai, get API key, use `typesafe/jev-1.13` via Decisions API. No local install needed. Costs per input token.
3. **HuggingFace Space**: `https://jaredpalmer-kev.hf.space` has a Gradio API (`/gradio_api/call/decide`), but it returned errors during testing (model may have been loading). Could retry.
4. **Patch torch requirement**: Force torch 2.2.x on cp312, patch Kev's pyproject.toml. Risky — may break model loading.
5. **Use existing Ollama models**: Keep current Gemma4:cloud approach but improve the prompt with few-shot examples and stricter output format. Less accurate than Kev but no install needed.

**Kellen needs to**: Run `modal setup` in a browser to authenticate Modal, then I can deploy Kev-4B to Modal.

## Dashboard Update Rule

**Kellen's directive**: Update the dashboard after each sprint. Include test outputs, videos, stats, progress.

## Git Status

- **Local repo**: ~/projects/signbridge/ — initialized, multiple commits, master branch
- **Remote**: github.com/Chased1k/signbridge.git — **DOES NOT EXIST YET**. Need to create on GitHub and push.
- **Workspace repo**: ~/projects/Speech-to-Sign-Language-Video.md committed to main workspace repo

## What To Do Next (Sprint 3)

1. **Kellen: authenticate Modal** — `source /tmp/modal-env/bin/activate && modal setup` (opens browser, creates `~/.modal.toml`)
2. **Deploy Kev-4B to Modal** — `KEV_MODEL=jaredpalmer/kev-4b modal deploy ~/projects/kev/skills/kev-deploy/scripts/kev_serve.py` → get endpoint URL
3. **Create GitHub repo** and push signbridge code
4. **Rewrite `llm_rephrase_and_map()`** in pipeline.py to call Kev endpoint (System One API: `POST /v1/systemone` with state + questions)
5. **Test gloss matching accuracy** with Kev vs current 76%
6. **Wire up Whisper** for real audio input (faster-whisper, CPU)
7. **Implement fal.ai polish** step (Dreamactor or similar video-to-video)
8. **Update dashboard** with Sprint 3 results
9. **Commit and push**

## Environment State (as of 2026-10-01 08:00 MST)

- Python 3.13.13 installed via uv
- Rust 1.99.0 installed at `~/.cargo/`
- Modal 1.6.0 installed in `/tmp/modal-env/` (NOT authenticated)
- Kev repo at `~/projects/kev/` (uv sync FAILED — no torch for Intel Mac)
- Signbridge API running on port 18105 (may need restart after session change)
- Cloudflared running (pid 36335) — DO NOT KILL
- All wdfab.io subdomains working (revenue, health, stt, files, mlb-sep30, bea, buzz-wd, signbridge)