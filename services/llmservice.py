"""LLM Service — Groq cloud API only.

Fast, reliable, no local dependencies.
"""

import os
import json
import requests
from dotenv import load_dotenv
from services.logger import get_logger

load_dotenv()
log = get_logger("llmservice")

# ── Groq config ───────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_groq(prompt):
    """Call Groq API and return the response text."""
    log.info("Calling Groq model: %s", GROQ_MODEL)

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 4096,
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()
    content = data["choices"][0]["message"]["content"]
    log.info("Groq response received (%d chars, %d tokens)",
             len(content), data.get("usage", {}).get("total_tokens", "?"))
    return content


def generate_response(prompt):
    """Generate a response using Groq cloud API."""
    if not GROQ_API_KEY:
        log.error("GROQ_API_KEY is not set in .env")
        raise RuntimeError(
            "GROQ_API_KEY is not set in .env.\n"
            "Get a free key at https://console.groq.com/keys"
        )

    return _call_groq(prompt)
