# backend/api_client.py
import os
import requests
import time

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL", "https://api.mistral.ai")
MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "")

def call_mistral(prompt: str, model: str = None, temperature: float = 0.2, timeout: int = 30):
    """
    Minimal HTTP client to call Mistral inference endpoint.
    Adjust path/payload per your Mistral docs.
    Returns the raw parsed JSON response (caller should extract text).
    """
    api_key = os.getenv("MISTRAL_API_KEY") or MISTRAL_API_KEY
    if not api_key:
        raise RuntimeError("MISTRAL_API_KEY not set in environment. Provide key in .env or Streamlit sidebar.")

    model = model or MISTRAL_MODEL
    if model:
        url = f"{MISTRAL_API_URL}/v1/models/{model}/generate"
    else:
        # Generic chat completions endpoint (if modelless)
        url = f"{MISTRAL_API_URL}/v1/chat/completions"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    payload = {
        # The exact payload expected by Mistral may differ; adapt if necessary.
        "input": prompt,
        "temperature": temperature,
        "max_new_tokens": 512,
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()
