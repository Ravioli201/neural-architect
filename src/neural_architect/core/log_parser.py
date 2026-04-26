"""Lightweight log normalizer.

The job here is *not* to be a full SIEM parser. The job is to detect the log
format, chunk it sensibly, and produce a normalized representation we can
feed to Gemini alongside the raw text — without blowing the context window.

Supported (best-effort) formats:
- JSON Lines (one event per line)
- Sysmon / Windows Event JSON
- Syslog / auth.log
- Apache/Nginx combined access log
- CSV with a header row
- Plain text fallback
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterator

from dateutil import parser as date_parser

_SYSLOG_RE = re.compile(
    r"^(?P<ts>\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})\s+"
    r"(?P<host>\S+)\s+"
    r"(?P<proc>[^:\[\s]+)(?:\[(?P<pid>\d+)\])?:\s+"
    r"(?P<msg>.*)$"
)

_APACHE_RE = re.compile(
    r"^(?P<ip>\S+)\s+\S+\s+(?P<user>\S+)\s+\[(?P<ts>[^\]]+)\]\s+"
    r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<proto>[^"]+)"\s+'
    r"(?P<status>\d+)\s+(?P<size>\S+)"
    r'(?:\s+"(?P<ref>[^"]*)"\s+"(?P<ua>[^"]*)")?'
)


@dataclass
class NormalizedEvent:
    raw: str
    timestamp: str | None
    source: str | None
    fields: dict[str, str]


def detect_format(text: str) -> str:
    sample = text.lstrip()[:4000]
    if not sample:
        return "empty"
    first_lines = [ln for ln in sample.splitlines() if ln.strip()][:20]
    # JSONL must be checked first: a multi-line file where every line is its
    # own JSON object would otherwise be misclassified as a single JSON blob
    # (which then fails to parse).
    if len(first_lines) > 1 and all(ln.startswith("{") for ln in first_lines):
        return "jsonl"
    if sample.startswith("{") or sample.startswith("["):
        return "json"
    if any(_SYSLOG_RE.match(ln) for ln in first_lines):
        return "syslog"
    if any(_APACHE_RE.match(ln) for ln in first_lines):
        return "apache"
    if first_lines and "," in first_lines[0] and len(first_lines) > 1:
        return "csv"
    return "text"


def normalize(text: str) -> list[NormalizedEvent]:
    fmt = detect_format(text)
    parser = _PARSERS.get(fmt, _parse_text)
    return list(parser(text))


def _parse_jsonl(text: str) -> Iterator[NormalizedEvent]:
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            yield NormalizedEvent(raw=line, timestamp=None, source=None, fields={})
            continue
        ts = _coerce_ts(obj.get("@timestamp") or obj.get("timestamp") or obj.get("time"))
        src = obj.get("source") or obj.get("host") or obj.get("Computer")
        flat = {k: str(v) for k, v in _flatten(obj).items()}
        yield NormalizedEvent(raw=line, timestamp=ts, source=src, fields=flat)


def _parse_json(text: str) -> Iterator[NormalizedEvent]:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        yield from _parse_text(text)
        return
    if isinstance(data, list):
        for item in data:
            yield from _parse_jsonl(json.dumps(item))
    else:
        yield from _parse_jsonl(json.dumps(data))


def _parse_syslog(text: str) -> Iterator[NormalizedEvent]:
    for line in text.splitlines():
        m = _SYSLOG_RE.match(line)
        if not m:
            if line.strip():
                yield NormalizedEvent(raw=line, timestamp=None, source=None, fields={})
            continue
        d = m.groupdict()
        yield NormalizedEvent(
            raw=line,
            timestamp=_coerce_ts(d["ts"]),
            source=d.get("host"),
            fields={k: v for k, v in d.items() if v is not None},
        )


def _parse_apache(text: str) -> Iterator[NormalizedEvent]:
    for line in text.splitlines():
        m = _APACHE_RE.match(line)
        if not m:
            if line.strip():
                yield NormalizedEvent(raw=line, timestamp=None, source=None, fields={})
            continue
        d = m.groupdict()
        yield NormalizedEvent(
            raw=line,
            timestamp=_coerce_ts(d["ts"]),
            source=d.get("ip"),
            fields={k: v for k, v in d.items() if v is not None},
        )


def _parse_csv(text: str) -> Iterator[NormalizedEvent]:
    import csv
    import io

    reader = csv.DictReader(io.StringIO(text))
    for row in reader:
        ts = _coerce_ts(row.get("timestamp") or row.get("time") or row.get("@timestamp"))
        src = row.get("host") or row.get("source")
        yield NormalizedEvent(
            raw=",".join(f"{k}={v}" for k, v in row.items()),
            timestamp=ts,
            source=src,
            fields={k: (v or "") for k, v in row.items()},
        )


def _parse_text(text: str) -> Iterator[NormalizedEvent]:
    for line in text.splitlines():
        if line.strip():
            yield NormalizedEvent(raw=line, timestamp=None, source=None, fields={})


_PARSERS = {
    "jsonl": _parse_jsonl,
    "json": _parse_json,
    "syslog": _parse_syslog,
    "apache": _parse_apache,
    "csv": _parse_csv,
    "text": _parse_text,
}


def _flatten(obj: dict, prefix: str = "") -> dict:
    out: dict = {}
    for k, v in obj.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(_flatten(v, prefix=f"{key}."))
        else:
            out[key] = v
    return out


def _coerce_ts(value) -> str | None:
    if value is None:
        return None
    try:
        return date_parser.parse(str(value)).isoformat()
    except (ValueError, OverflowError, date_parser.ParserError):
        return None
