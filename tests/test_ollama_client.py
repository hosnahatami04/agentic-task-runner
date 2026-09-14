"""Tests for src/llm/ollama_client.py."""

from unittest.mock import patch

import ollama
import pytest

from llm.ollama_client import OllamaConnectionError, _client, generate


def _ollama_available() -> bool:
    try:
        _client.list()
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _ollama_available(), reason="Ollama is not running")
def test_generate_returns_text_from_real_ollama():
    result = generate("Respond with exactly the word: OK")

    assert isinstance(result, str)
    assert len(result) > 0


def test_generate_retries_then_succeeds():
    responses = [
        ollama.ResponseError("temporary failure"),
        {"response": "hello"},
    ]

    with patch("llm.ollama_client._client.generate", side_effect=responses):
        with patch("llm.ollama_client.time.sleep") as mock_sleep:
            result = generate("hi")

    assert result == "hello"
    assert mock_sleep.call_count == 1


def test_generate_raises_after_max_retries():
    with patch(
        "llm.ollama_client._client.generate",
        side_effect=ollama.ResponseError("still failing"),
    ):
        with patch("llm.ollama_client.time.sleep"):
            with pytest.raises(OllamaConnectionError):
                generate("hi")
