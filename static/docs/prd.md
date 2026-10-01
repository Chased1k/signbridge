# SignBridge — Product Requirements Document

> Voice note → ASL signer video. On-demand, photorealistic, expressive.

## Overview

SignBridge takes an audio file (voice note, ramble, any spoken content) and produces a video of an ASL signer performing the translation. The pipeline uses open-source tooling for the signing skeleton (GenASL/RTMPose + ASLLVD dataset) and fal.ai video generation for photorealistic polish. The system processes on-demand — one audio file in, one video out. No batch processing.

## Primary User

Kellen (initially). Content creator who rambles voice notes and wants them translated to ASL video for accessibility and content repurposing. Eventually: any content creator, educator, or accessibility-focused organization.

## Core Features (MVP)

### Feature 1: Audio Ingest

- **User story:** As a user, I want to submit an audio file and receive a sign language video back
- **Acceptance criteria:**
  - [ ] POST endpoint accepts audio file (mp3, wav, m4a, ogg)
  - [ ] Returns job ID immediately (async processing)
  - [ ] Webhook or polling for completion
  - [ ] Max file size: 50MB (~30 min audio)
- **Inputs:** Audio file
- **Outputs:** Job ID, status endpoint

### Feature 2: Transcription + Summarization

- **User story:** As the system, I need clean text from audio to translate
- **Acceptance criteria:**
  - [ ] Whisper transcription with timestamps
  - [ ] LLM cleans transcript → concise summary script
  - [ ] Summary preserves meaning, removes filler
  - [ ] Output: clean English text + word timestamps
- **Inputs:** Audio file
- **Outputs:** Transcript JSON, summary text

### Feature 3: ASL Gloss Translation

- **User story:** As the system, I need ASL gloss to look up signs
- **Acceptance criteria:**
  - [ ] English → ASL gloss with grammar adjustments
  - [ ] Facial expression annotations per sign segment
  - [ ] Fingerspelling fallback for vocabulary gaps
  - [ ] Output: gloss sequence with timing
- **Inputs:** Summary text
- **Outputs:** Gloss JSON array `[{gloss, start_time, end_time, expression}]`

### Feature 4: Pose Video Assembly

- **User story:** As the system, I need a skeleton signing video from gloss
- **Acceptance criteria:**
  - [ ] Look up each gloss in ASLLVD pose video database
  - [ ] **Gloss coverage loop:** If a gloss isn't in the database, the LLM rephrases using available vocabulary (e.g., "procrastinate" → "PUT-OFF" or "DELAY UNTIL LATER")
  - [ ] Track rephrasing attempts (max 3 retries per missing gloss)
  - [ ] Fingerspelling as last-resort fallback for names/proper nouns/words that can't be rephrased
  - [ ] Log coverage gaps for future dataset expansion
  - [ ] Concatenate segments with smooth transitions
  - [ ] Output: pose avatar video (mp4)
- **Inputs:** Gloss JSON array, pose lookup database
- **Outputs:** Pose video file, coverage report

### Feature 4b: Gloss Coverage Resolver

- **User story:** As the system, I need to maximize signing coverage by rephrasing within available vocabulary
- **Acceptance criteria:**
  - [ ] Input: missing gloss + sentence context
  - [ ] LLM prompt: "Rephrase '{missing_gloss}' using these available signs: {available_glosses_sample}. Keep ASL grammar."
  - [ ] Output: alternative gloss sequence that exists in database
  - [ ] Coverage stats logged: hit rate, rephrase rate, fingerspell rate
  - [ ] Builds a "gap dictionary" over time — cached rephrasings for common missing words

### Feature 5: Photorealistic Polish (fal.ai)

- **User story:** As a user, I want the signer to look like a real person, not a stick figure
- **Acceptance criteria:**
  - [ ] Pose video + character sheet → fal.ai Dreamactor v2
  - [ ] Chunk videos >30 sec (Dreamactor limit)
  - [ ] Stitch chunked outputs
  - [ ] Output: photorealistic signer video (mp4)
- **Inputs:** Pose video, character sheet image URL
- **Outputs:** Final video file

### Feature 6: Delivery

- **User story:** As a user, I want to receive my video
- **Acceptance criteria:**
  - [ ] Video available at URL (served via wdfab.io or S3)
  - [ ] Status callback / webhook notification
  - [ ] Video retained for 24 hours then cleaned up
- **Inputs:** Final video file
- **Outputs:** Video URL

## Non-Goals (MVP)

- Real-time/streaming translation (future work)
- Multi-language sign languages (ASL only for POC)
- Custom signer training/fine-tuning
- Mobile app
- User authentication (single-user POC)
- Batch processing

## Data Model

### Job

| Field | Type | Required | Notes |
|---|---|---|---|
| id | uuid | yes | Primary key |
| status | enum | yes | pending, transcribing, translating, posing, polishing, done, error |
| audio_path | string | yes | Input audio file path |
| transcript | text | no | Whisper output |
| summary | text | no | LLM cleaned summary |
| gloss_json | json | no | ASL gloss sequence |
| pose_video_path | string | no | Intermediate pose video |
| final_video_path | string | no | Final polished video |
| character_sheet_url | string | no | Character image for polish phase |
| error | text | no | Error message if failed |
| created_at | datetime | yes | Job creation time |
| completed_at | datetime | no | Job completion time |

## Technical Constraints

- **Stack:** Python 3.10+, FastAPI, Whisper.cpp, OpenMMLab (MMPose), fal.ai API
- **Platform:** macOS (Watchtower) for dev, Docker for deployment
- **GPU:** Required for MMPose pose processing — rent VPS or use Colab for dataset prep, pre-computed lookup table for on-demand
- **fal.ai:** Dreamactor v2 for motion transfer, key in `~/.openclaw/credentials/fal.json`
- **ComfyUI:** Node-based image generation available via OpenClaw comfy extension (character sheet generation)
- **Performance:** On-demand, <5 min for 30 sec audio (pose lookup + fal.ai generation)
- **Security:** fal.ai key in env, no hardcoded secrets

## Design Direction

- **Dashboard:** Dark mode, technical aesthetic, pipeline diagram
- **URL:** signbridge.wdfab.io
- **Visual elements:** Animated pipeline flow, status indicators, architecture diagram
- **Key screens:**
  1. Project overview dashboard — pipeline diagram, status, architecture
  2. Job submission — drag audio, see progress
  3. Results — video player with comparison (pose vs polished)

## Open Questions

1. **Character sheet:** Use ComfyUI to generate, or stock photo, or upload your own?
2. **GPU strategy:** Pre-compute all 3,300 pose videos once (lookup table), or compute on-demand?
3. **Deployment:** Docker on Watchtower, or separate VPS?
4. **Chunking:** How to handle >30 sec videos with Dreamactor — stitch at pose level or output level?