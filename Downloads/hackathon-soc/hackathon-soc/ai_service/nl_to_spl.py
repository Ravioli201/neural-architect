"""
Natural language -> Splunk SPL query translator.
Lets analysts ask plain-English questions during the demo.
"""
import google.generativeai as genai

NL_TO_SPL_PROMPT = """Convert this analyst question into a valid Splunk SPL query.

Available indexes and fields:
- index=snort: src_ip, dest_ip, src_port, dest_port, signature, classification, priority, _time
- index=esp32: mac_address, ssid_requested, rssi, dns_query, _time
- index=ai_triage: ai_analysis.severity, ai_analysis.mitre_technique, ai_analysis.summary, _time

Rules:
- Always include an index= clause
- Default time range: earliest=-1h unless the user says otherwise
- Use stats, top, or timechart for aggregations
- Return ONLY the SPL query — no explanation, no markdown fences, no backticks

Question: {question}

SPL:"""

_model = genai.GenerativeModel(
    "gemini-2.5-flash",
    generation_config={"temperature": 0.1},
)


def nl_to_spl(question: str) -> str:
    response = _model.generate_content(
        NL_TO_SPL_PROMPT.format(question=question)
    )
    spl = response.text.strip()
    # Strip stray markdown fences
    if spl.startswith("```"):
        spl = spl.strip("`").strip()
        if spl.startswith("spl"):
            spl = spl[3:].strip()
    return spl


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

    questions = [
        "show me the top 10 source IPs that triggered alerts in the last hour",
        "which MAC addresses queried more than 5 unique domains today",
        "what are the highest severity AI-triaged alerts from the last 30 minutes",
    ]
    for q in questions:
        print(f"Q: {q}")
        print(f"SPL: {nl_to_spl(q)}\n")
