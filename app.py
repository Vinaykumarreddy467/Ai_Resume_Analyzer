"""AI Resume Analyzer — FastAPI Server

Serves the frontend and provides a /analyze API endpoint
that processes uploaded PDFs through the LLM pipeline.
"""

import json
import time
import os
import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from services.pdfreader import extract_text
from services.prompbuilder import build_prompt
from services.llmservice import generate_response
from services.reportgenerator import save_reports

app = FastAPI(title="AI Resume Analyzer")

TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ── Serve index.html at root ────────────────────────────────────
HTML_PATH = Path(__file__).parent / "index.html"


@app.get("/", response_class=HTMLResponse)
async def root():
    return HTML_PATH.read_text(encoding="utf-8")


# ── Analysis endpoint ───────────────────────────────────────────
@app.post("/analyze")
async def analyze(resume: UploadFile = File(...), jd: UploadFile = File(...)):
    # Validate file types
    for f, label in [(resume, "Resume"), (jd, "Job Description")]:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            raise HTTPException(400, f"{label} must be a PDF file")

    # Save uploaded PDFs to temp
    resume_path = TEMP_DIR / f"{uuid.uuid4().hex}_resume.pdf"
    jd_path = TEMP_DIR / f"{uuid.uuid4().hex}_jd.pdf"

    try:
        # Write files
        for src, dst in [(resume, resume_path), (jd, jd_path)]:
            with open(dst, "wb") as f:
                content = await src.read()
                f.write(content)

        # ── Pipeline ──────────────────────────────────────────
        total_start = time.time()

        resume_text = extract_text(str(resume_path))
        jd_text = extract_text(str(jd_path))

        prompt = build_prompt(resume_text, jd_text)

        llm_start = time.time()
        analysis_raw = generate_response(prompt)
        llm_end = time.time()

        total_end = time.time()

        # Parse JSON from LLM
        try:
            analysis = json.loads(analysis_raw)
        except json.JSONDecodeError:
            # Try to find JSON block in the response
            import re
            json_match = re.search(r'\{.*\}', analysis_raw, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                raise HTTPException(500, f"LLM returned invalid JSON:\n{analysis_raw[:500]}")

        # Add metadata
        analysis["total_runtime_seconds"] = round(total_end - total_start, 2)
        analysis["llm_runtime_seconds"] = round(llm_end - llm_start, 2)
        analysis["processing_runtime_seconds"] = round(
            (total_end - total_start) - (llm_end - llm_start), 2
        )
        analysis["resume_filename"] = resume.filename
        analysis["jd_filename"] = jd.filename

        # Save report
        report_path = save_reports(analysis)

        return JSONResponse({
            "success": True,
            "data": analysis,
            "report_path": report_path,
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        # Cleanup temp files
        for p in [resume_path, jd_path]:
            if p.exists():
                p.unlink()


# ── List past reports ──────────────────────────────────────────
@app.get("/reports")
async def list_reports():
    reports_dir = Path("reports")
    if not reports_dir.exists():
        return {"reports": []}

    reports = []
    for f in sorted(reports_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            reports.append({
                "filename": f.name,
                "candidate_name": data.get("candidate_name", "Unknown"),
                "candidate_role": data.get("candidate_role", "Unknown"),
                "match_score": data.get("match_score"),
                "resume_filename": data.get("resume_filename", "Unknown"),
                "jd_filename": data.get("jd_filename", "Unknown"),
                "timestamp": data.get("total_runtime_seconds"),
            })
        except Exception:
            continue

    return {"reports": reports}


# ── Download a report ──────────────────────────────────────────
@app.get("/reports/{filename}")
async def download_report(filename: str):
    reports_dir = Path("reports")
    filepath = reports_dir / filename

    # Prevent directory traversal
    try:
        filepath = filepath.resolve(strict=True)
        reports_dir = reports_dir.resolve()
        if not str(filepath).startswith(str(reports_dir)):
            raise HTTPException(400, "Invalid path")
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Report not found")

    data = json.loads(filepath.read_text(encoding="utf-8"))
    return JSONResponse(data)


# ── Serve static assets (if any in future) ─────────────────────
@app.exception_handler(StarletteHTTPException)
async def not_found_handler(request, exc):
    if exc.status_code == 404:
        return JSONResponse({"error": "Not found"}, status_code=404)
    raise exc
