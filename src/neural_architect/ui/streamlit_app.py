"""Streamlit UI for Neural Architect — minimal monochrome theme with light/dark toggle."""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "src"))

import json
import os
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from neural_architect import __version__
from neural_architect.core.analyzer import Analyzer
from neural_architect.core.models import AttackChain, Severity
from neural_architect.exporters import to_markdown_report, to_stix_bundle
from neural_architect.llm.gemini_client import GeminiClient
from neural_architect.ui.visualizer import render_3d_attack_graph
from neural_architect.ui.chatbot import SOCChatbot

load_dotenv()
ROOT = Path(__file__).resolve().parents[3]
SAMPLES_DIR = ROOT / "data" / "samples"
LOGO_PATH = ROOT / "assets" / "logo.svg"

st.set_page_config(
    page_title="Neural Architect",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Theme state -----------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

THEMES = {
    "dark": {
        "bg":        "#0a0a0a",
        "surface":   "#141414",
        "surface_2": "#1c1c1c",
        "border":    "#262626",
        "border_2":  "#333333",
        "text":      "#fafafa",
        "text_dim":  "#a3a3a3",
        "text_mute": "#737373",
        "accent":    "#22d3ee",
    },
    "light": {
        "bg":        "#ffffff",
        "surface":   "#fafafa",
        "surface_2": "#f4f4f4",
        "border":    "#e5e5e5",
        "border_2":  "#d4d4d4",
        "text":      "#0a0a0a",
        "text_dim":  "#525252",
        "text_mute": "#737373",
        "accent":    "#0891b2",
    },
}
T = THEMES[st.session_state["theme"]]

SEVERITY_COLOR = {
    Severity.LOW: T["text_dim"],
    Severity.MEDIUM: "#a3a3a3",
    Severity.HIGH: T["text"],
    Severity.CRITICAL: T["accent"],
}

LOGO_SVG = LOGO_PATH.read_text() if LOGO_PATH.exists() else ""

# --- Global CSS ------------------------------------------------------------
st.markdown(f"""
<style>
  .stApp {{ background: {T["bg"]}; color: {T["text"]}; }}
  [data-testid="stSidebar"] {{ background: {T["surface"]}; border-right: 1px solid {T["border"]}; }}
  [data-testid="stSidebar"] * {{ color: {T["text"]} !important; }}
  h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: {T["text"]}; }}
  .stMarkdown, .stMarkdown p {{ color: {T["text"]}; }}

  .na-hero {{
      display: flex; align-items: center; gap: 1.25rem;
      padding: 1.5rem 1.75rem; margin-bottom: 1.5rem;
      background: {T["surface"]}; border: 1px solid {T["border"]};
      border-radius: 12px;
  }}
  .na-hero-logo {{ width: 56px; height: 56px; color: {T["accent"]}; flex-shrink: 0; }}
  .na-hero-title {{ font-size: 1.65rem; font-weight: 600; color: {T["text"]}; margin: 0; line-height: 1.2; }}
  .na-hero-sub {{ font-size: 0.95rem; color: {T["text_dim"]}; margin: 0.25rem 0 0 0; }}

  .na-pill {{
      display: inline-block; padding: 3px 10px; border-radius: 999px;
      background: transparent; border: 1px solid {T["border_2"]};
      color: {T["text_dim"]}; font-size: 0.75rem; margin-right: 6px;
  }}

  .na-event {{
      border: 1px solid {T["border"]}; border-left: 3px solid {T["accent"]};
      padding: 0.75rem 1rem; margin: 0.5rem 0;
      background: {T["surface"]}; border-radius: 6px;
  }}
  .na-tech {{
      font-family: ui-monospace, SFMono-Regular, monospace;
      font-size: 0.8rem; color: {T["accent"]};
      background: {T["surface_2"]}; padding: 1px 6px; border-radius: 3px;
      margin-right: 4px;
  }}

  /* Tab-styled radio */
  div[role="radiogroup"] {{
      gap: 0 !important;
      border-bottom: 1px solid {T["border"]};
      padding: 0; margin-bottom: 1.25rem;
  }}
  div[role="radiogroup"] > label {{
      background: transparent !important;
      border: none !important;
      border-bottom: 2px solid transparent !important;
      border-radius: 0 !important;
      padding: 0.55rem 1rem !important;
      margin: 0 !important;
      color: {T["text_dim"]} !important;
      font-weight: 400 !important;
      transition: color 0.15s, border-color 0.15s;
      cursor: pointer;
  }}
  div[role="radiogroup"] > label:hover {{
      color: {T["text"]} !important;
  }}
  div[role="radiogroup"] > label[data-checked="true"],
  div[role="radiogroup"] > label:has(input:checked) {{
      color: {T["text"]} !important;
      border-bottom-color: {T["accent"]} !important;
      font-weight: 500 !important;
  }}
  div[role="radiogroup"] > label > div:first-child {{ display: none !important; }}

  /* Buttons */
  .stButton > button {{
      background: {T["text"]}; color: {T["bg"]};
      border: 1px solid {T["text"]}; border-radius: 8px;
      font-weight: 500; padding: 0.5rem 1rem;
      transition: opacity 0.15s;
  }}
  .stButton > button:hover {{ opacity: 0.85; background: {T["text"]}; color: {T["bg"]}; }}
  .stButton > button:disabled {{ opacity: 0.4; }}

  /* Inputs */
  .stTextInput > div > div > input,
  .stTextArea textarea,
  .stSelectbox > div > div {{
      background: {T["surface"]} !important;
      color: {T["text"]} !important;
      border: 1px solid {T["border"]} !important;
      border-radius: 6px !important;
  }}

  /* Metrics */
  [data-testid="stMetric"] {{
      background: {T["surface"]}; border: 1px solid {T["border"]};
      border-radius: 8px; padding: 0.85rem 1rem;
  }}
  [data-testid="stMetricLabel"] {{ color: {T["text_dim"]} !important; font-size: 0.78rem !important; }}
  [data-testid="stMetricValue"] {{ color: {T["text"]} !important; font-weight: 500 !important; }}

  /* Status box */
  [data-testid="stStatusWidget"] {{ background: {T["surface"]}; border: 1px solid {T["border"]}; border-radius: 8px; }}

  /* File uploader */
  [data-testid="stFileUploader"] section {{
      background: {T["surface"]}; border: 1px dashed {T["border_2"]}; border-radius: 8px;
  }}

  /* Empty-state callout */
  .na-empty {{
      text-align: center; padding: 3rem 2rem; margin-top: 2rem;
      border: 1px dashed {T["border_2"]}; border-radius: 12px;
      color: {T["text_dim"]};
  }}
  .na-empty-icon {{ width: 48px; height: 48px; margin: 0 auto 0.75rem auto; color: {T["text_mute"]}; }}

  /* Chat */
  [data-testid="stChatMessage"] {{ background: {T["surface"]}; border: 1px solid {T["border"]}; border-radius: 8px; }}

  /* Hide streamlit chrome */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 2rem; padding-bottom: 4rem; }}
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---------------------------------------------------------------
with st.sidebar:
    # Theme toggle
    st.markdown("##### Appearance")
    theme_label = st.radio(
        "theme_radio",
        options=["Dark", "Light"],
        index=0 if st.session_state["theme"] == "dark" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="theme_radio",
    )
    new_theme = "dark" if theme_label == "Dark" else "light"
    if new_theme != st.session_state["theme"]:
        st.session_state["theme"] = new_theme
        st.rerun()

    st.markdown("---")
    st.markdown("##### Configuration")

    _secret_key = ""
    try:
        _secret_key = st.secrets.get("GEMINI_API_KEY", "") or st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        pass
    api_key = (
        _secret_key
        or os.environ.get("GEMINI_API_KEY", "")
        or st.text_input("Gemini API key", type="password", label_visibility="collapsed", placeholder="Gemini API key")
    )
    model_choice = st.selectbox("Model", options=["gemini-2.5-flash", "gemini-2.5-pro"], index=0)

    if api_key:
        st.markdown(f'<div style="color:{T["accent"]}; font-size:0.85rem;">● API key configured</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="color:{T["text_mute"]}; font-size:0.85rem;">○ Key required</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("##### Sample data")
    samples = sorted(SAMPLES_DIR.glob("*.log")) if SAMPLES_DIR.exists() else []
    sample_choice = st.selectbox("Load sample", options=["—"] + [s.name for s in samples], label_visibility="collapsed")

    st.markdown("<div style='flex-grow:1; min-height:2rem'></div>", unsafe_allow_html=True)
    st.markdown(
        f'<div style="color:{T["text_mute"]}; font-size:0.75rem;">'
        f'Neural Architect v{__version__}<br>'
        f'<a href="https://github.com/Ravioli201/neural-architect" style="color:{T["text_mute"]};">GitHub →</a>'
        f'</div>',
        unsafe_allow_html=True,
    )

# --- Hero ------------------------------------------------------------------
st.markdown(f"""
<div class="na-hero">
  <div class="na-hero-logo">{LOGO_SVG}</div>
  <div>
    <div class="na-hero-title">Neural Architect</div>
    <div class="na-hero-sub">AI-powered digital forensics. Reconstruct attack chains from raw logs.</div>
    <div style="margin-top: 0.6rem;">
      <span class="na-pill">Gemini 2.5</span>
      <span class="na-pill">MITRE ATT&CK</span>
      <span class="na-pill">STIX 2.1</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# --- Input -----------------------------------------------------------------
st.markdown("##### 1 · Submit telemetry")
input_tabs = st.tabs(["Paste", "Upload"])

raw_logs = ""
with input_tabs[0]:
    default_val = ""
    if sample_choice != "—":
        default_val = (SAMPLES_DIR / sample_choice).read_text()
    raw_logs = st.text_area("logs", value=default_val, height=180, placeholder="Paste raw logs here...", label_visibility="collapsed")

with input_tabs[1]:
    ups = st.file_uploader("Upload log files", type=["log", "txt", "json", "jsonl", "csv"], accept_multiple_files=True, label_visibility="collapsed")
    if ups:
        chunks = []
        for f in ups:
            content = f.read().decode("utf-8", errors="replace")
            chunks.append(f"##### FILE: {f.name} #####\n{content}")
        raw_logs = "\n\n".join(chunks)
        st.caption(f"Loaded {len(ups)} file(s)")

go_button = st.button("Reconstruct attack chain", type="primary", use_container_width=True, disabled=not raw_logs.strip())

# --- Execution -------------------------------------------------------------
if go_button:
    if not api_key:
        st.error("Provide a Gemini API key in the sidebar.")
        st.stop()

    with st.status("Analyzing incident...", expanded=True) as status:
        try:
            client = GeminiClient(api_key=api_key, model=model_choice)
            analyzer = Analyzer(client=client)
            chain = analyzer.analyze(raw_logs)

            bot = SOCChatbot(api_key=api_key)
            st.session_state["chat_session"] = bot.start_session(str(chain))
            st.session_state["chain"] = chain
            st.session_state["messages"] = []

            status.update(label="Analysis complete", state="complete")
        except Exception as e:
            status.update(label="Analysis failed", state="error")
            st.exception(e)
            st.stop()

# --- Results ---------------------------------------------------------------
chain: AttackChain | None = st.session_state.get("chain")
if chain:
    st.markdown("##### 2 · Reconstructed incident")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Incident ID", chain.incident_id)
    m2.metric("Severity", chain.severity.value.upper())
    m3.metric("Events", len(chain.events))
    m4.metric("Techniques", len(chain.technique_ids))

    _view_options = ["3D attack path", "Timeline", "Ask the analyst", "MITRE heatmap", "Exports"]
    if "active_view" not in st.session_state:
        st.session_state["active_view"] = _view_options[0]
    active_view = st.radio(
        "view",
        options=_view_options,
        horizontal=True,
        label_visibility="collapsed",
        key="active_view",
    )

    if active_view == _view_options[0]:
        fig = render_3d_attack_graph(chain.events)
        if fig:
            fig.update_layout(template="plotly_dark" if st.session_state["theme"] == "dark" else "plotly_white",
                              paper_bgcolor=T["surface"], plot_bgcolor=T["surface"])
            st.plotly_chart(fig, use_container_width=True)

    elif active_view == _view_options[1]:
        for i, ev in enumerate(chain.events, start=1):
            color = SEVERITY_COLOR.get(ev.severity, T["accent"])
            techs = " ".join(f'<span class="na-tech">{t.technique_id}</span>' for t in ev.techniques)
            st.markdown(f"""
                <div class="na-event" style="border-left-color:{color};">
                    <div style="font-weight:500; color:{T['text']};">#{i} · {ev.phase.value.replace('_', ' ').title()}</div>
                    <div style="color:{T['text_dim']}; margin:0.35rem 0;">{ev.description}</div>
                    <div>{techs}</div>
                </div>
            """, unsafe_allow_html=True)

    elif active_view == _view_options[2]:
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

    elif active_view == _view_options[3]:
        tactic_counts = {}
        for ev in chain.events:
            for t in ev.techniques:
                tactic_counts[t.tactic.value] = tactic_counts.get(t.tactic.value, 0) + 1

        if tactic_counts:
            fig = go.Figure(go.Bar(
                x=list(tactic_counts.keys()),
                y=list(tactic_counts.values()),
                marker_color=T["accent"],
            ))
            fig.update_layout(
                height=350,
                template="plotly_dark" if st.session_state["theme"] == "dark" else "plotly_white",
                paper_bgcolor=T["surface"], plot_bgcolor=T["surface"],
                margin=dict(l=0, r=0, t=20, b=50),
            )
            st.plotly_chart(fig, use_container_width=True)

    elif active_view == _view_options[4]:
        e1, e2, e3 = st.columns(3)
        e1.download_button("Markdown report", data=to_markdown_report(chain), file_name=f"{chain.incident_id}.md", use_container_width=True)
        e2.download_button("STIX 2.1 bundle", data=str(to_stix_bundle(chain).serialize()), file_name=f"{chain.incident_id}.stix.json", use_container_width=True)
        e3.download_button("Raw JSON", data=json.dumps(chain.model_dump(mode="json"), indent=2), file_name=f"{chain.incident_id}.json", use_container_width=True)

else:
    st.markdown(f"""
    <div class="na-empty">
      <div style="font-size:1rem; color:{T['text_dim']};">Submit logs above to reconstruct an attack chain.</div>
      <div style="font-size:0.85rem; margin-top:0.5rem;">Try a sample dataset from the sidebar to see what the output looks like.</div>
    </div>
    """, unsafe_allow_html=True)