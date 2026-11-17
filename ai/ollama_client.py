"""Small adapter around the official Ollama Python SDK."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

try:
    import ollama
except ImportError:  # pragma: no cover - exercised when dependencies are missing
    ollama = None  # type: ignore[assignment]


class OllamaClientError(RuntimeError):
    """Raised when Ollama cannot be reached or returns an invalid response."""


def _as_dict(value: Any) -> dict[str, Any]:
    """Convert SDK response models and dictionaries to a plain dictionary."""
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    raise OllamaClientError("Ollama returned an unsupported response type.")


class OllamaClient:
    """Ollama chat client configured for one local model."""

    def __init__(self, host: str, model: str) -> None:
        if ollama is None:
            raise OllamaClientError(
                "The Ollama Python SDK is not installed for this Python interpreter. "
                "Create/activate the project virtual environment and run "
                "'python -m pip install -r requirements.txt'."
            )
        self.model = model
        self._client = ollama.Client(host=host)

    def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        tools: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        """Send a conversation and tool schemas to Ollama."""
        try:
            response = self._client.chat(
                model=self.model,
                messages=list(messages),
                tools=list(tools),
            )
        except Exception as error:  # SDK exception types vary by version.
            raise OllamaClientError(f"Ollama request failed: {error}") from error
        return _as_dict(response)
