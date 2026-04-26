🔍 Neural Architect

AI-Powered Forensic Analysis & Threat Intelligence Platform

Neural Architect is a real-time forensic analysis tool built with Streamlit and powered by Google's Gemini 2.5 Flash. It ingests raw log streams and malware artifacts, automatically reconstructing attack chains, mapping them to the MITRE ATT&CK framework, and generating interactive visualizations.

 (Pro-tip: Add a screenshot of your dashboard here!)

✨ Features

Live AI Analysis: Streams the forensic breakdown in real-time as the AI processes the logs.

Automated MITRE Mapping: Maps adversary behaviors directly to MITRE ATT&CK tactics and techniques.

3D Threat Visualization: Interactive 3D scatter plots mapping attack progression across time, severity, and impact using Plotly.

Tactical Playback HUD: A custom-built, step-by-step interactive timeline that animates the attack story.

Context-Aware Assistant: A floating AI chat assistant that not only understands the forensic report but is also aware of your current UI settings (like your Confidence Threshold slider).

One-Click Export: Instantly compile the generated threat intelligence into a downloadable PDF report.

🛠️ Tech Stack

Frontend & UI: Streamlit (with custom HTML/CSS/JS components)

AI Engine: Google Gemini API (gemini-2.5-flash)

Data Visualization: Plotly Express, Pandas

Export: FPDF
