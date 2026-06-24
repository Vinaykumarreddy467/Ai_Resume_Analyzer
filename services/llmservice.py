"""LLM Service — Auto-detects Ollama (local) or falls back to Groq (cloud).

Priority:
1. Ollama — if the server is reachable at OLLAMA_URL
2. Groq — if Ollama is down and GROQ_API_KEY is set
3. Error — if neither is available
"""

import os
import time
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Ollama config ──────────────────────────────────────────────
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:latest")

# ── Groq config (fallback) ─────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3-70b-8192")

# ── Provider detection (cached for the lifetime of the process) ─
_use_ollama = None


def _check_ollama():
    """Return True if Ollama is reachable."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        return r.status_code == 200
    except requests.RequestException:
        return False


def _get_provider():
    """Determine which provider to use. Result is cached."""
    global _use_ollama
    if _use_ollama is None:
        if _check_ollama():
            print(f"[LLM] ✅ Ollama detected at {OLLAMA_URL}")
            _use_ollama = True
        elif GROQ_API_KEY:
            print("[LLM] ☁️  Ollama not detected — falling back to Groq")
            _use_ollama = False
        else:
            print("[LLM] ❌ No LLM provider available (Ollama offline and no GROQ_API_KEY)")
            _use_ollama = False  # will raise on first request
    return _use_ollama


def _call_ollama(prompt):
    """Stream response from Ollama."""
    print(f"[LLM] Calling Ollama model: {OLLAMA_MODEL}")
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": True},
        stream=True,
        timeout=300,
    )
    response.raise_for_status()

    full = ""
    for line in response.iter_lines():
        if not line:
            continue
        chunk = json.loads(line)
        token = chunk.get("response", "")
        print(token, end="", flush=True)
        full += token
    print()
    return full


def _call_groq(prompt):
    """Call Groq API (non-streaming for simplicity)."""
    print(f"[LLM] Calling Groq model: {GROQ_MODEL}")
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
    print(content)
    return content


def generate_response(prompt):
    """Generate a response using the best available provider."""
    if _get_provider():
        # Ollama is available
        if OLLAMA_MODEL:
            return _call_ollama(prompt)
        else:
            raise RuntimeError(
                "Ollama is running but OLLAMA_MODEL is not set in .env"
            )
    elif GROQ_API_KEY:
        # Groq fallback
        return _call_groq(prompt)
    else:
        raise RuntimeError(
            "No LLM provider available.\n"
            "  • Start Ollama (ollama serve) OR\n"
            "  • Set GROQ_API_KEY in .env (get one at https://console.groq.com/keys)"
        )
