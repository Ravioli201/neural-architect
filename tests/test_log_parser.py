"""Tests for log format detection and normalization."""
from __future__ import annotations

from neural_architect.core import log_parser

JSONL = """\
{"@timestamp":"2026-04-09T22:14:02Z","host":"FILE-SRV-03","action":"read"}
{"@timestamp":"2026-04-09T22:14:18Z","host":"FILE-SRV-03","action":"read"}
"""

SYSLOG = """\
Apr 12 14:04:08 web01 sshd[18821]: Accepted password for root from 194.5.249.99 port 51221 ssh2
Apr 12 14:04:09 web01 sshd[18821]: pam_unix(sshd:session): session opened for user root by (uid=0)
"""

APACHE = (
    '203.0.113.42 - - [12/Apr/2026:14:02:11 +0000] "GET / HTTP/1.1" 200 1842 "-" "Mozilla/5.0"\n'
    '203.0.113.42 - - [12/Apr/2026:14:02:14 +0000] "GET /robots.txt HTTP/1.1" 200 51 "-" "Mozilla/5.0"\n'
)


def test_detects_jsonl():
    assert log_parser.detect_format(JSONL) == "jsonl"


def test_detects_syslog():
    assert log_parser.detect_format(SYSLOG) == "syslog"


def test_detects_apache():
    assert log_parser.detect_format(APACHE) == "apache"


def test_detects_text_fallback():
    assert log_parser.detect_format("just some random words here\nand another line") == "text"


def test_detects_empty():
    assert log_parser.detect_format("") == "empty"


def test_normalize_jsonl_extracts_timestamp_and_host():
    events = log_parser.normalize(JSONL)
    assert len(events) == 2
    assert all(e.timestamp is not None for e in events)
    assert events[0].source == "FILE-SRV-03"


def test_normalize_syslog_extracts_host():
    events = log_parser.normalize(SYSLOG)
    assert len(events) == 2
    assert events[0].source == "web01"


def test_normalize_apache_extracts_ip_as_source():
    events = log_parser.normalize(APACHE)
    assert len(events) == 2
    assert events[0].source == "203.0.113.42"


def test_normalize_handles_garbage_lines():
    text = "this is not json or syslog\nbut should still produce events"
    events = log_parser.normalize(text)
    assert len(events) == 2
