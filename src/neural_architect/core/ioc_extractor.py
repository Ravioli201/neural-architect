"""Deterministic IOC extraction.

Runs *before* the LLM. Pulls out IPs, domains, hashes, CVEs, paths, etc.
using regex so the model gets structured anchors and we don't pay tokens
for the model to do work that regex can do faster and more reliably.
"""
from __future__ import annotations

import re
from typing import Iterable

from neural_architect.core.models import Indicator, IndicatorType

# Source: well-known public regex patterns, refined for low false-positive rate.
_PATTERNS: dict[IndicatorType, re.Pattern[str]] = {
    IndicatorType.IPV4: re.compile(
        r"(?<![\d.])"
        r"(?:(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)\.){3}"
        r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
        r"(?![\d.])"
    ),
    IndicatorType.SHA256: re.compile(r"\b[a-fA-F0-9]{64}\b"),
    IndicatorType.SHA1: re.compile(r"\b[a-fA-F0-9]{40}\b"),
    IndicatorType.MD5: re.compile(r"\b[a-fA-F0-9]{32}\b"),
    IndicatorType.CVE: re.compile(r"\bCVE-\d{4}-\d{4,7}\b", re.IGNORECASE),
    IndicatorType.EMAIL: re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    ),
    IndicatorType.URL: re.compile(
        r"\bhttps?://[^\s\"'<>]+",
        re.IGNORECASE,
    ),
    IndicatorType.DOMAIN: re.compile(
        r"\b(?=[a-zA-Z0-9-]{1,63}\.)"
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+"
        r"(?:com|net|org|io|gov|mil|edu|co|us|uk|de|ru|cn|tk|xyz|info|biz|"
        r"top|club|online|site|store|live|me|tv|app|ai|dev)\b",
        re.IGNORECASE,
    ),
    IndicatorType.FILE_PATH: re.compile(
        r"(?:[a-zA-Z]:\\(?:[^\\/:*?\"<>|\r\n\s]+\\)*[^\\/:*?\"<>|\r\n\s]+|"
        r"/(?:usr|etc|var|tmp|opt|home|root)/[^\s\"'<>]+)"
    ),
    IndicatorType.REGISTRY_KEY: re.compile(
        r"\b(?:HKLM|HKCU|HKEY_LOCAL_MACHINE|HKEY_CURRENT_USER)\\[^\s\"'<>]+",
        re.IGNORECASE,
    ),
}

# Avoid flagging RFC1918, loopback, multicast, and broadcast as IOCs by default.
_NOISY_IPS = re.compile(
    r"^(?:0\.|10\.|127\.|169\.254\.|172\.(?:1[6-9]|2\d|3[01])\.|"
    r"192\.168\.|2(?:2[4-9]|3\d)\.|255\.255\.255\.255)"
)


def extract(text: str, *, include_internal: bool = False) -> list[Indicator]:
    """Extract IOCs from a blob of text.

    Args:
        text: raw log content.
        include_internal: if False, internal/private IPs are dropped.
    """
    seen: set[tuple[IndicatorType, str]] = set()
    out: list[Indicator] = []

    for ioc_type, pattern in _PATTERNS.items():
        for match in pattern.finditer(text):
            value = match.group(0)
            if ioc_type is IndicatorType.IPV4 and not include_internal:
                if _NOISY_IPS.match(value):
                    continue
            key = (ioc_type, value.lower())
            if key in seen:
                continue
            seen.add(key)
            out.append(
                Indicator(
                    type=ioc_type,
                    value=value,
                    context=_snippet(text, match.start(), match.end()),
                )
            )
    # Hash precedence: a 64-char hex matches MD5+SHA1+SHA256 patterns by length;
    # collapse duplicates keeping the strongest classification.
    return _dedupe_overlapping_hashes(out)


def _snippet(text: str, start: int, end: int, *, window: int = 60) -> str:
    s = max(0, start - window)
    e = min(len(text), end + window)
    return text[s:e].replace("\n", " ").strip()


def _dedupe_overlapping_hashes(indicators: Iterable[Indicator]) -> list[Indicator]:
    """SHA256 > SHA1 > MD5 when the same byte range matched multiple patterns."""
    by_value: dict[str, Indicator] = {}
    rank = {IndicatorType.SHA256: 3, IndicatorType.SHA1: 2, IndicatorType.MD5: 1}
    for ind in indicators:
        if ind.type not in rank:
            by_value[ind.value.lower() + "::" + ind.type.value] = ind
            continue
        existing = by_value.get(ind.value.lower())
        if existing is None or rank[ind.type] > rank[existing.type]:
            by_value[ind.value.lower()] = ind
    return list(by_value.values())
