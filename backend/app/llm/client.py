"""Thin wrapper around the LiteLLM call to OpenRouter/Cerebras."""

from __future__ import annotations

from litellm import completion

from .models import ChatResponse

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}


def call_llm(messages: list[dict]) -> str:
    """Synchronous call to the LLM requesting structured output. Returns raw JSON text."""
    response = completion(
        model=MODEL,
        messages=messages,
        response_format=ChatResponse,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
    )
    return response.choices[0].message.content
