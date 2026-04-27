"""FastAPI service.

Exposes Neural Architect as a microservice with three endpoints:

- POST /analyze    — submit raw logs, get back an AttackChain
- POST /export/stix — analyze and return STIX 2.1 bundle
- POST /export/markdown — analyze and return a markdown IR report
- GET  /health     — liveness probe
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

from neural_architect import __version__
from neural_architect.core.analyzer import Analyzer
from neural_architect.core.models import AttackChain
from neural_architect.exporters import to_markdown_report, to_stix_bundle
from neural_architect.llm.gemini_client import GeminiClient, GeminiUnavailableError

log = logging.getLogger(__name__)

MAX_BYTES = int(os.environ.get("NA_MAX_LOG_BYTES", 2_000_000))


class AnalyzeRequest(BaseModel):
    logs: str = Field(..., description="Raw log content. Plain text, JSONL, syslog, etc.")
    incident_id: str | None = Field(None, description="Optional client-supplied ID")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Eagerly construct the client so misconfig fails fast at startup, not on first request.
    try:
        app.state.analyzer = Analyzer(client=GeminiClient())
        log.info("Analyzer initialized with model: %s", app.state.analyzer._client.model)
    except GeminiUnavailableError as e:
        log.error("Failed to initialize Gemini client: %s", e)
        app.state.analyzer = None
    yield


app = FastAPI(
    title="Neural Architect",
    description="AI-powered digital forensics. Reconstruct attack chains and map to MITRE ATT&CK.",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict:
    ready = app.state.analyzer is not None
    return {
        "status": "ok" if ready else "degraded",
        "version": __version__,
        "gemini_configured": ready,
    }


@app.post("/analyze", response_model=AttackChain)
async def analyze(req: AnalyzeRequest) -> AttackChain:
    _validate_payload(req)
    return _run(req)


@app.post("/export/stix")
async def export_stix(req: AnalyzeRequest) -> JSONResponse:
    _validate_payload(req)
    chain = _run(req)
    bundle = to_stix_bundle(chain)
    return JSONResponse(content=bundle.serialize(as_dict=True))


@app.post("/export/markdown", response_class=PlainTextResponse)
async def export_markdown(req: AnalyzeRequest) -> str:
    _validate_payload(req)
    chain = _run(req)
    return to_markdown_report(chain)


def _validate_payload(req: AnalyzeRequest) -> None:
    if app.state.analyzer is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Set GEMINI_API_KEY and restart.",
        )
    payload_bytes = len(req.logs.encode("utf-8"))
    if payload_bytes > MAX_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Payload {payload_bytes} bytes exceeds limit of {MAX_BYTES}.",
        )


def _run(req: AnalyzeRequest) -> AttackChain:
    try:
        return app.state.analyzer.analyze(req.logs, incident_id=req.incident_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except GeminiUnavailableError as e:
        raise HTTPException(status_code=502, detail=f"LLM upstream error: {e}")
