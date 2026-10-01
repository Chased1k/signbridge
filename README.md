# SignBridge

Speech → Sign Language Video Pipeline. Takes audio in, produces photorealistic ASL signer video.

**Dashboard:** <https://signbridge.wdfab.io>
**Project doc:** <https://github.com/Chased1k/chiron-brain/blob/main/projects/Speech-to-Sign-Language-Video.md>

## Quickstart

```bash
# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn src.api:app --reload --port 18104

# Or use the dashboard
cd static && python3 -m http.server 18104
```

## Pipeline

1. **Ingest** — Audio file via API
2. **Transcribe** — Whisper.cpp → English text
3. **Summarize** — LLM → clean script
4. **Translate** — LLM → ASL gloss with expressions
5. **Pose Lookup + Coverage Loop** — Gloss → pose videos (rephrase if missing)
6. **Stitch** — ffmpeg concat → pose avatar video
7. **Polish** — fal.ai Dreamactor v2 → photorealistic signer
8. **Deliver** — Video URL returned

## Structure

```
signbridge/
├── src/           # Python source (pipeline stages)
├── docs/          # PRD, constitution, agent logs
├── scripts/       # Utility scripts (dataset download, pose processing)
├── data/          # Datasets, pose library, job outputs (gitignored)
├── tests/         # pytest test suite
└── static/        # Dashboard HTML
```

## Dev Workflow

This project uses the dev-workflows sprint system:
- `docs/agents/constitution.md` — Rules for all agents
- `docs/prd.md` — Product requirements
- `docs/agents/implementation-plan.md` — Sprint breakdown
- `docs/agents/build-log.md` — What was done
- `docs/agents/decision-log.md` — Why decisions were made
- `docs/agents/assumptions.md` — What we're assuming
- `docs/agents/open-questions.md` — What's unresolved

**Working directory for Codex/OpenCode:** `/Users/watchtower/projects/signbridge/`