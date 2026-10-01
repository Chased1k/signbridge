#!/usr/bin/env python3
"""
SignBridge API — FastAPI service for on-demand ASL video generation.

Endpoints:
  POST /api/jobs        — submit audio file or text, returns job_id
  GET  /api/jobs/{id}   — poll job status
  GET  /api/jobs/{id}/video — download result video
  GET  /api/health      — health check
  GET  /api/stats       — pose library stats
"""

import json
import os
import sys
import uuid
import asyncio
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

app = FastAPI(title="SignBridge API", version="0.1.0")

@app.get("/")
async def root():
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/dashboard/")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job storage (POC — in-memory + file backed)
JOBS_DIR = PROJECT_ROOT / "data" / "output"
JOBS_DIR.mkdir(parents=True, exist_ok=True)
JOBS = {}  # job_id -> {status, stages, created_at, ...}

POSE_LOOKUP = PROJECT_ROOT / "data" / "pose_library" / "pose_lookup.json"


def load_jobs():
    """Load existing job results from disk on startup."""
    for f in JOBS_DIR.glob("*_results.json"):
        try:
            with open(f) as fh:
                data = json.load(fh)
                JOBS[data["job_id"]] = data
        except:
            pass


@app.on_event("startup")
async def startup():
    load_jobs()


@app.get("/api/health")
async def health():
    with open(POSE_LOOKUP) as f:
        lookup = json.load(f)
    return {
        "status": "ok",
        "pose_library_size": len(lookup),
        "jobs_cached": len(JOBS),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/stats")
async def stats():
    with open(POSE_LOOKUP) as f:
        lookup = json.load(f)
    # Count by signer
    signers = {}
    for g, data in lookup.items():
        signer = data.get("signer", "unknown")
        signers[signer] = signers.get(signer, 0) + 1
    return {
        "total_glosses": len(lookup),
        "by_signer": signers,
        "jobs_total": len(JOBS),
        "jobs_completed": sum(1 for j in JOBS.values() if j.get("status") == "ok"),
    }


@app.post("/api/jobs")
async def create_job(
    background_tasks: BackgroundTasks,
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    character_url: Optional[str] = Form(None),
):
    if not audio and not text:
        raise HTTPException(400, "Must provide audio file or text input")

    job_id = f"job_{uuid.uuid4().hex[:8]}"
    
    # Save audio if provided
    audio_path = None
    if audio:
        suffix = Path(audio.filename or "input.mp3").suffix
        audio_path = JOBS_DIR / f"{job_id}_input{suffix}"
        with open(audio_path, "wb") as f:
            f.write(await audio.read())

    # Initial job record
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "created_at": datetime.now().isoformat(),
        "has_audio": audio is not None,
        "text_input": text[:100] if text else None,
        "character_url": character_url,
    }

    # Run pipeline in background
    background_tasks.add_task(run_job, job_id, audio_path, text, character_url)

    return {"job_id": job_id, "status": "queued", "message": "Job submitted. Poll /api/jobs/{job_id} for status."}


def run_job(job_id, audio_path, text, character_url):
    """Background task: run the pipeline."""
    from pipeline import run_pipeline
    JOBS[job_id]["status"] = "processing"
    try:
        result = run_pipeline(
            audio_path=str(audio_path) if audio_path else None,
            text_input=text,
            character_url=character_url,
            output_name=job_id
        )
        JOBS[job_id] = result
    except Exception as e:
        JOBS[job_id]["status"] = "error"
        JOBS[job_id]["error"] = str(e)


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    job = JOBS[job_id]
    # Don't return full stage data (can be large)
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "created_at": job.get("created_at") or job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "coverage": job.get("stages", {}).get("translate", {}).get("data", {}).get("coverage"),
        "glosses": job.get("stages", {}).get("translate", {}).get("data", {}).get("glosses", []),
        "summary": job.get("stages", {}).get("translate", {}).get("data", {}).get("summary"),
        "final_video": job.get("final_video"),
        "error": job.get("error"),
    }


@app.get("/api/jobs/{job_id}/video")
async def get_video(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(404, "Job not found")
    job = JOBS[job_id]
    if job["status"] != "ok" or not job.get("final_video"):
        raise HTTPException(400, f"Job status: {job['status']} — no video available")
    video_path = job["final_video"]
    if not os.path.exists(video_path):
        raise HTTPException(404, "Video file not found")
    return FileResponse(video_path, media_type="video/mp4", filename=f"signbridge_{job_id}.mp4")


# Mount static dashboard
DASHBOARD_DIR = PROJECT_ROOT / "dashboard" / "static"
if DASHBOARD_DIR.exists():
    app.mount("/dashboard", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=18105)