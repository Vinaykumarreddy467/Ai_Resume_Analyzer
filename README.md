# AI Resume Analyzer

A web-based tool that compares a candidate's resume PDF against a job description PDF using **Groq cloud API**, then displays a structured analysis in a beautiful animated dashboard.

## Features

- **Web UI** with drag-and-drop PDF upload
- **Real-time progress** — animated timeline shows each step
- **ATS-style comparison** — match score, matching/missing skills, strengths, weaknesses, recommendations
- **Groq cloud AI** — blazing fast responses (~2 seconds)
- **Report history** — browse and download past analyses
- **Structured logging** — console + file + error logs for tracing issues
- **Animated dashboard** — glassmorphism design with card reveal animations

## Project Structure

```
ai-resume-analyzer/
├── app.py                # FastAPI web server (run this)
├── main.py               # CLI entry point (alternative)
├── index.html            # Frontend dashboard
├── .env.example          # Template for environment variables
├── .gitignore
├── requirements.txt
├── README.md
├── data/temp/            # Temporary uploaded PDFs (auto-cleaned)
├── reports/              # Generated JSON analysis reports
├── logs/                 # Application logs
│   ├── analyzer.log      # Full debug log
│   └── errors.log        # Errors only
├── services/
│   ├── logger.py          # Centralized logging setup
│   ├── pdfreader.py       # PDF text extraction via pypdf
│   ├── prompbuilder.py    # Builds the LLM prompt
│   ├── llmservice.py      # Groq cloud API client
│   └── reportgenerator.py # Saves analysis as JSON
└── venv/                 # Python virtual environment (local)
```

## Prerequisites

- Python 3.8+
- A **Groq API key** (free) — get one at [console.groq.com/keys](https://console.groq.com/keys)

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

3. Configure your Groq API key in `.env`:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your key:
   ```
   GROQ_API_KEY=gsk_your_key_here
   GROQ_MODEL=llama-3.1-8b-instant
   ```

## Usage

### Web UI (Recommended)

```bash
source venv/bin/activate
python app.py
```

Open **http://localhost:8000** in your browser. Upload both PDFs and click **Start Analysis**.

### CLI Mode

Place your PDFs in the `data/` folder:
```
data/
├── resume.pdf
└── jd.pdf
```

Then run:
```bash
source venv/bin/activate
python main.py
```

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
    "candidate_name": "Vinay Kumar Reddy",
    "candidate_role": "Front-end Developer",
    "match_score": 60,
    "matching_skills": ["JavaScript", "React", "HTML/CSS"],
    "missing_skills": ["Java", "Spring Boot", "Microservices"],
    "strengths": ["Strong frontend experience with modern frameworks"],
    "weaknesses": ["Limited backend and Java ecosystem experience"],
    "recommendations": ["Learn Spring Boot", "Build backend projects"],
    "total_runtime_seconds": 2.48,
    "llm_runtime_seconds": 2.33,
    "processing_runtime_seconds": 0.15
}
```

## Logs

All application activity is logged automatically:

| File | Level | Contents |
|---|---|---|
| `logs/analyzer.log` | DEBUG+ | Every step — PDF extraction, prompt, LLM call, results |
| `logs/errors.log` | ERROR+ | Only errors with full Python tracebacks |

Set log levels via environment variables:
```bash
LOG_LEVEL_CONSOLE=DEBUG   # More verbose console output
LOG_LEVEL_FILE=INFO       # Less verbose file output
```

## Performance

Powered by **Groq cloud API** — no local GPU or model downloads needed. Typical response time: **~2 seconds** per analysis.
