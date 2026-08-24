import pytest

from dashboard.assistant_service import (
    AssistantServiceError,
    _ollama_url,
)


def test_local_ollama_is_allowed(
    monkeypatch,
):
    monkeypatch.setenv(
        "OLLAMA_URL",
        "http://127.0.0.1:11434/api/generate",
    )

    monkeypatch.setenv(
        "PLANTLIFE365_ALLOW_REMOTE_OLLAMA",
        "false",
    )

    assert (
        _ollama_url()
        == "http://127.0.0.1:11434/api/generate"
    )


def test_remote_ollama_is_blocked_by_default(
    monkeypatch,
):
    monkeypatch.setenv(
        "OLLAMA_URL",
        "https://example.com/api/generate",
    )

    monkeypatch.setenv(
        "PLANTLIFE365_ALLOW_REMOTE_OLLAMA",
        "false",
    )

    with pytest.raises(
        AssistantServiceError
    ):
        _ollama_url()


def test_remote_ollama_requires_explicit_opt_in(
    monkeypatch,
):
    monkeypatch.setenv(
        "OLLAMA_URL",
        "https://example.com/api/generate",
    )

    monkeypatch.setenv(
        "PLANTLIFE365_ALLOW_REMOTE_OLLAMA",
        "true",
    )

    assert (
        _ollama_url()
        == "https://example.com/api/generate"
    )
