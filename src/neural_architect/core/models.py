"""Typed data models shared across the pipeline.

These mirror the JSON schema the Gemini model is instructed to return,
and the schemas FastAPI/Streamlit consume. Single source of truth.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class KillChainPhase(str, Enum):
    """Lockheed-Martin / MITRE-style kill chain phases."""
    RECONNAISSANCE = "reconnaissance"
    RESOURCE_DEVELOPMENT = "resource_development"
    INITIAL_ACCESS = "initial_access"
    EXECUTION = "execution"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DEFENSE_EVASION = "defense_evasion"
    CREDENTIAL_ACCESS = "credential_access"
    DISCOVERY = "discovery"
    LATERAL_MOVEMENT = "lateral_movement"
    COLLECTION = "collection"
    COMMAND_AND_CONTROL = "command_and_control"
    EXFILTRATION = "exfiltration"
    IMPACT = "impact"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IndicatorType(str, Enum):
    IPV4 = "ipv4"
    DOMAIN = "domain"
    URL = "url"
    MD5 = "md5"
    SHA1 = "sha1"
    SHA256 = "sha256"
    FILE_PATH = "file_path"
    REGISTRY_KEY = "registry_key"
    EMAIL = "email"
    CVE = "cve"
    USER = "user"
    PROCESS = "process"


class Indicator(BaseModel):
    type: IndicatorType
    value: str
    first_seen: Optional[datetime] = None
    context: Optional[str] = Field(None, description="Where/how this IOC appeared")


class MitreTechnique(BaseModel):
    """A MITRE ATT&CK (sub-)technique reference."""
    technique_id: str = Field(..., description="e.g. T1566 or T1566.001")
    name: str
    tactic: KillChainPhase
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = Field(..., description="Why this technique was inferred")


class AttackEvent(BaseModel):
    """A single reconstructed step in the attack chain."""
    timestamp: Optional[datetime] = None
    phase: KillChainPhase
    actor: Optional[str] = Field(None, description="user/process/host responsible")
    target: Optional[str] = Field(None, description="affected entity")
    description: str
    techniques: list[MitreTechnique] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list, description="raw log lines or artifacts")
    severity: Severity = Severity.MEDIUM


class AttackChain(BaseModel):
    """The full reconstructed incident."""
    incident_id: str
    summary: str = Field(..., description="One-paragraph executive summary")
    severity: Severity
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    events: list[AttackEvent] = Field(default_factory=list)
    indicators: list[Indicator] = Field(default_factory=list)
    suspected_actor: Optional[str] = Field(
        None, description="Threat group attribution if reasonably inferable, else null"
    )
    recommended_actions: list[str] = Field(default_factory=list)
    model_notes: Optional[str] = Field(
        None, description="Caveats from the model: gaps, ambiguity, confidence"
    )

    @property
    def technique_ids(self) -> list[str]:
        ids = {t.technique_id for e in self.events for t in e.techniques}
        return sorted(ids)
