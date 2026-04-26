import os
import json
import logging
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
import google.generativeai as genai
from flask import Flask, request, jsonify

# These are your local project files
from triage import triage_alert
from nl_to_spl import nl_to_spl
from report import generate_report
from splunk_forwarder import forward_to_splunk

# --- Setup ---
load_dotenv()

# --- DEBUG TRUTH PRINTS ---
# These will show up in your terminal as soon as you run the script
print("\n" + "="*40)
print("HACKATHON DEBUG MODE")
print(f"Splunk URL Found: {os.environ.get('SPLUNK_HEC_URL')}")
print(f"Splunk Token Found: {os.environ.get('SPLUNK_HEC_TOKEN')}")
print(f"Gemini API Key Loaded: {bool(os.environ.get('GOOGLE_API_KEY'))}")
print("="*40 + "\n")

API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not set. Check your .env file.")

genai.configure(api_key=API_KEY)

# Log file setup
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
TRIAGE_LOG = LOG_DIR / "ai_triage.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("ai_service")

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "service": "ai_service"}

@app.route("/triage", methods=["POST"])
def triage_endpoint():
    """Take an alert, enrich it with AI, and push to Splunk."""
    alert = request.get_json(force=True)
    known_macs = alert.pop("known_macs", [])

    try:
        result = triage_alert(alert, known_macs)
    except Exception as e:
        log.exception("Triage failed")
        result = {
            "severity": "unknown",
            "summary": f"AI triage unavailable: {e}",
            "raw_alert": alert,
        }

    # Prepare the package for Splunk
    enriched = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "original_alert": alert,
        "ai_analysis": result,
    }

    # 1. Write to local log file (The "Paper Trail")
    with open(TRIAGE_LOG, "a") as f:
        f.write(json.dumps(enriched) + "\n")

    # 2. Forward to teammate's Splunk HEC (The "Live Feed")
    # This MUST happen before the return statement!
    forward_to_splunk(enriched)

    log.info(
        "Triaged alert: severity=%s",
        result.get("severity", "unknown"),
    )
    
    # 3. Final step: send the answer back to the simulator
    return jsonify(enriched)

@app.route("/query", methods=["POST"])
def query_endpoint():
    data = request.get_json(force=True)
    question = data.get("question", "")
    try:
        spl = nl_to_spl(question)
        return {"question": question, "spl": spl}
    except Exception as e:
        return {"error": str(e)}, 500

@app.route("/report", methods=["POST"])
def report_endpoint():
    data = request.get_json(force=True)
    events = data.get("events", [])
    try:
        markdown = generate_report(events)
        return {"report": markdown}
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    log.info("Starting AI service on http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)