"""Tests for the typed data models."""
from __future__ import annotations

import pytest

from neural_architect.core.models import (
    AttackChain,
    AttackEvent,
    KillChainPhase,
    MitreTechnique,
    Severity,
)


def _chain(events):
    return AttackChain(
        incident_id="INC-TEST",
        summary="test",
        severity=Severity.MEDIUM,
        events=events,
    )


def test_technique_ids_are_unique_and_sorted():
    chain = _chain([
        AttackEvent(
            phase=KillChainPhase.INITIAL_ACCESS,
            description="phish",
            techniques=[
                MitreTechnique(
                    technique_id="T1566.001",
                    name="Spearphishing Attachment",
                    tactic=KillChainPhase.INITIAL_ACCESS,
                    confidence=0.9,
                    rationale="x",
                ),
            ],
        ),
        AttackEvent(
            phase=KillChainPhase.EXECUTION,
            description="exec",
            techniques=[
                MitreTechnique(
                    technique_id="T1059.001",
                    name="PowerShell",
                    tactic=KillChainPhase.EXECUTION,
                    confidence=0.95,
                    rationale="y",
                ),
                MitreTechnique(
                    technique_id="T1566.001",  # duplicate across events
                    name="Spearphishing Attachment",
                    tactic=KillChainPhase.INITIAL_ACCESS,
                    confidence=0.9,
                    rationale="z",
                ),
            ],
        ),
    ])
    assert chain.technique_ids == ["T1059.001", "T1566.001"]


def test_confidence_must_be_between_zero_and_one():
    with pytest.raises(Exception):
        MitreTechnique(
            technique_id="T1059",
            name="x",
            tactic=KillChainPhase.EXECUTION,
            confidence=1.5,
            rationale="too high",
        )


def test_severity_enum_round_trips_through_json():
    chain = _chain([])
    j = chain.model_dump_json()
    assert '"severity":"medium"' in j

    revived = AttackChain.model_validate_json(j)
    assert revived.severity is Severity.MEDIUM
