"""LLM Service — Tries Ollama first with a timeout, falls back to Groq.

Priority:
1. Ollama — with 60-second total timeout (if reachable)
2. Groq — if Ollama times out, is unavailable, or GROQ_API_KEY is set explicitly
3. Error — if neither is available
"""

import os
import time
import json
import requests
from dotenv import load_dotenv
from services.logger import get_logger

load_dotenv()
log = get_logger("llmservice")

# ── Ollama config ──────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")
OLLAMA_TIMEOUT = 60  # seconds — switch to Groq if Ollama exceeds this


# ── Groq config (fallback) ─────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")


# ── Exceptions ─────────────────────────────────────────────────
class ProviderTimeout(Exception):
    """Raised when the active provider takes too long to respond."""
    pass


# ── Helpers ────────────────────────────────────────────────────

def _ollama_reachable():
    """Quick check — is Ollama running?"""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _has_groq():
    return bool(GROQ_API_KEY)


# ── Ollama (streaming, with total-timeout) ─────────────────────

def _call_ollama(prompt):
    """Stream response from Ollama. Raises ProviderTimeout if > OLLAMA_TIMEOUT."""
    log.info("Calling Ollama model: %s", OLLAMA_MODEL)
    deadline = time.time() + OLLAMA_TIMEOUT

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
        stream=True,
        timeout=(10, OLLAMA_TIMEOUT),  # connect timeout, then read timeout
    )
    response.raise_for_status()

    full = ""
    for line in response.iter_lines():
        if time.time() > deadline:
            log.warning("Ollama timed out after %ds — aborting", OLLAMA_TIMEOUT)
            raise ProviderTimeout(
                f"Ollama took longer than {OLLAMA_TIMEOUT}s"
            )
        if not line:
            continue
        chunk = json.loads(line)
        token = chunk.get("response", "")
        full += token
    log.info("Ollama streaming complete (%d chars)", len(full))
    return full


# ── Groq (cloud) ───────────────────────────────────────────────

def _call_groq(prompt):
    """Call Groq API (non-streaming)."""
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
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"]
    log.info("Groq response received (%d chars)", len(content))
    return content


# ── Main entry point ───────────────────────────────────────────

def generate_response(prompt):
    """Generate a response — tries Ollama (with timeout), falls back to Groq."""

    ollama_up = _ollama_reachable()

    # ── Try Ollama first if it's running ───────────────────────
    if ollama_up:
        if not OLLAMA_MODEL:
            raise RuntimeError("Ollama is running but OLLAMA_MODEL is not set in .env")
        try:
            log.info("Ollama reachable — trying local inference")
            return _call_ollama(prompt)
        except ProviderTimeout:
            log.warning("Ollama timed out — switching to Groq")
        except requests.RequestException as e:
            log.error("Ollama error: %s — switching to Groq", e)

        # Fall through to Groq on timeout / error
        if not _has_groq():
            raise RuntimeError(
                "Ollama failed and no GROQ_API_KEY is set in .env.\n"
                "  • Set a shorter model in .env (e.g., OLLAMA_MODEL=phi3:latest)\n"
                "  • Or set GROQ_API_KEY for cloud fallback"
            )

    # ── Fallback: Groq ─────────────────────────────────────────
    if _has_groq():
        log.info("Using Groq cloud fallback")
        return _call_groq(prompt)

    # ── Nothing works ──────────────────────────────────────────
    log.error("No LLM provider available (Ollama down, no GROQ_API_KEY)")
    raise RuntimeError(
        "No LLM provider available.\n"
        "  • Start Ollama (ollama serve) OR\n"
        "  • Set GROQ_API_KEY in .env (get one at https://console.groq.com/keys)"
    )
