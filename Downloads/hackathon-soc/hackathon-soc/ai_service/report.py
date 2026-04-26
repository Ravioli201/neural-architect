"""
Incident report generator. Uses Gemini 2.5 Pro for deeper reasoning
over the full event timeline. Run this at end of demo for a polished
markdown report you can show as your final slide.
"""
import json
import google.generativeai as genai

REPORT_PROMPT = """You are a senior SOC analyst writing a post-incident report for a blue team demonstration.

Below are all alerts and events captured during the session. Write a professional markdown report with these sections:

# Incident Report

## 1. Executive Summary
2-3 sentences for a non-technical reader.

## 2. Attack Timeline
Chronological bulleted list with timestamps, source, and what happened.

## 3. Indicators of Compromise (IoCs)
Markdown table with columns: Type | Value | First Seen | Notes

## 4. MITRE ATT&CK Mapping
Markdown table with columns: Technique ID | Name | Tactic | Observed Evidence

## 5. Recommended Mitigations
Bulleted, prioritized (most urgent first). Be specific to the observed activity.

## 6. Detection Coverage Notes
Brief notes on what the pipeline caught well and what it missed.

Be specific. Reference actual IPs, MACs, signatures, and DNS queries from the data.
Do NOT invent details that aren't in the events.

Events:
{events_json}
"""

_pro_model = genai.GenerativeModel(
    "gemini-2.5-pro",
    generation_config={"temperature": 0.3},
)


def generate_report(events: list) -> str:
    response = _pro_model.generate_content(
        REPORT_PROMPT.format(events_json=json.dumps(events, indent=2))
    )
    return response.text


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    sample_events = [
        {
            "timestamp": "2026-04-25T14:02:11Z",
            "type": "esp32_connection",
            "mac_address": "AA:BB:CC:11:22:33",
            "ssid": "Free_Airport_WiFi",
        },
        {
            "timestamp": "2026-04-25T14:02:45Z",
            "type": "snort_alert",
            "signature": "ET POLICY Cleartext FTP Login Attempt",
            "src_ip": "10.0.0.5",
            "dest_ip": "10.0.0.1",
        },
        {
            "timestamp": "2026-04-25T14:03:02Z",
            "type": "snort_alert",
            "signature": "ET SCAN Nmap Scripting Engine",
            "src_ip": "10.0.0.5",
        },
    ]
    print(generate_report(sample_events))
