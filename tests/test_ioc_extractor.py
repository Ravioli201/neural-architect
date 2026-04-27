"""Tests for the regex-based IOC extractor."""
from __future__ import annotations

from neural_architect.core import ioc_extractor
from neural_architect.core.models import IndicatorType


def _types(indicators) -> set:
    return {(i.type, i.value) for i in indicators}


def test_extracts_public_ipv4_but_not_private():
    text = "Outbound to 45.137.21.118 from internal host 10.0.0.5; loopback 127.0.0.1"
    out = ioc_extractor.extract(text)
    types = _types(out)
    assert (IndicatorType.IPV4, "45.137.21.118") in types
    assert (IndicatorType.IPV4, "10.0.0.5") not in types
    assert (IndicatorType.IPV4, "127.0.0.1") not in types


def test_extracts_private_ipv4_when_requested():
    out = ioc_extractor.extract("internal: 10.0.0.5", include_internal=True)
    assert any(i.value == "10.0.0.5" for i in out)


def test_extracts_sha256_and_classifies_correctly():
    h = "8a4b9c2e1d6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b"
    out = ioc_extractor.extract(f"hash={h}")
    assert any(i.type is IndicatorType.SHA256 and i.value == h for i in out)
    # Should not double-classify the same hex run as MD5/SHA1.
    assert not any(i.type in (IndicatorType.MD5, IndicatorType.SHA1) and i.value == h for i in out)


def test_extracts_cve_case_insensitive():
    out = ioc_extractor.extract("affected by cve-2024-12345 in handler")
    assert any(i.type is IndicatorType.CVE for i in out)


def test_extracts_url_and_domain():
    out = ioc_extractor.extract("download from https://malicious.example.com/payload")
    assert any(i.type is IndicatorType.URL for i in out)
    assert any(i.type is IndicatorType.DOMAIN for i in out)


def test_dedupes_repeated_iocs():
    text = "45.137.21.118 again 45.137.21.118 still 45.137.21.118"
    out = ioc_extractor.extract(text)
    ip_count = sum(1 for i in out if i.type is IndicatorType.IPV4)
    assert ip_count == 1


def test_extracts_registry_key():
    out = ioc_extractor.extract("HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\Updater")
    assert any(i.type is IndicatorType.REGISTRY_KEY for i in out)


def test_empty_input_returns_empty():
    assert ioc_extractor.extract("") == []
    assert ioc_extractor.extract("   \n\n  ") == []
