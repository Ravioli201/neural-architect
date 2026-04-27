"""Interactive SOC analyst chatbot.

Anchors a Gemini chat session to a specific reconstructed incident so an
analyst can ask follow-ups — "why is T1566.001 only medium confidence?",
"what should I do first?", "what's the right Sigma rule for this?" —
without re-supplying the whole context every turn.
"""
from __future__ import annotations

import os
from typing import Optional

from google import genai
from google.genai import types

DEFAULT_MODEL = "gemini-2.5-flash"


class SOCChatbot:
    """Stateful chat session anchored to a specific incident."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY is required for the chatbot. "
                "Get one at https://aistudio.google.com/apikey."
            )
        self._client = genai.Client(api_key=key)
        self._model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

    def start_session(self, attack_chain_summary: str):
        """Begin a chat session conditioned on a specific incident summary.

        The summary is wired into the system prompt so the model has the
        incident context for every subsequent message in this session.
        """
        system_instruction = (
            "You are an expert SOC Tier-3 analyst assisting another analyst "
            "with an incident they just reconstructed.\n\n"
            "Incident context:\n"
            f"{attack_chain_summary}\n\n"
            "Answer questions accurately, suggest concrete remediation steps, "
            "and explain MITRE ATT&CK techniques in plain language. If you "
            "do not know, say so — never invent IOCs or attribution."
        )
        return self._client.chats.create(
            model=self._model,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
            ),
        )

    @staticmethod
    def ask(chat_session, query: str) -> str:
        """Send a message in an existing session and return the model's reply."""
        response = chat_session.send_message(query)
        return response.text or ""