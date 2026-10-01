# Constitution — SignBridge

> Code of conduct for all agents working on this project. Non-negotiable.

## Core Architecture Rule

The pipeline is a series of discrete stages, each with clear inputs and outputs. Each stage is independently testable and replaceable. The LLM orchestrates stages but never IS a stage.

## Pipeline Stages

1. **Ingest:** Audio file received (API endpoint or file drop)
2. **Transcribe:** Whisper → English transcript
3. **Summarize:** LLM → cleaned summary (concise spoken script)
4. **Translate:** LLM → ASL gloss with expression annotations
5. **Pose Lookup + Coverage Loop:** Gloss → pose video segments from ASLLVD dataset. **If gloss not found:** LLM rephrases using available vocabulary (max 3 retries). Last resort: fingerspell.
6. **Stitch:** Concatenate pose segments → continuous pose avatar video
7. **Polish:** Pose video + character sheet → fal.ai Dreamactor v2 → photorealistic signer
8. **Deliver:** Output video URL returned to caller

Each stage has its own module, tests, and CLI entry point. Stages communicate via file paths (not in-memory state).

### Coverage Loop Detail

The gloss→pose lookup is a **loop**, not a one-shot:
1. Split gloss sentence into individual glosses
2. Look up each gloss in ASLLVD pose database
3. If any gloss is missing:
   - Send missing gloss + sentence context to LLM
   - LLM rephrases using available vocabulary (e.g., "procrastinate" → "DELAY PUT-OFF")
   - Re-run lookup on rephrased glosses
   - Max 3 retries per missing gloss
4. If still missing after retries → fingerspell the word
5. Log all coverage gaps to build a gap dictionary for future dataset expansion

This is critical because 3,300 signs won't cover everything. The system gets smarter over time as we:
- Cache successful rephrasings (gap dictionary)
- Expand the pose database with more datasets (WLASL, Phoenix-2014T, How2Sign)
- Contribute back to ASLLVD with new annotations

## Development Process

1. **Work sprint-by-sprint.** Do not skip ahead. Each sprint builds on the last.
2. **TDD is non-negotiable.** Write failing tests, verify red, implement, verify green.
3. **Do not silently make architectural decisions.** Log in assumptions.md or open-questions.md.
4. **One commit per sprint.** Meaningful messages. No amend without review.
5. **Never introduce new dependencies without explicit approval.**
6. **Follow existing patterns.** Read neighboring files before writing new code.

## Agent Responsibilities

### Reviewer (CTO)
- Reads all context before every sprint
- Breaks work into tasks with explicit scope and acceptance criteria
- Reviews all code with structured verdicts
- Commits approved work
- Maintains decision log, assumptions log, open questions
- Flags when human review needed

### Implementer (Builder)
- Writes tests first, code second
- Runs full test suite — no regressions
- Runs lint and typecheck — must be clean
- Updates build log with structured entries
- Reports completion in structured format
- Never commits — Reviewer handles commits

## Safety Principles

- ASL translation accuracy is critical — wrong signs can cause harmful miscommunication
- Always include disclaimer: "AI-generated translation. Verify with certified interpreter for critical content."
- Never claim to replace human interpreters
- Facial expression grammar is part of the language — not optional decoration

## Code Conventions

- **Language:** Python 3.10+ (pipeline), JavaScript/HTML (dashboard)
- **Strict typing:** Use type hints everywhere in Python
- **Config:** Environment variables + `.env` for secrets, JSON for config
- **File I/O:** Stages communicate via file paths in `data/` directory
- **API:** FastAPI for the on-demand endpoint
- **Tests:** pytest, one test file per module
- **Comments:** Docstrings on all public functions. Inline comments only for non-obvious logic.

## Verification Gates

Before any sprint is complete:
- [ ] Full test suite passes
- [ ] Typecheck clean (mypy --strict)
- [ ] Lint clean (ruff)
- [ ] No new dependencies without approval
- [ ] All agent log files updated
- [ ] Commit message follows convention