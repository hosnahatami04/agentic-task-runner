"""Thin wrapper around the Ollama Python client with retry logic."""

from __future__ import annotations

import time

import ollama

DEFAULT_MODEL = "qwen2.5:7b-instruct"
DEFAULT_HOST = "http://127.0.0.1:11434"
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

_client = ollama.Client(host=DEFAULT_HOST, trust_env=False)


class OllamaConnectionError(Exception):
    """Raised when Ollama cannot be reached after all retries are exhausted."""


def generate(prompt: str, model: str = DEFAULT_MODEL) -> str:
    """Send a prompt to Ollama and return the model's text response.

    Blocking call: waits for the full response before returning (no streaming).
    Retries on connection errors since Ollama may be briefly unavailable
    (e.g. still loading the model into memory).
    """
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = _client.generate(model=model, prompt=prompt, stream=False)
            return response["response"]
        except (ollama.ResponseError, ConnectionError) as exc:
            last_error = exc
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    raise OllamaConnectionError(
        f"Failed to reach Ollama after {MAX_RETRIES} attempts"
    ) from last_error
