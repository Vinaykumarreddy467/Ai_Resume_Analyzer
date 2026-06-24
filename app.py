"""AI Resume Analyzer — FastAPI Server

Serves the frontend and provides a /analyze API endpoint
that processes uploaded PDFs through the LLM pipeline.
"""

import json
import time
import os
import re
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from services.pdfreader import extract_text
from services.prompbuilder import build_prompt
from services.llmservice import generate_response
from services.reportgenerator import save_reports
from services.logger import get_logger

log = get_logger("app")

app = FastAPI(title="AI Resume Analyzer")

TEMP_DIR = Path("data/temp")
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ── Serve index.html at root ────────────────────────────────────
HTML_PATH = Path(__file__).parent / "index.html"


@app.get("/", response_class=HTMLResponse)
async def root():
    log.debug("Serving index.html")
    return HTML_PATH.read_text(encoding="utf-8")


# ── Analysis endpoint ───────────────────────────────────────────
@app.post("/analyze")
async def analyze(resume: UploadFile = File(...), jd: UploadFile = File(...)):
    request_id = uuid.uuid4().hex[:8]
    log.info("[%s] Analysis request — resume=%s, jd=%s", request_id, resume.filename, jd.filename)

    # Validate file types
    for f, label in [(resume, "Resume"), (jd, "Job Description")]:
        if not f.filename or not f.filename.lower().endswith(".pdf"):
            log.warning("[%s] Invalid file type: %s (%s)", request_id, f.filename, label)
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
        log.debug("[%s] Temp files written", request_id)

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
            log.warning("[%s] LLM response was not pure JSON — attempting regex extraction", request_id)
            json_match = re.search(r'\{.*\}', analysis_raw, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                log.info("[%s] JSON extracted via regex", request_id)
            else:
                log.error("[%s] No valid JSON found in LLM response", request_id)
                log.debug("[%s] Raw response (first 500): %s", request_id, analysis_raw[:500])
                raise HTTPException(500, f"LLM returned invalid JSON:\n{analysis_raw[:500]}")

        # Add metadata
        analysis["total_runtime_seconds"] = round(total_end - total_start, 2)
        analysis["llm_runtime_seconds"] = round(llm_end - llm_start, 2)
        analysis["processing_runtime_seconds"] = round(
            (total_end - total_start) - (llm_end - llm_start), 2
        )
        analysis["resume_filename"] = resume.filename
        analysis["jd_filename"] = jd.filename

        log.info("[%s] Analysis complete — score=%s, runtime=%.2fs, llm=%.2fs",
                 request_id, analysis.get("match_score"), total_end - total_start, llm_end - llm_start)

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
        log.error("[%s] Analysis failed: %s", request_id, e, exc_info=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")
    finally:
        # Cleanup temp files
        for p in [resume_path, jd_path]:
            if p.exists():
                p.unlink()
                log.debug("[%s] Cleaned up temp file: %s", request_id, p.name)


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
        except Exception as e:
            log.warning("Skipping corrupt report file: %s (%s)", f.name, e)
            continue

    log.debug("Listed %d reports", len(reports))
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
            log.warning("Directory traversal attempt: %s", filename)
            raise HTTPException(400, "Invalid path")
    except (ValueError, FileNotFoundError):
        raise HTTPException(404, "Report not found")

    data = json.loads(filepath.read_text(encoding="utf-8"))
    log.debug("Downloaded report: %s", filename)
    return JSONResponse(data)


# ── 404 handler ────────────────────────────────────────────────
@app.exception_handler(StarletteHTTPException)
async def not_found_handler(request, exc):
    if exc.status_code == 404:
        return JSONResponse({"error": "Not found"}, status_code=404)
    raise exc
