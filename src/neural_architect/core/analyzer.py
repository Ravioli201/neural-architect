"""High-level orchestrator: raw logs in, AttackChain out.

This is the public surface most callers (Streamlit, FastAPI, CLI, eval
harness) interact with. It composes the deterministic pre-processing
(log normalization + IOC extraction) with the Gemini reconstruction.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from neural_architect.core import ioc_extractor, log_parser
from neural_architect.core.models import AttackChain, Indicator
from neural_architect.llm.gemini_client import GeminiClient
from neural_architect.llm.prompts import USER_PROMPT_TEMPLATE

log = logging.getLogger(__name__)

# Keep raw excerpt bounded to protect context window and cost.
RAW_EXCERPT_BYTES = 60_000
TIMELINE_PREVIEW_N = 40


class Analyzer:
    """End-to-end attack-chain reconstruction.

    Example:
        >>> analyzer = Analyzer()
        >>> chain = analyzer.analyze(open("incident.log").read())
        >>> chain.severity
        <Severity.HIGH: 'high'>
    """

    def __init__(self, client: GeminiClient | None = None) -> None:
        self._client = client or GeminiClient()

    def analyze(self, raw_log: str, *, incident_id: str | None = None) -> AttackChain:
        if not raw_log or not raw_log.strip():
            raise ValueError("raw_log is empty.")

        fmt = log_parser.detect_format(raw_log)
        events = log_parser.normalize(raw_log)
        iocs = ioc_extractor.extract(raw_log)

        log.info(
            "Pre-LLM pass: format=%s events=%d iocs=%d",
            fmt,
            len(events),
            len(iocs),
        )

        prompt = self._build_prompt(
            fmt=fmt,
            events=events,
            iocs=iocs,
            raw_log=raw_log,
        )

        chain = self._client.reconstruct(prompt)

        # Stamp ID + merge regex-extracted IOCs that the model may have missed.
        chain.incident_id = incident_id or chain.incident_id or _new_incident_id()
        chain.indicators = _merge_indicators(chain.indicators, iocs)
        return chain

    @staticmethod
    def _build_prompt(
        *,
        fmt: str,
        events: list[log_parser.NormalizedEvent],
        iocs: list[Indicator],
        raw_log: str,
    ) -> str:
        ioc_lines = "\n".join(
            f"- [{i.type.value}] {i.value}" for i in iocs[:80]
        ) or "(none extracted)"

        timeline_lines = []
        for e in events[:TIMELINE_PREVIEW_N]:
            ts = e.timestamp or "?"
            src = e.source or "?"
            preview = e.raw[:200].replace("\n", " ")
            timeline_lines.append(f"{ts} [{src}] {preview}")
        timeline_preview = "\n".join(timeline_lines) or "(no events normalized)"

        excerpt = raw_log[:RAW_EXCERPT_BYTES]
        if len(raw_log) > RAW_EXCERPT_BYTES:
            excerpt += f"\n... [truncated, {len(raw_log) - RAW_EXCERPT_BYTES} more bytes]"

        return USER_PROMPT_TEMPLATE.format(
            fmt=fmt,
            event_count=len(events),
            ioc_count=len(iocs),
            iocs=ioc_lines,
            preview_n=TIMELINE_PREVIEW_N,
            timeline_preview=timeline_preview,
            raw_excerpt=excerpt,
        )


def _new_incident_id() -> str:
    return f"INC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


def _merge_indicators(
    from_model: list[Indicator],
    from_regex: list[Indicator],
) -> list[Indicator]:
    """Union of model-found and regex-found IOCs, deduped by (type, value)."""
    seen = {(i.type, i.value.lower()) for i in from_model}
    merged = list(from_model)
    for ind in from_regex:
        if (ind.type, ind.value.lower()) not in seen:
            merged.append(ind)
            seen.add((ind.type, ind.value.lower()))
    return merged
