# AI Resume Analyzer

A web-based tool that compares a candidate's resume PDF against a job description PDF using a local LLM (Ollama), then displays a structured analysis in a beautiful dashboard.

## Features

- **Web UI** with drag-and-drop PDF upload
- **Real-time progress** — animated timeline shows each step
- **ATS-style comparison** — match score, matching/missing skills, strengths, weaknesses, recommendations
- **Local LLM** — runs entirely on your machine via Ollama (no API keys needed)
- **Report history** — browse and download past analyses
- **Animated dashboard** — glassmorphism design with card reveal animations

## Project Structure

```
ai-resume-analyzer/
├── app.py                # FastAPI web server (run this)
├── main.py               # CLI entry point (alternative)
├── index.html            # Frontend dashboard
├── .env                  # Ollama config (URL + model name)
├── .gitignore
├── README.md
├── data/
│   ├── resume.pdf        # Place your resume PDF here
│   └── jd.pdf            # Place your job description PDF here
├── reports/              # Generated JSON analysis reports
├── services/
│   ├── pdfreader.py       # PDF text extraction via pypdf
│   ├── prompbuilder.py    # Builds the LLM prompt
│   ├── llmservice.py      # Calls Ollama API (streaming)
│   └── reportgenerator.py # Saves analysis as JSON
└── venv/                 # Python virtual environment (local)
```

## Prerequisites

- [Ollama](https://ollama.com) installed and running
- Python 3.8+
- A model pulled in Ollama (e.g., `ollama pull phi3:latest`)

## Setup

1. Clone the repo:
   ```bash
   git clone https://github.com/Vinaykumarreddy467/Ai_Resume_Analyzer.git
   cd Ai_Resume_Analyzer
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
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

### Web UI (Recommended)

```bash
source venv/bin/activate
python app.py
```

Open **http://localhost:8000** in your browser. Upload both PDFs and click **Start Analysis**.

### CLI Mode

```bash
source venv/bin/activate
python main.py
```

The script extracts text from both PDFs, runs the analysis, prints the streaming response, and saves the report to `reports/`.

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Serves the frontend dashboard |
| `/analyze` | POST | Upload resume + JD PDFs, returns analysis JSON |
| `/reports` | GET | Lists all past analysis reports |
| `/reports/{filename}` | GET | Downloads a specific report JSON |

### Example Output

```json
{
    "candidate_name": "John Doe",
    "candidate_role": "Full Stack Developer",
    "match_score": 87,
    "matching_skills": ["JavaScript", "React", "Python"],
    "missing_skills": ["Kubernetes", "Terraform"],
    "strengths": ["Strong full-stack experience"],
    "weaknesses": ["Limited DevOps experience"],
    "recommendations": ["Learn Kubernetes"],
    "total_runtime_seconds": 8.42,
    "llm_runtime_seconds": 6.10,
    "processing_runtime_seconds": 2.32
}
```

## Performance

Runs entirely locally via Ollama — no API keys, no data leaves your machine. Performance depends on your hardware and model choice:

| Model | Size | Est. Time (CPU, 4 cores) |
|---|---|---|
| phi3:latest | 2.2 GB | ~25-40 sec |
| qwen2.5-coder:7b | 4.7 GB | ~60-90 sec |
| gemma4:latest | 9.6 GB | ~90+ sec |
