import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import os
import pandas as pd
import plotly.express as px
import json
import re
from fpdf import FPDF
from dotenv import load_dotenv

# ============================================================
# CONFIG
# ============================================================
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

GEMINI_MODEL = "gemini-2.5-flash"

st.set_page_config(
    page_title="Neural Architect",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:         #000000;
    --surface:    #1c1c1e;
    --surface2:   #2c2c2e;
    --border:     rgba(255,255,255,0.1);
    --border-sub: rgba(255,255,255,0.06);
    --accent:     #0a84ff;
    --accent-hi:  #409cff;
    --text:       #ffffff;
    --text-2:     rgba(235,235,245,0.6);
    --text-3:     rgba(235,235,245,0.3);
    --success:    #30d158;
    --danger:     #ff453a;
}

/* ── Base ── */
.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, 'SF Pro Display', 'Inter', sans-serif;
}

/* Hide Streamlit's native sidebar completely */
section[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

/* Main content breathing room */
.main .block-container {
    padding-top: 3.25rem;
    padding-left: 4rem;
    padding-right: 4rem;
    max-width: 100% !important;
}

hr {
    border: none;
    border-top: 0.5px solid var(--border-sub);
    margin: 2.5rem 0;
}

/* ── Typography ── */
h1, h2, h3, h4 {
    font-family: -apple-system, 'SF Pro Display', 'Inter', sans-serif;
    letter-spacing: -0.03em;
}
h1 {
    font-size: 2.25rem;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: -0.045em;
    border-bottom: 0.5px solid var(--border-sub);
    padding-bottom: 1rem;
    margin-bottom: 0.25rem;
}
h2 {
    font-size: 1.0625rem;
    font-weight: 600;
    color: var(--text);
    margin-top: 0;
    margin-bottom: 1rem;
}
h3 { font-size: 0.9375rem; color: var(--text-2); font-weight: 400; }
p, li { color: var(--text-2); line-height: 1.7; }
label, span { color: var(--text-2); }
small, .stCaption { color: var(--text-3) !important; font-size: 0.8rem; }

/* ── Buttons ── */
.stButton > button {
    background: var(--accent);
    color: #ffffff;
    border: none;
    border-radius: 980px;
    font-family: -apple-system, 'SF Pro Text', 'Inter', sans-serif;
    font-weight: 600;
    font-size: 0.875rem;
    padding: 0.5625rem 1.375rem;
    height: auto;
    letter-spacing: -0.01em;
    transition: background 0.15s ease;
}
.stButton > button:hover {
    background: var(--accent-hi);
    color: #ffffff;
    transform: none;
    box-shadow: none;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] section {
    background: var(--surface);
    border: 0.5px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem;
    transition: background 0.15s;
}
[data-testid="stFileUploader"] section:hover { background: var(--surface2); }
[data-testid="stFileUploader"] label { color: var(--text-2); font-size: 0.875rem; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    border-bottom: 0.5px solid var(--border-sub);
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: var(--text-3);
    border: none;
    border-bottom: 1.5px solid transparent;
    border-radius: 0;
    font-family: -apple-system, 'Inter', sans-serif;
    font-weight: 400;
    font-size: 0.875rem;
    padding: 0.75rem 1.25rem;
    margin: 0;
    transition: color 0.15s;
}
.stTabs [aria-selected="true"] {
    color: var(--accent);
    border-bottom: 1.5px solid var(--accent);
}

/* ── Code ── */
code, pre, .stCode {
    font-family: 'SF Mono', 'JetBrains Mono', monospace !important;
    font-size: 0.8125rem !important;
}
[data-testid="stCodeBlock"] {
    background: var(--surface) !important;
    border: 0.5px solid var(--border) !important;
    border-radius: 12px !important;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea, .stSelectbox > div > div {
    background: var(--surface) !important;
    border: 0.5px solid var(--border) !important;
    color: var(--text) !important;
    border-radius: 10px !important;
    font-family: -apple-system, 'Inter', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(10,132,255,0.2) !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: var(--accent);
    box-shadow: none;
}

/* ── Alerts ── */
.stAlert {
    background: var(--surface) !important;
    border: 0.5px solid var(--border) !important;
    border-radius: 12px !important;
    color: var(--text-2) !important;
}

/* ── Insight cards ── */
.insight-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 0.75rem;
    margin-top: 0.75rem;
}
.insight-card {
    background: var(--surface);
    border: 0.5px solid rgba(10,132,255,0.2);
    border-left: 2px solid var(--accent);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    font-size: 0.8375rem;
    color: rgba(235,235,245,0.72);
    line-height: 1.55;
    font-family: -apple-system, 'Inter', sans-serif;
}
.insight-card::before {
    content: "INSIGHT";
    display: block;
    font-size: 0.625rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    color: var(--accent);
    margin-bottom: 0.375rem;
    opacity: 0.8;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--surface);
    border: 0.5px solid var(--border-sub);
    border-radius: 12px;
    padding: 0.875rem 1rem;
    margin-bottom: 0.5rem;
}

/* ── Right settings panel ── */
div:has(> #na-rpanel-anchor) {
    position: fixed;
    top: 0; right: 0;
    width: 0; height: 0;
    z-index: 998;
}
div:has(> #na-rpanel-anchor) + div[data-testid="stVerticalBlock"] {
    position: fixed;
    top: 0; right: 0;
    width: 288px;
    height: 100vh;
    background: rgba(28,28,30,0.97);
    border-left: 0.5px solid rgba(255,255,255,0.07);
    padding: 4.5rem 1.625rem 2rem;
    z-index: 999;
    overflow-y: auto;
    backdrop-filter: blur(48px);
    -webkit-backdrop-filter: blur(48px);
    box-shadow: -24px 0 64px rgba(0,0,0,0.45);
}

/* ── Panel toggle button — top right ── */
div:has(> #na-panel-btn-anchor) {
    position: fixed;
    top: 0; right: 0;
    width: 0; height: 0;
    z-index: 1001;
}
div:has(> #na-panel-btn-anchor) + div[data-testid="stVerticalBlock"] {
    position: fixed;
    top: 1rem; right: 1.25rem;
    width: auto;
    z-index: 1002;
}
div:has(> #na-panel-btn-anchor) + div[data-testid="stVerticalBlock"] .stButton > button {
    background: rgba(44,44,46,0.85);
    color: rgba(235,235,245,0.55);
    border: 0.5px solid rgba(255,255,255,0.1);
    border-radius: 10px;
    padding: 0.4375rem 0.875rem;
    font-size: 0.8125rem;
    font-weight: 500;
    letter-spacing: 0;
    backdrop-filter: blur(20px);
    box-shadow: none;
}
div:has(> #na-panel-btn-anchor) + div[data-testid="stVerticalBlock"] .stButton > button:hover {
    background: rgba(58,58,60,0.9);
    color: rgba(235,235,245,0.85);
    transform: none;
    box-shadow: none;
}

/* ── Floating chat — bottom LEFT (avoids right panel) ── */
div:has(> #na-chat-anchor) {
    position: fixed;
    bottom: 0; left: 0;
    width: 0; height: 0;
    z-index: 9999;
}
div:has(> #na-chat-anchor) + div[data-testid="stVerticalBlock"] {
    position: fixed;
    bottom: 24px; left: 24px;
    width: 380px;
    max-height: 70vh;
    background: rgba(28,28,30,0.88);
    border: 0.5px solid var(--border);
    border-radius: 16px;
    padding: 16px;
    z-index: 9999;
    overflow-y: auto;
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    box-shadow: 0 24px 64px rgba(0,0,0,0.7);
}
div:has(> #na-chat-toggle-anchor) + div[data-testid="stVerticalBlock"] {
    position: fixed;
    bottom: 24px; left: 24px;
    width: auto;
    z-index: 10000;
}
div:has(> #na-chat-toggle-anchor) + div[data-testid="stVerticalBlock"] .stButton > button {
    border-radius: 980px;
    padding: 0.5625rem 1.375rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# SESSION STATE
# ============================================================
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = ""
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "chat_open" not in st.session_state:
    st.session_state.chat_open = False
if "panel_open" not in st.session_state:
    st.session_state.panel_open = True

# ============================================================
# DERIVED STATE
# ============================================================
gemini_ok = bool(GOOGLE_API_KEY)
trust_score = st.session_state.get("conf_threshold", 85)

# Shift main content left when right panel is open
if st.session_state.panel_open:
    st.markdown(
        '<style>.main .block-container { padding-right: 312px !important; }</style>',
        unsafe_allow_html=True,
    )

# ============================================================
# HEADER
# ============================================================
st.title("Neural Architect")
st.markdown(
    '<p style="color:#86868b;font-size:0.9375rem;margin-top:-0.75rem;margin-bottom:2.5rem;'
    'font-family:-apple-system,Inter,sans-serif;letter-spacing:-0.01em;font-weight:400;">'
    'AI-powered forensic analysis &amp; threat intelligence</p>',
    unsafe_allow_html=True,
)

# ============================================================
# HELPERS
# ============================================================
def safe_decode(file) -> str:
    raw = file.read()
    for enc in ("utf-8", "utf-16", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def stream_gemini(prompt: str):
    if not gemini_ok:
        yield "Gemini API key not configured. Set GOOGLE_API_KEY in your .env file."
        return
    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"temperature": 0.35, "max_output_tokens": 8192},
        )
        resp = model.generate_content(prompt, stream=True)
        for chunk in resp:
            if chunk.text:
                yield chunk.text
    except Exception as e:
        yield f"\n\nError: {e}"


def chat_with_gemini(question: str, context: str) -> str:
    if not gemini_ok:
        return "Gemini API key not configured."
    try:
        model = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"temperature": 0.3, "max_output_tokens": 2048},
        )
        prompt = (
            "You are a security analyst assistant. Answer the user's question concisely "
            "using the forensic analysis context below. If the context does not contain "
            "the answer, say so plainly.\n\n"
            f"ANALYSIS CONTEXT:\n{context or '(no analysis run yet)'}\n\n"
            f"QUESTION: {question}"
        )
        resp = model.generate_content(prompt)
        return resp.text
    except Exception as e:
        return f"Error: {e}"


def truncate_text(content: str, max_chars: int = 80_000) -> str:
    if len(content) <= max_chars:
        return content
    half = max_chars // 2
    return content[:half] + f"\n\n[...{len(content) - max_chars:,} chars truncated...]\n\n" + content[-half:]


def extract_json_block(text: str):
    # Primary: look for explicit DATA_START / DATA_END markers
    m = re.search(r"DATA_START(.*?)DATA_END", text, re.DOTALL)
    raw = m.group(1).strip() if m else None

    # Fallback: find outermost JSON array in the full text
    if raw is None:
        start = text.find("[")
        if start != -1:
            depth, i = 0, start
            for i, ch in enumerate(text[start:], start):
                if ch == "[":
                    depth += 1
                elif ch == "]":
                    depth -= 1
                    if depth == 0:
                        raw = text[start : i + 1]
                        break

    if raw is None:
        return None

    # Strip JS-style line comments before parsing
    raw = re.sub(r"//[^\n]*", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def split_section(text: str, start: str, end: str = None) -> str:
    if start not in text:
        return ""
    chunk = text.split(start, 1)[1]
    if end and end in chunk:
        chunk = chunk.split(end, 1)[0]
    return chunk.strip()


def build_pdf(text: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    safe = text.encode("latin-1", "ignore").decode("latin-1")
    pdf.multi_cell(0, 6, txt=safe)
    return bytes(pdf.output())


_ATTACK_STORY_HTML = """<!DOCTYPE html>
<html><head><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#000;color:#fff;font-family:-apple-system,'SF Pro Display',sans-serif;overflow-x:hidden}
.wrap{padding:24px 24px 32px}
.hdr{display:flex;justify-content:space-between;align-items:center;margin-bottom:28px}
.ttl{font-size:14px;font-weight:600;color:rgba(235,235,245,.85);letter-spacing:-.02em}
.ctrls{display:flex;align-items:center;gap:10px}
#prevBtn,#nextBtn,#playBtn{background:rgba(10,132,255,.12);border:.5px solid rgba(10,132,255,.35);color:#0a84ff;
  border-radius:980px;font-size:11.5px;font-weight:600;padding:5px 14px;cursor:pointer;
  font-family:inherit;letter-spacing:-.01em;transition:background .15s}
#prevBtn:hover,#nextBtn:hover,#playBtn:hover{background:rgba(10,132,255,.22)}
#prevBtn:disabled,#nextBtn:disabled{opacity:.35;cursor:not-allowed}
#stepLbl{font-size:10px;color:rgba(235,235,245,.6);margin-right:8px;white-space:nowrap;}
#ctr{font-size:10.5px;color:rgba(235,235,245,.28);font-variant-numeric:tabular-nums}
.track{display:flex;align-items:center;overflow-x:auto;padding-bottom:12px;scrollbar-width:none}
.track::-webkit-scrollbar{display:none}
.node{flex-shrink:0;width:175px;opacity:0;transform:translateY(20px) scale(.95);
  transition:opacity .45s ease,transform .45s cubic-bezier(.34,1.56,.64,1)}
.node.vis{opacity:1;transform:none}
.node.past .card{opacity:.45}
.node.active .card{border-color:rgba(10,132,255,.45);background:rgba(10,132,255,.05);
  box-shadow:0 0 0 1px rgba(10,132,255,.12),0 8px 28px rgba(0,0,0,.55)}
.card{background:#1c1c1e;border:.5px solid rgba(255,255,255,.07);border-radius:12px;
  padding:13px;transition:all .3s ease;position:relative;overflow:hidden}
.node.active .card::after{content:'';position:absolute;top:0;left:-100%;width:55%;height:100%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.035),transparent);
  animation:shim 2s ease-in-out infinite}
@keyframes shim{0%{left:-100%}100%{left:220%}}
.phase{font-size:8.5px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;
  margin-bottom:7px;padding:2px 6px;border-radius:4px;display:inline-block}
.evt{font-size:12px;font-weight:600;color:rgba(235,235,245,.9);line-height:1.4;
  margin-bottom:9px;letter-spacing:-.01em}
.ts{font-size:9.5px;color:rgba(235,235,245,.28);font-family:'SF Mono',monospace;margin-bottom:8px}
.srow{display:flex;align-items:center;gap:5px}
.slbl{font-size:8.5px;color:rgba(235,235,245,.22);text-transform:uppercase;letter-spacing:.08em;width:22px;flex-shrink:0}
.strack{flex:1;height:2px;background:rgba(255,255,255,.05);border-radius:1px;overflow:hidden}
.sfill{height:100%;border-radius:1px;width:0%;transition:width .6s cubic-bezier(.4,0,.2,1) .3s}
.node.vis .sfill{width:var(--sp)}
.conn{flex-shrink:0;width:36px;display:flex;align-items:center;position:relative;top:-8px}
.cline{height:1px;background:linear-gradient(90deg,rgba(255,255,255,.1),rgba(255,255,255,.03));
  flex:1;opacity:0;transition:opacity .35s ease .15s}
.carr{color:rgba(255,255,255,.12);font-size:9px;opacity:0;transition:opacity .35s ease .25s}
.conn.vis .cline,.conn.vis .carr{opacity:1}
.dots{display:flex;gap:8px;justify-content:center;margin-top:20px}
.dot{width:22px;height:22px;min-width:22px;border-radius:50%;background:rgba(255,255,255,.1);cursor:pointer;transition:all .3s;display:flex;align-items:center;justify-content:center;font-size:10px;color:rgba(255,255,255,.65);}
.dot.active{background:#0a84ff;transform:scale(1.25);color:#fff;}
.dot.past{background:rgba(10,132,255,.32);color:#fff;}
@keyframes pulse{0%{transform:scale(.85);opacity:.6}100%{transform:scale(1.45);opacity:0}}
.ring{position:absolute;inset:-4px;border:1px solid rgba(10,132,255,.28);border-radius:14px;
  animation:pulse 1.7s ease-out infinite;pointer-events:none}
</style></head><body>
<div class="wrap">
  <div class="hdr">
    <span class="ttl">Attack story &middot; Step by step</span>
    <div class="ctrls">
      <span id="stepLbl"></span>
      <button id="prevBtn" onclick="prev()" disabled>&#9664;</button>
      <button id="playBtn" onclick="toggle()">Play</button>
      <button id="nextBtn" onclick="nextStep()" disabled>&#9654;</button>
      <span id="ctr">0 / 0</span>
    </div>
  </div>
  <div class="track" id="track"></div>
  <div class="dots" id="dots"></div>
</div>
<script>
const DATA=__DATA__;
const PC={"Initial Access":"#ff453a","Execution":"#ff9f0a","Persistence":"#ffd60a",
"Privilege Escalation":"#ff6961","Defense Evasion":"#bf5af2","Credential Access":"#ff375f",
"Discovery":"#64d2ff","Lateral Movement":"#0a84ff","Collection":"#30d158",
"Command and Control":"#ff453a","Exfiltration":"#ff6961","Impact":"#ff453a"};
function pc(p){for(const[k,v]of Object.entries(PC)){if(p&&p.toLowerCase().includes(k.toLowerCase()))return v;}return"#86868b";}
function sc(s){return s>=8?"#ff453a":s>=5?"#ff9f0a":"#30d158";}
const track=document.getElementById("track"),dots=document.getElementById("dots");
DATA.forEach((d,i)=>{
  if(i>0){const c=document.createElement("div");c.className="conn";c.id="c"+i;
    c.innerHTML='<div class="cline"></div><div class="carr">&#9654;</div>';track.appendChild(c);}
  const n=document.createElement("div");n.className="node";n.id="n"+i;
  const p=pc(d.phase||""),s=sc(d.severity||5),sp=((d.severity||5)/10*100).toFixed(0)+"%";
  n.style.setProperty("--sp",sp);
  n.innerHTML='<div class="card"><span class="phase" style="background:'+p+'22;color:'+p+';">'+(d.phase||"Unknown")+'</span>'
    +'<div class="evt">'+(d.event||"")+'</div><div class="ts">'+(d.time||"")+'</div>'
    +'<div class="srow"><span class="slbl">SEV</span><div class="strack"><div class="sfill" style="background:'+s+';"></div></div></div></div>';
  track.appendChild(n);
  const dot=document.createElement("div");dot.className="dot";dot.id="d"+i;dot.textContent = i + 1;dot.onclick=()=>jump(i);dots.appendChild(dot);
});
let cur=-1,playing=false,tmr=null;
function upd(){
  const count = DATA.length;
  const currentStep = Math.max(0, cur + 1);
  document.getElementById("ctr").textContent = currentStep + " / " + count;
  if(document.getElementById("stepLbl")) {
      document.getElementById("stepLbl").textContent = "Step " + currentStep + " of " + count;
  }
  document.getElementById("prevBtn").disabled = cur <= 0;
  document.getElementById("nextBtn").disabled = cur >= count - 1;
}
function show(idx){
  cur=idx;upd();
  DATA.forEach((_,i)=>{
    const n=document.getElementById("n"+i),dot=document.getElementById("d"+i);
    if(i<=idx){
      n.classList.add("vis");
      if(i<idx){n.classList.add("past");n.classList.remove("active");const r=n.querySelector(".ring");if(r)r.remove();}
      else{n.classList.add("active");n.classList.remove("past");
        if(!n.querySelector(".ring")){const r=document.createElement("div");r.className="ring";n.querySelector(".card").appendChild(r);}
        n.scrollIntoView({behavior:"smooth",inline:"center",block:"nearest"});}
    } else {
      n.classList.remove("vis","active","past");const r=n.querySelector(".ring");if(r)r.remove();
    }
    dot.className="dot"+(i===idx?" active":i<idx?" past":"");
    if(i>0&&i<=idx)document.getElementById("c"+i).classList.add("vis");
    else if(i>0)document.getElementById("c"+i).classList.remove("vis");
  });
}
function jump(i){ clearInterval(tmr); playing=false; document.getElementById("playBtn").textContent="Play"; show(i); }
function prev(){ if(cur>0){ clearInterval(tmr); playing=false; document.getElementById("playBtn").textContent="Play"; show(cur-1); } }
function nextStep(){ if(cur < DATA.length-1){ clearInterval(tmr); playing=false; document.getElementById("playBtn").textContent="Play"; show(cur+1); } }
function toggle(){
  if(playing){ clearInterval(tmr); playing=false; document.getElementById("playBtn").textContent="Play"; }
  else{
    if(cur>=DATA.length-1) cur=-1;
    playing=true;
    document.getElementById("playBtn").textContent="Pause";
    tmr=setInterval(()=>{
      if(cur<DATA.length-1) show(cur+1);
      else { clearInterval(tmr); playing=false; document.getElementById("playBtn").textContent="Play"; }
    },1200);
  }
}
document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") prev();
  else if (event.key === "ArrowRight") nextStep();
  else if (event.key === " ") { event.preventDefault(); toggle(); }
});
upd();setTimeout(toggle,700);
</script></body></html>"""

def render_attack_story(timeline: list) -> None:
    if not timeline:
        return
    data_json = json.dumps(timeline)
    html = _ATTACK_STORY_HTML.replace("__DATA__", data_json)
    components.html(html, height=420, scrolling=False)


# ============================================================
# INPUT
# ============================================================
st.subheader("Input")
col1, col2 = st.columns(2)
with col1:
    logs = st.file_uploader("Log streams", accept_multiple_files=True)
with col2:
    malware = st.file_uploader("Malware artifacts", accept_multiple_files=True)

st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
run_clicked = st.button("Run analysis")

# ============================================================
# EXECUTE
# ============================================================
if run_clicked:
    if not (logs or malware):
        st.error("No data provided.")
    elif not gemini_ok:
        st.error("GOOGLE_API_KEY not set in .env.")
    else:
        log_content = truncate_text("".join([safe_decode(f) for f in logs])) if logs else ""
        malware_content = truncate_text("".join([safe_decode(f) for f in malware]), max_chars=40_000) if malware else ""

        prompt = f"""You are a senior forensic analyst. Analyze the artifacts below and produce a structured report.

Confidence threshold: {trust_score}%. Only include findings you assess with at least {trust_score}% confidence. Do not speculate or report observations below this threshold.

While you work, narrate your findings in real time. Whenever you spot something significant, output a single line beginning with "INSIGHT:" followed by the observation, before continuing.

Use these EXACT section headers in this order:

### RECONSTRUCTION
A detailed narrative of the attack chain and MITRE ATT&CK technique mapping.

### MALWARE LAB
Static analysis of any scripts. Cover intent, obfuscation, C2 callbacks, and IOCs.

### REMEDIATION
A bash or PowerShell containment script wrapped in a fenced code block.

### TIMELINE
A JSON timeline wrapped between DATA_START and DATA_END. Include the MITRE ATT&CK phase and a separate impact score for each event:
DATA_START
[{{"time": "HH:MM", "event": "name", "severity": 1-10, "impact": 1-10, "phase": "ATT&CK phase"}}]
DATA_END

LOG DATA:
{log_content or "(none provided)"}

MALWARE ARTIFACTS:
{malware_content or "(none provided)"}
"""

        st.markdown("---")
        st.subheader("Live analysis")
        full_text = st.write_stream(stream_gemini(prompt))
        st.session_state.analysis_result = full_text

# ============================================================
# RESULTS
# ============================================================
if st.session_state.analysis_result:
    full_text = st.session_state.analysis_result

    insights = re.findall(r"INSIGHT:\s*(.+)", full_text)
    if insights:
        st.markdown("---")
        st.subheader("Key observations")
        cards_html = "".join(
            f'<div class="insight-card">{ins.strip()}</div>'
            for ins in insights[:8]
        )
        st.markdown(f'<div class="insight-grid">{cards_html}</div>', unsafe_allow_html=True)

    timeline = extract_json_block(full_text)
    if timeline:
        try:
            df = pd.DataFrame(timeline)
            if "impact" not in df.columns:
                df["impact"] = df["severity"]
            if "phase" not in df.columns:
                df["phase"] = "Unknown"

            fig = px.scatter_3d(
                df,
                x="time", y="severity", z="impact",
                color="phase",
                size="severity",
                hover_name="event",
                hover_data={"time": True, "severity": True, "impact": True, "phase": True},
                text="event",
            )
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(family="-apple-system, Inter, sans-serif", color="rgba(235,235,245,0.5)", size=11),
                title=dict(
                    text="Attack progression · 3D",
                    font=dict(family="-apple-system, Inter, sans-serif", color="rgba(235,235,245,0.85)", size=15),
                ),
                scene=dict(
                    xaxis=dict(title="Time",     backgroundcolor="rgba(28,28,30,1)", gridcolor="rgba(255,255,255,0.06)", showbackground=True, zerolinecolor="rgba(255,255,255,0.06)"),
                    yaxis=dict(title="Severity", backgroundcolor="rgba(28,28,30,1)", gridcolor="rgba(255,255,255,0.06)", showbackground=True, zerolinecolor="rgba(255,255,255,0.06)"),
                    zaxis=dict(title="Impact",   backgroundcolor="rgba(28,28,30,1)", gridcolor="rgba(255,255,255,0.06)", showbackground=True, zerolinecolor="rgba(255,255,255,0.06)"),
                ),
                legend=dict(font=dict(color="rgba(235,235,245,0.5)"), bgcolor="rgba(0,0,0,0)"),
                margin=dict(l=0, r=0, t=48, b=0),
            )
            fig.update_traces(textfont=dict(color="rgba(235,235,245,0.7)", size=9))
            st.markdown("---")
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")
            st.subheader("Attack story")
            render_attack_story(timeline)
        except Exception as e:
            st.warning(f"Could not render timeline: {e}")

    st.markdown("---")
    t1, t2, t3 = st.tabs(["Forensics", "Malware lab", "Remediation"])
    with t1:
        st.markdown(split_section(full_text, "### RECONSTRUCTION", "### MALWARE LAB") or "_No reconstruction generated._")
    with t2:
        st.markdown(split_section(full_text, "### MALWARE LAB", "### REMEDIATION") or "_No malware analysis generated._")
    with t3:
        rem = split_section(full_text, "### REMEDIATION", "### TIMELINE")
        m = re.search(r"```(?:bash|powershell|sh|ps1)?\s*(.*?)```", rem, re.DOTALL)
        if m:
            st.code(m.group(1).strip(), language="bash")
        else:
            st.markdown(rem or "_No remediation script generated._")

    st.markdown("---")
    st.download_button(
        "Export report",
        data=build_pdf(full_text),
        file_name="NeuralArchitect_Report.pdf",
        mime="application/pdf",
    )

# ============================================================
# RIGHT PANEL TOGGLE — top right
# ============================================================
st.markdown('<div id="na-panel-btn-anchor"></div>', unsafe_allow_html=True)
with st.container():
    btn_label = "✕  Close" if st.session_state.panel_open else "Settings"
    if st.button(btn_label, key="panel_toggle_btn"):
        st.session_state.panel_open = not st.session_state.panel_open
        st.rerun()

# ============================================================
# RIGHT PANEL — settings
# ============================================================
if st.session_state.panel_open:
    st.markdown('<div id="na-rpanel-anchor"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown(
            '<p style="font-size:0.6875rem;color:rgba(235,235,245,0.3);letter-spacing:0.1em;'
            'text-transform:uppercase;font-weight:600;margin:0 0 1.5rem;">Configuration</p>',
            unsafe_allow_html=True,
        )
        status_color = "#30d158" if gemini_ok else "#ff453a"
        status_label = "Connected" if gemini_ok else "API key missing"
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">'
            f'<span style="width:6px;height:6px;border-radius:50%;background:{status_color};'
            f'flex-shrink:0;display:inline-block;"></span>'
            f'<span style="font-size:0.875rem;color:rgba(235,235,245,0.65);">{status_label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div style="display:inline-flex;align-items:center;background:#2c2c2e;border-radius:6px;'
            f'padding:0.25rem 0.625rem;margin-bottom:2rem;">'
            f'<span style="font-size:0.75rem;font-family:SF Mono,JetBrains Mono,monospace;'
            f'color:rgba(235,235,245,0.4);">{GEMINI_MODEL}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="font-size:0.6875rem;color:rgba(235,235,245,0.3);letter-spacing:0.1em;'
            'text-transform:uppercase;font-weight:600;margin:0 0 0.875rem;">Analysis</p>',
            unsafe_allow_html=True,
        )
        st.slider("Confidence threshold", 0, 100, 85, key="conf_threshold")
        st.markdown(
            '<p style="font-size:0.75rem;color:rgba(235,235,245,0.28);line-height:1.55;margin-top:0.375rem;">'
            'Findings below this confidence level are suppressed from the report.</p>',
            unsafe_allow_html=True,
        )

# ============================================================
# FLOATING CHAT — bottom left
# ============================================================
st.markdown('<div id="na-chat-toggle-anchor"></div>', unsafe_allow_html=True)
with st.container():
    label = "✕  Close" if st.session_state.chat_open else "Ask assistant"
    if st.button(label, key="chat_toggle_btn"):
        st.session_state.chat_open = not st.session_state.chat_open
        st.rerun()

if st.session_state.chat_open:
    st.markdown('<div id="na-chat-anchor"></div>', unsafe_allow_html=True)
    with st.container():
        st.markdown("**Assistant**")
        st.caption("Ask anything about the current analysis.")

        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if question := st.chat_input("Type a question"):
            st.session_state.chat_messages.append({"role": "user", "content": question})
            with st.spinner("Thinking..."):
                answer = chat_with_gemini(question, st.session_state.analysis_result)
            st.session_state.chat_messages.append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state.chat_messages:
            if st.button("Clear chat", key="chat_clear_btn"):
                st.session_state.chat_messages = []
                st.rerun()
