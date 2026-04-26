"""Thin wrapper around the Gemini API.

We use the official `google-genai` SDK and ask the model for JSON that matches
our Pydantic schema directly. That gives us:
- structured, parseable output
- typed objects on the way back into Python
- a single point of retry and error handling
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any

from google import genai
from google.genai import types

from neural_architect.core.models import AttackChain
from neural_architect.llm.prompts import ANALYST_SYSTEM_PROMPT

log = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"
MAX_RETRIES = 3
RETRY_BACKOFF_S = 2.0


class GeminiUnavailableError(RuntimeError):
    """Raised when the Gemini API key is missing or the call fails after retries."""


class GeminiClient:
    """Forensics-flavored Gemini client.

    Centralizes:
      - API key resolution
      - structured output config
      - retry / backoff
      - response validation against `AttackChain`
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        system_prompt: str = ANALYST_SYSTEM_PROMPT,
        request_timeout_s: int = 120,
    ) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise GeminiUnavailableError(
                "GEMINI_API_KEY not set. Get one at https://aistudio.google.com/apikey "
                "and put it in .env or your shell environment."
            )
        self._client = genai.Client(api_key=key)
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)
        self._system_prompt = system_prompt
        self._timeout = request_timeout_s

    @property
    def model(self) -> str:
        return self._model

    def reconstruct(self, user_prompt: str) -> AttackChain:
        """Run the model and return a parsed AttackChain.

        Raises:
            GeminiUnavailableError: if the API call fails after retries.
            ValueError: if the model returns JSON that does not match the schema.
        """
        config = types.GenerateContentConfig(
            system_instruction=self._system_prompt,
            response_mime_type="application/json",
            response_schema=AttackChain,
            temperature=0.2,
            max_output_tokens=8192,
        )

        last_err: Exception | None = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model,
                    contents=user_prompt,
                    config=config,
                )
                return self._parse(response)
            except (ValueError, json.JSONDecodeError) as e:
                # Schema/parse errors are not retryable — the model produced bad JSON.
                raise
            except Exception as e:  # noqa: BLE001 — we want to retry transient API errors
                last_err = e
                log.warning(
                    "Gemini call failed (attempt %d/%d): %s",
                    attempt,
                    MAX_RETRIES,
                    e,
                )
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_BACKOFF_S * attempt)

        raise GeminiUnavailableError(
            f"Gemini API failed after {MAX_RETRIES} attempts: {last_err}"
        ) from last_err

    @staticmethod
    def _parse(response: Any) -> AttackChain:
        # The new SDK exposes parsed output directly when response_schema is set.
        parsed = getattr(response, "parsed", None)
        if isinstance(parsed, AttackChain):
            return parsed

        text = getattr(response, "text", None) or ""
        if not text:
            raise ValueError("Gemini returned an empty response.")
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Gemini returned non-JSON output: {text[:200]}...") from e
        return AttackChain.model_validate(data)
