"""Streamlit UI for Neural Architect.
A polished demo surface for the analyzer:
- Multi-file upload or sample dataset
- 3D Attack Graph & MITRE Heatmap
- Interactive SOC Analyst Chatbot
- STIX / Markdown export
"""
from __future__ import annotations
import sys
from pathlib import Path

# Fix the path for Streamlit Cloud
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import json
import os
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from neural_architect import __version__
from neural_architect.core.analyzer import Analyzer
from neural_architect.core.models import AttackChain, KillChainPhase, Severity
from neural_architect.exporters import to_markdown_report, to_stix_bundle
from neural_architect.llm.gemini_client import GeminiClient, GeminiUnavailableError
from neural_architect.ui.visualizer import render_3d_attack_graph
from neural_architect.ui.chatbot import SOCChatbot

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

# ----------------------------- Styles ---------------------------------------
st.markdown(
    """
    <style>
      .na-hero {
          background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #312e81 100%);
          padding: 2rem 2rem 1.5rem 2rem;
          border-radius: 16px; color: #e2e8f0; margin-bottom: 1rem;
      }
      .na-hero h1 { color: #f1f5f9; margin: 0; font-size: 2.2rem; }
      .na-hero p  { color: #94a3b8; margin: .5rem 0 0 0; font-size: 1.05rem; }
      .na-pill {
          display:inline-block; padding: 2px 10px; border-radius: 999px;
          background:#1e293b; color:#cbd5e1; font-size:.78rem; margin-right:6px;
      }
      .na-event {
          border-left: 3px solid #6366f1; padding: .6rem .9rem; margin: .5rem 0;
          background: rgba(99,102,241,0.06); border-radius: 6px;
      }
      .na-tech {
          font-family: ui-monospace, SFMono-Regular, monospace;
          font-size: .85rem; color: #6366f1;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Sidebar --------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    
    # Auto-resolve API Key
    _secret_key = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("GOOGLE_API_KEY", "")
    api_key = _secret_key or st.text_input("Gemini API key", value=os.environ.get("GEMINI_API_KEY", ""), type="password")
    
    model_choice = st.selectbox("Model", options=["gemini-2.5-flash", "gemini-2.5-pro"], index=0)
    
    if api_key:
        st.success("✓ API Key Configured")
    else:
        st.warning("⚠️ Key Required")

    st.markdown("---")
    st.markdown("### 📚 Sample data")
    samples = sorted(SAMPLES_DIR.glob("*.log")) if SAMPLES_DIR.exists() else []
    sample_choice = st.selectbox("Load sample", options=["—"] + [s.name for s in samples])
    
    st.markdown("---")
    st.caption(f"Neural Architect v{__version__}")
    st.caption("[GitHub](https://github.com/Ravioli201/neural-architect)")

# ----------------------------- Hero -----------------------------------------
st.markdown(
    """
    <div class="na-hero">
      <h1>🧠 Neural Architect</h1>
      <p>AI-powered digital forensics. Drop in raw logs — get back a reconstructed attack chain in seconds.</p>
      <div style="margin-top: .8rem;">
        <span class="na-pill">3D Visualizer</span>
        <span class="na-pill">Analyst Chatbot</span>
        <span class="na-pill">MITRE ATT&CK v15</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------- Input ----------------------------------------
st.subheader("1. Submit telemetry")
input_tabs = st.tabs(["📋 Paste / Sample", "📁 Upload Multi-Logs"])

raw_logs = ""
with input_tabs[0]:
    default_val = ""
    if sample_choice != "—":
        default_val = (SAMPLES_DIR / sample_choice).read_text()
    raw_logs = st.text_area("Logs", value=default_val, height=200, placeholder="Paste logs here...", label_visibility="collapsed")

with input_tabs[1]:
    ups = st.file_uploader("Upload log files", type=["log", "txt", "json", "jsonl", "csv"], accept_multiple_files=True)
    if ups:
        chunks = []
        for f in ups:
            content = f.read().decode("utf-8", errors="replace")
            chunks.append(f"##### FILE: {f.name} #####\n{content}")
        raw_logs = "\n\n".join(chunks)
        st.success(f"Loaded {len(ups)} file(s)")

go_button = st.button("🔍 Reconstruct Attack Chain", type="primary", use_container_width=True, disabled=not raw_logs.strip())

# ----------------------------- Execution ------------------------------------
if go_button:
    if not api_key:
        st.error("Please provide a Gemini API key.")
        st.stop()

    with st.status("Analyzing Incident...", expanded=True) as status:
        try:
            client = GeminiClient(api_key=api_key, model=model_choice)
            analyzer = Analyzer(client=client)
            chain = analyzer.analyze(raw_logs)
            
            # Initialize the Chatbot session
            bot = SOCChatbot(api_key=api_key)
            st.session_state["chat_session"] = bot.start_session(str(chain))
            st.session_state["chain"] = chain
            st.session_state["messages"] = [] # Clear old chat
            
            status.update(label="✅ Analysis complete", state="complete")
        except Exception as e:
            status.update(label="❌ Analysis failed", state="error")
            st.exception(e)
            st.stop()

# ----------------------------- Results --------------------------------------
chain: AttackChain | None = st.session_state.get("chain")
if chain:
    st.subheader("2. Reconstructed Incident")
    
    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Incident ID", chain.incident_id)
    m2.metric("Severity", chain.severity.value.upper())
    m3.metric("Events Found", len(chain.events))
    m4.metric("MITRE Techniques", len(chain.technique_ids))

    # Tabs for the different views
    res_tabs = st.tabs(["🌐 3D Attack Path", "📑 Detailed Timeline", "💬 Ask the Analyst", "📊 MITRE Heatmap", "📦 Exports"])

    with res_tabs[0]:
        st.markdown("### Interactive 3D Attack Graph")
        fig = render_3d_attack_graph(chain.events)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

    with res_tabs[1]:
        st.markdown("### Attack Timeline")
        for i, ev in enumerate(chain.events, start=1):
            color = SEVERITY_COLOR.get(ev.severity, "#6366f1")
            techs = " ".join(f'<span class="na-tech">{t.technique_id}</span>' for t in ev.techniques)
            st.markdown(f"""
                <div class="na-event" style="border-left-color:{color};">
                    <strong>#{i} · {ev.phase.value.replace('_', ' ').title()}</strong><br/>
                    {ev.description}<br/>{techs}
                </div>
            """, unsafe_allow_html=True)

    with res_tabs[2]:
        st.markdown("### SOC Analyst Assistant")
        for m in st.session_state.get("messages", []):
            with st.chat_message(m["role"]):
                st.markdown(m["content"])
        
        if prompt := st.chat_input("Ask a follow-up about this incident..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            bot = SOCChatbot(api_key=api_key)
            response = bot.ask(st.session_state["chat_session"], prompt)
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)

    with res_tabs[3]:
        st.markdown("### MITRE ATT&CK Tactic Coverage")
        tactic_counts = {}
        for ev in chain.events:
            for t in ev.techniques:
                tactic_counts[t.tactic.value] = tactic_counts.get(t.tactic.value, 0) + 1
        
        if tactic_counts:
            fig = go.Figure(go.Bar(x=list(tactic_counts.keys()), y=list(tactic_counts.values()), marker_color="#6366f1"))
            fig.update_layout(height=350, template="plotly_dark", margin=dict(l=0, r=0, t=20, b=50))
            st.plotly_chart(fig, use_container_width=True)

    with res_tabs[4]:
        st.markdown("### Export Results")
        e1, e2, e3 = st.columns(3)
        e1.download_button("📄 Markdown Report", data=to_markdown_report(chain), file_name=f"{chain.incident_id}.md", use_container_width=True)
        e2.download_button("🛡️ STIX 2.1 Bundle", data=str(to_stix_bundle(chain).serialize()), file_name=f"{chain.incident_id}.stix.json", use_container_width=True)
        e3.download_button("📦 Raw JSON", data=json.dumps(chain.model_dump(mode="json"), indent=2), file_name=f"{chain.incident_id}.json", use_container_width=True)

else:
    st.info("👆 Submit logs to generate an analysis.")