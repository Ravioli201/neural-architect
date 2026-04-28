"""STIX 2.1 bundle exporter.

Turns a reconstructed AttackChain into a STIX bundle that downstream SOC
tools (MISP, OpenCTI, TAXII servers) can consume. Uses the official `stix2`
library so we get spec-compliant SDOs and SROs, not hand-rolled JSON.
"""
from __future__ import annotations

from datetime import datetime, timezone

import stix2

from neural_architect.core.models import (
    AttackChain,
    IndicatorType,
)

# Map our IOC types to STIX pattern fragments.
_PATTERN_BUILDERS = {
    IndicatorType.IPV4: lambda v: f"[ipv4-addr:value = '{v}']",
    IndicatorType.DOMAIN: lambda v: f"[domain-name:value = '{v}']",
    IndicatorType.URL: lambda v: f"[url:value = '{v}']",
    IndicatorType.MD5: lambda v: f"[file:hashes.MD5 = '{v}']",
    IndicatorType.SHA1: lambda v: f"[file:hashes.'SHA-1' = '{v}']",
    IndicatorType.SHA256: lambda v: f"[file:hashes.'SHA-256' = '{v}']",
    IndicatorType.EMAIL: lambda v: f"[email-addr:value = '{v}']",
    IndicatorType.FILE_PATH: lambda v: f"[file:name = '{_escape(v)}']",
    IndicatorType.REGISTRY_KEY: lambda v: f"[windows-registry-key:key = '{_escape(v)}']",
}


def to_stix_bundle(chain: AttackChain) -> stix2.Bundle:
    """Convert an AttackChain into a STIX 2.1 Bundle."""
    identity = stix2.Identity(
        name="Neural Architect",
        identity_class="system",
        description="AI-assisted DFIR reconstruction",
    )

    objects: list = [identity]

    # Indicators (IOC SDOs)
    for ioc in chain.indicators:
        builder = _PATTERN_BUILDERS.get(ioc.type)
        if not builder:
            continue
        try:
            objects.append(
                stix2.Indicator(
                    name=f"{ioc.type.value}: {ioc.value}",
                    pattern=builder(ioc.value),
                    pattern_type="stix",
                    valid_from=ioc.first_seen or datetime.now(timezone.utc),
                    created_by_ref=identity.id,
                    description=ioc.context,
                )
            )
        except stix2.exceptions.STIXError:
            continue

    # Attack patterns (one per unique technique)
    seen_techniques: dict[str, stix2.AttackPattern] = {}
    for event in chain.events:
        for tech in event.techniques:
            if tech.technique_id in seen_techniques:
                continue
            ap = stix2.AttackPattern(
                name=tech.name,
                external_references=[
                    {
                        "source_name": "mitre-attack",
                        "external_id": tech.technique_id,
                        "url": _mitre_url(tech.technique_id),
                    }
                ],
                description=tech.rationale,
                created_by_ref=identity.id,
            )
            seen_techniques[tech.technique_id] = ap
            objects.append(ap)

    # Incident-level Report SDO that ties everything together
    if objects:
        report = stix2.Report(
            name=f"Incident {chain.incident_id}",
            published=chain.started_at or datetime.now(timezone.utc),
            report_types=["incident"],
            description=chain.summary,
            object_refs=[o.id for o in objects],
            created_by_ref=identity.id,
        )
        objects.append(report)

    return stix2.Bundle(objects=objects, allow_custom=True)


def _mitre_url(technique_id: str) -> str:
    base = "https://attack.mitre.org/techniques"
    if "." in technique_id:
        parent, sub = technique_id.split(".", 1)
        return f"{base}/{parent}/{sub}/"
    return f"{base}/{technique_id}/"


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")
