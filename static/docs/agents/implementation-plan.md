# Implementation Plan — SignBridge

## Phase 0: Foundation (Sprint 0) — ✅ In Progress

| Task | Status | Notes |
|---|---|---|
| Project folder structure | ✅ | `/Users/watchtower/projects/signbridge/` |
| Constitution, PRD, agent logs | ✅ | `docs/agents/` |
| Fal.ai key located | ✅ | Saved to `~/.openclaw/credentials/fal.json` |
| Dashboard created | ✅ | `signbridge.wdfab.io` |
| Cloudflared route added | ✅ | `signbridge.wdfab.io` → localhost:18104 |

## Phase 1: Dataset + Pose Processing (Sprint 1)

| Task | Est. | Status |
|---|---|---|
| Clone GenASL repo, extract data prep scripts | 1h | Pending |
| Download ASLLVD metadata Excel from BU | 15min | Pending |
| Clean metadata to CSV (gloss → session/scene/frames) | 30min | Pending |
| Download sign video files from BU FTP (parallel) | 1-2h | Pending |
| Set up MMPose/RTMPose on GPU VPS (RunPod/Vast.ai) | 1h | Pending |
| Run batch pose conversion: 3,300 signs → pose videos | 2-4h | Pending |
| Build gloss → pose video lookup table (SQLite/JSON) | 30min | Pending |
| Upload pose video library + lookup table to Watchtower | 30min | Pending |

**Deliverable:** `data/pose_library/` with 3,300+ pose video clips + `data/gloss_lookup.json`

## Phase 2: Translation Pipeline (Sprint 2)

| Task | Est. | Status |
|---|---|---|
| Whisper.cpp integration (audio → transcript) | 1h | Pending |
| LLM summary prompt engineering (transcript → clean script) | 1h | Pending |
| ASL gloss translation prompt engineering (English → gloss) | 2h | Pending |
| Expression annotation in gloss output | 1h | Pending |
| Fingerspelling fallback handler | 30min | Pending |
| Unit tests for translation pipeline | 1h | Pending |

**Deliverable:** `src/translate.py` — audio in, gloss JSON out

## Phase 3: Video Assembly (Sprint 3)

| Task | Est. | Status |
|---|---|---|
| Gloss → pose video segment lookup | 30min | Pending |
| Video concatenation with ffmpeg (smooth transitions) | 1h | Pending |
| Missing gloss handler (fingerspell video or skip + log) | 1h | Pending |
| Timestamp sync (gloss timing → video segments) | 1h | Pending |
| Unit tests for video assembly | 1h | Pending |

**Deliverable:** `src/assemble.py` — gloss JSON in, pose video out

## Phase 4: fal.ai Polish (Sprint 4)

| Task | Est. | Status |
|---|---|---|
| Character sheet selection/generation | 30min | Pending |
| Dreamactor v2 API integration (image + video → output) | 1h | Pending |
| Video chunking for >30 sec inputs | 1h | Pending |
| Chunk stitching (ffmpeg) | 30min | Pending |
| Error handling + retry logic | 30min | Pending |
| Integration tests | 1h | Pending |

**Deliverable:** `src/polish.py` — pose video + character sheet in, final video out

## Phase 5: API + End-to-End (Sprint 5)

| Task | Est. | Status |
|---|---|---|
| FastAPI endpoint: POST /api/jobs (audio upload) | 1h | Pending |
| Async job processing pipeline | 1h | Pending |
| Job status endpoint: GET /api/jobs/{id} | 30min | Pending |
| Webhook callback for completion | 30min | Pending |
| Video serving (static file or presigned URL) | 30min | Pending |
| End-to-end test with real voice note | 1h | Pending |
| Docker container for deployment | 1h | Pending |

**Deliverable:** Working API at `signbridge.wdfab.io` — audio in, video out

## Phase 6: Dashboard Enhancement (Sprint 6 — Future)

| Task | Est. | Status |
|---|---|---|
| Interactive pipeline diagram | 2h | Pending |
| Job history + status visualization | 1h | Pending |
| Side-by-side comparison (pose vs polished) | 1h | Pending |
| Character sheet picker | 1h | Pending |

**Total estimated dev time: ~20-25 hours + 2-4 hours GPU processing**