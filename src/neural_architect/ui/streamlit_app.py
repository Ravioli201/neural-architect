import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))
"""Streamlit UI for Neural Architect.

A polished demo surface for the analyzer:
- file upload OR sample dataset OR paste-in
- live-streaming "thinking" status
- timeline view, MITRE heatmap, IOC table
- one-click STIX / Markdown export
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from neural_architect import __version__
from neural_architect.core.analyzer import Analyzer
from neural_architect.core.models import AttackChain, KillChainPhase, Severity
from neural_architect.exporters import to_markdown_report, to_stix_bundle
from neural_architect.llm.gemini_client import GeminiClient, GeminiUnavailableError

load_dotenv()

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "data" / "samples"

SEVERITY_COLOR = {
    Severity.LOW: "#3b82f6",
    Severity.MEDIUM: "#f59e0b",
    Severity.HIGH: "#ef4444",
    Severity.CRITICAL: "#7c3aed",
}

st.set_page_config(
    page_title="Neural Architect — AI DFIR",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ----------------------------- styles ---------------------------------------

st.markdown(
    """
    <style>
      .na-hero {
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #312e81 100%);
          padding: 2rem 2rem 1.5rem 2rem;
          border-radius: 16px;
          color: #e2e8f0;
          margin-bottom: 1rem;
      }
      .na-hero h1 { color: #f1f5f9; margin: 0; font-size: 2.2rem; }
      .na-hero p  { color: #94a3b8; margin: .5rem 0 0 0; font-size: 1.05rem; }
      .na-pill {
          display:inline-block; padding: 2px 10px; border-radius: 999px;
          background:#1e293b; color:#cbd5e1; font-size:.78rem; margin-right:6px;
      }
      .na-event {
          border-left: 3px solid #6366f1;
          padding: .6rem .9rem;
          margin: .5rem 0;
          background: rgba(99,102,241,0.06);
          border-radius: 6px;
      }
      .na-tech {
          font-family: ui-monospace, SFMono-Regular, monospace;
          font-size: .85rem; color: #6366f1;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


# ----------------------------- sidebar --------------------------------------

with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    api_key = st.text_input(
        "Gemini API key",
        value=os.environ.get("GEMINI_API_KEY", ""),
        type="password",
        help="Get one at https://aistudio.google.com/apikey",
    )
    model = st.selectbox(
        "Model",
        options=["gemini-2.5-flash", "gemini-2.5-pro"],
        index=0,
        help="Flash is fast and cheap; Pro is slower but reasons more deeply.",
    )
    st.markdown("---")
    st.markdown("### 📚 Sample data")
    st.caption("No logs handy? Try one of these.")
    samples = sorted(SAMPLES_DIR.glob("*.log")) if SAMPLES_DIR.exists() else []
    sample_choice = st.selectbox(
        "Load sample",
        options=["—"] + [s.name for s in samples],
    )
    st.markdown("---")
    st.caption(f"Neural Architect v{__version__}")
    st.caption("[GitHub](https://github.com/Ravioli201/neural-architect)")


# ----------------------------- hero -----------------------------------------

st.markdown(
    """
    <div class="na-hero">
      <h1>🧠 Neural Architect</h1>
      <p>AI-powered digital forensics. Drop in raw logs — get back a reconstructed
         attack chain mapped to MITRE ATT&amp;CK in seconds.</p>
      <div style="margin-top: .8rem;">
        <span class="na-pill">Gemini 2.5 Flash</span>
        <span class="na-pill">MITRE ATT&CK v15</span>
        <span class="na-pill">STIX 2.1 export</span>
        <span class="na-pill">Open source</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ----------------------------- input ----------------------------------------

st.subheader("1. Submit telemetry")
input_tabs = st.tabs(["📋 Paste", "📁 Upload"])

raw_logs = ""
with input_tabs[0]:
    default = ""
    if sample_choice and sample_choice != "—":
        default = (SAMPLES_DIR / sample_choice).read_text()
    raw_logs = st.text_area(
        "Logs",
        value=default,
        height=240,
        placeholder="Paste syslog, JSONL, Sysmon, Apache, or any plain text logs...",
        label_visibility="collapsed",
    )

with input_tabs[1]:
    up = st.file_uploader(
        "Upload a log file",
        type=["log", "txt", "json", "jsonl", "csv"],
        accept_multiple_files=False,
    )
    if up is not None:
        raw_logs = up.read().decode("utf-8", errors="replace")
        st.success(f"Loaded {up.name} ({len(raw_logs):,} chars)")

go_button = st.button(
    "🔍 Reconstruct Attack Chain",
    type="primary",
    use_container_width=True,
    disabled=not raw_logs.strip(),
)


# ----------------------------- run ------------------------------------------

if go_button:
    if not api_key:
        st.error("Please provide a Gemini API key in the sidebar.")
        st.stop()

    try:
        client = GeminiClient(api_key=api_key, model=model)
        analyzer = Analyzer(client=client)
    except GeminiUnavailableError as e:
        st.error(f"Could not initialize Gemini: {e}")
        st.stop()

    with st.status("Analyzing telemetry…", expanded=True) as status:
        st.write("• Detecting log format…")
        st.write("• Extracting indicators of compromise…")
        st.write("• Asking Gemini to reconstruct the attack chain…")
        try:
            chain = analyzer.analyze(raw_logs)
            status.update(label="✅ Reconstruction complete", state="complete")
        except Exception as e:  # noqa: BLE001 — surface any error to the user
            status.update(label="❌ Failed", state="error")
            st.exception(e)
            st.stop()

    st.session_state["chain"] = chain


# ----------------------------- render ---------------------------------------

chain: AttackChain | None = st.session_state.get("chain")
if chain is None:
    st.info("👆 Paste logs or load a sample to get started.")
    st.stop()


st.subheader("2. Reconstructed incident")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Incident", chain.incident_id)
c2.metric("Severity", chain.severity.value.upper())
c3.metric("Events", len(chain.events))
c4.metric("MITRE techniques", len(chain.technique_ids))

st.markdown(f"**Summary.** {chain.summary}")
if chain.suspected_actor:
    st.warning(f"⚠️ Suspected actor: **{chain.suspected_actor}**")


# ---- timeline
st.markdown("### Attack timeline")
for i, ev in enumerate(chain.events, start=1):
    color = SEVERITY_COLOR.get(ev.severity, "#6366f1")
    techs = " ".join(
        f'<span class="na-tech">{t.technique_id}</span>' for t in ev.techniques
    ) or "<span class='na-tech'>—</span>"
    ts = ev.timestamp.isoformat() if ev.timestamp else "unknown time"
    st.markdown(
        f"""
        <div class="na-event" style="border-left-color:{color};">
          <strong>#{i} · {ev.phase.value.replace('_', ' ').title()}</strong>
          &nbsp;<span style="color:#64748b;">{ts}</span><br/>
          {ev.description}<br/>
          {techs}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if ev.evidence:
        with st.expander("Evidence"):
            st.code("\n".join(ev.evidence[:10]))


# ---- MITRE heatmap (one bar per tactic)
st.markdown("### MITRE ATT&CK coverage")
tactic_counts: dict[str, int] = {}
for ev in chain.events:
    for t in ev.techniques:
        tactic_counts[t.tactic.value] = tactic_counts.get(t.tactic.value, 0) + 1

if tactic_counts:
    ordered = [p.value for p in KillChainPhase if p.value in tactic_counts]
    fig = go.Figure(
        go.Bar(
            x=ordered,
            y=[tactic_counts[t] for t in ordered],
            marker_color="#6366f1",
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=20, b=80),
        xaxis_tickangle=-30,
        yaxis_title="techniques observed",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.caption("No MITRE techniques mapped.")


# ---- IOCs
st.markdown("### Indicators of compromise")
if chain.indicators:
    rows = [{"type": i.type.value, "value": i.value, "context": i.context or ""} for i in chain.indicators]
    st.dataframe(rows, use_container_width=True, hide_index=True)
else:
    st.caption("No IOCs found.")


# ---- recommended actions
if chain.recommended_actions:
    st.markdown("### Recommended actions")
    for a in chain.recommended_actions:
        st.markdown(f"- {a}")


# ---- exports
st.markdown("### 3. Export")
e1, e2, e3 = st.columns(3)
with e1:
    st.download_button(
        "📄 Markdown report",
        data=to_markdown_report(chain),
        file_name=f"{chain.incident_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )
with e2:
    st.download_button(
        "🛡️ STIX 2.1 bundle",
        data=str(to_stix_bundle(chain).serialize(pretty=True)),
        file_name=f"{chain.incident_id}.stix.json",
        mime="application/json",
        use_container_width=True,
    )
with e3:
    st.download_button(
        "📦 Raw JSON",
        data=json.dumps(chain.model_dump(mode="json"), indent=2, default=str),
        file_name=f"{chain.incident_id}.json",
        mime="application/json",
        use_container_width=True,
    )

if chain.model_notes:
    st.caption(f"📝 Model notes: {chain.model_notes}")
