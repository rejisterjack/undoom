"""Model providers used by replay. The default CI provider is a caller-supplied fake."""

from __future__ import annotations

import os
from typing import Any, Protocol

from undoom.errors import ReplayError
from undoom.models import ModelResponse
from undoom.openai_messages import parse_completion
from undoom.replay.loading import load_callable


class ModelProvider(Protocol):
    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float,
    ) -> ModelResponse: ...


class OpenAIProvider:
    """Live chat completions. Used when a case is replayed for real."""

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        temperature: float,
    ) -> ModelResponse:
        client = self._client
        if client is None:
            try:
                from openai import OpenAI
            except ImportError as exc:
                raise ReplayError(
                    "OpenAI support is not installed. Install it with: pip install 'undoom[openai]'"
                ) from exc
            client = OpenAI()
            self._client = client
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            kwargs["tools"] = tools
        response = client.chat.completions.create(**kwargs)
        return parse_completion(response)


def resolve_provider(spec: str | None = None) -> ModelProvider:
    """`openai`, or `module:factory` that returns a provider."""

    chosen = spec or os.environ.get("UNDOOM_MODEL_PROVIDER", "openai")
    if chosen == "openai":
        return OpenAIProvider()
    if ":" not in chosen:
        raise ReplayError(f"unknown provider {chosen!r}; use 'openai' or 'module:factory'")
    factory = load_callable(chosen)
    provider = factory()
    if not hasattr(provider, "complete"):
        raise ReplayError(f"{chosen} did not return a model provider")
    return provider
