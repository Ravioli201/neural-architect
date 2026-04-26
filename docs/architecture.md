# Architecture

![architecture diagram](../assets/architecture.svg)

## Why this shape?

The single biggest lesson from running LLMs against security data is that
**the model needs structured anchors to stay grounded**. If you hand a
language model 50 KB of raw syslog and ask "what happened?", you'll get
a plausible-sounding story that may or may not be true. The fix isn't a
bigger model — it's better preprocessing.

So Neural Architect splits the work in two:

### 1. Deterministic preprocessing
Things regex and parsers do reliably and cheaply:
- **Log format detection** (`core/log_parser.py`) — auto-detects JSONL,
  syslog, Apache combined, CSV, plain text. No LLM tokens spent on
  format guessing.
- **IOC extraction** (`core/ioc_extractor.py`) — pulls IPs, domains,
  hashes, CVEs, paths, registry keys with battle-tested patterns. Drops
  internal/loopback/multicast IPs by default.
- **Prompt construction** (`core/analyzer.py`) — builds a bounded
  context window with a normalized timeline preview, deterministic IOC
  list, and a capped raw excerpt. Always reproducible.

### 2. LLM reconstruction
The part where deterministic logic falls over: weaving timestamped
events into a *narrative*, mapping to MITRE techniques, deciding what's
suspicious.
- **Gemini 2.5 Flash** with structured output (Pydantic schema as
  `response_schema`).
- **Analyst-grade system prompt** that explicitly instructs the model
  to ground claims in evidence, prefer sub-techniques where supported,
  and stay conservative on attribution.
- **Retries with backoff** for transient API failures; schema errors
  fail fast (model returned bad JSON → log it, surface it, don't loop).

### 3. Outputs
Same `AttackChain` object, different surfaces:
- Streamlit UI for analyst-in-the-loop demos.
- FastAPI service so this can plug into existing SOC pipelines.
- STIX 2.1 export for MISP / OpenCTI / TAXII consumers.
- Markdown report for ticketing systems and email.

## Why Gemini 2.5 Flash?
- Large context (≥1M tokens) lets us feed sizable raw log excerpts.
- Native structured output via `response_schema` removes the JSON-parsing
  fragility most LLM apps suffer from.
- Pricing makes per-incident analysis viable at SOC scale.

## What's next
- **Streaming reconstruction** — incrementally update the timeline as
  the model emits events, so analysts don't wait for the full response.
- **Multi-shot analysis** — break very large incidents into chunks and
  reduce-merge the per-chunk chains.
- **Vector store of historical incidents** — RAG against past
  reconstructions to spot repeat actors or campaigns.
- **Triage scoring** — predict severity from a single event before the
  full reconstruction runs, for high-volume queue prioritization.
