# AI Resume Analyzer

A Python tool that compares a candidate's resume PDF against a job description PDF using a local LLM (Ollama), then generates a structured analysis report.

## Features

- Extracts text from resume and job description PDFs
- Sends both to a local LLM for ATS-style comparison
- Returns structured analysis: match score, matching/missing skills, strengths, weaknesses, recommendations
- Saves results as timestamped JSON reports
- Built-in HTML dashboard with drag-and-drop upload and visual results (standalone demo)

## Project Structure

```
ai-resume-analyzer/
├── .env                  # Ollama config (URL + model name)
├── .gitignore
├── README.md
├── main.py               # Entry point — runs the full analysis pipeline
├── index.html            # Frontend dashboard (static demo, not connected to backend)
├── data/
│   ├── resume.pdf        # Place your resume PDF here
│   └── jd.pdf            # Place your job description PDF here
├── reports/              # Generated JSON analysis reports
└── services/
    ├── pdfreader.py       # PDF text extraction via pypdf
    ├── prompbuilder.py    # Builds the LLM prompt
    ├── llmservice.py      # Calls Ollama API (streaming)
    └── reportgenerator.py # Saves analysis as JSON
```

## Prerequisites

- [Ollama](https://ollama.com) installed and running
- Python 3.8+
- A model pulled in Ollama (e.g., `ollama pull phi3:latest`)

## Setup

1. Clone the repo:
   ```bash
   git clone <repo-url>
   cd ai-resume-analyzer
   ```

2. Install dependencies:
   ```bash
   pip install pypdf requests python-dotenv
   ```

3. Configure the model in `.env`:
   ```
   OLLAMA_URL=http://localhost:11434
   MODEL_NAME=phi3:latest
   ```

4. Place your PDFs:
   - `data/resume.pdf` — candidate resume
   - `data/jd.pdf` — job description

## Usage

```bash
python main.py
```

The script will:
1. Extract text from both PDFs
2. Build a comparison prompt
3. Send it to your local LLM
4. Print the streaming response
5. Parse the JSON output
6. Save the report to `reports/`

### Example Output

```json
{
    "candidate_name": "John Doe",
    "candidate_role": "Full Stack Developer",
    "match_score": 87,
    "matching_skills": ["JavaScript", "React", "Python", ...],
    "missing_skills": ["Kubernetes", "Terraform", ...],
    "strengths": ["Strong full-stack experience", ...],
    "weaknesses": ["Limited DevOps experience", ...],
    "recommendations": ["Learn Kubernetes", ...]
}
```

## HTML Dashboard

`index.html` provides a visual frontend with:
- Drag-and-drop PDF upload
- Animated progress timeline
- Metrics, results, and insights cards
- Local report history (saved in browser)

> **Note:** The frontend is a standalone demo with hardcoded sample data. It is not currently connected to the Python backend.

## Performance

Runs entirely locally via Ollama — no API keys, no data leaves your machine. Performance depends on your hardware and model choice:

| Model | Size | Est. Time (CPU) |
|---|---|---|
| phi3:latest | 2.2 GB | ~25-40 sec |
| qwen2.5-coder:7b | 4.7 GB | ~60-90 sec |
| gemma4:latest | 9.6 GB | ~90+ sec |
