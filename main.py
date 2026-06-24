"""CLI entry point for AI Resume Analyzer."""

import json
import time
from services.pdfreader import extract_text
from services.prompbuilder import build_prompt
from services.llmservice import generate_response
from services.reportgenerator import save_reports
from services.logger import get_logger

log = get_logger("cli")

total_start = time.time()

log.info("Reading resume from data/resume.pdf")
resume_text = extract_text("data/resume.pdf")

log.info("Reading job description from data/jd.pdf")
jd_text = extract_text("data/jd.pdf")

print("=" * 50)
print("Resume Text:")
print("=" * 50)
print(resume_text)
print("\n\n")

print("=" * 50)
print("Job Description Text:")
print("=" * 50)
print(jd_text)
print("\n\n")

log.info("Resume: %d chars | JD: %d chars", len(resume_text), len(jd_text))

prompt = build_prompt(resume_text, jd_text)

log.info("Prompt built (%d chars)", len(prompt))

llm_start = time.time()

log.info("Calling LLM...")
analysis = generate_response(prompt)

llm_end = time.time()

print("\n\n")
print("=" * 50)
print("RESUME ANALYSIS:")
print("=" * 50)
print(analysis)

total_end = time.time()

try:
    analysis_dict = json.loads(analysis)
    analysis_dict["total_runtime_seconds"] = total_end - total_start
    analysis_dict["llm_runtime_seconds"] = llm_end - llm_start
    analysis_dict["processing_runtime_seconds"] = (total_end - total_start) - (llm_end - llm_start)

    log.info("JSON parsed successfully — match_score=%s", analysis_dict.get("match_score"))

except json.JSONDecodeError as e:
    log.error("JSON decode error: %s", e)
    print("\nJSON ERROR:")
    print(e)
    print("\nRAW RESPONSE:")
    print(analysis)
    exit(1)

report_path = save_reports(analysis_dict)
print(f"Report saved at: {report_path}")
log.info("CLI run complete — report saved to %s", report_path)

