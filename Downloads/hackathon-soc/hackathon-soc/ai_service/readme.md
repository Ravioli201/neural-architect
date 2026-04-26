🔍 Neural Architect

AI-Powered Forensic Analysis & Threat Intelligence Platform

Neural Architect is a real-time forensic analysis tool built with Streamlit and powered by Google's Gemini 2.5 Flash. It ingests raw log streams and malware artifacts, automatically reconstructing attack chains, mapping them to the MITRE ATT&CK framework, and generating interactive visualizations.

 (Pro-tip: Add a screenshot of your dashboard here!)

✨ Features

Live AI Analysis: Streams the forensic breakdown in real-time as the AI processes the logs.

Automated MITRE Mapping: Maps adversary behaviors directly to MITRE ATT&CK tactics and techniques.

3D Threat Visualization: Interactive 3D scatter plots mapping attack progression across time, severity, and impact using Plotly.

Tactical Playback HUD: A custom-built, step-by-step interactive timeline that animates the attack story.

One-Click Export: Instantly compile the generated threat intelligence into a downloadable PDF report.

🛠️ Tech Stack

Frontend & UI: Streamlit (with custom HTML/CSS/JS components)

AI Engine: Google Gemini API (gemini-2.5-flash)

Data Visualization: Plotly Express, Pandas

Export: FPDF

🚀 Quick Start

1. Clone the repository

git clone [https://github.com/YOUR_USERNAME/neural-architect.git](https://github.com/YOUR_USERNAME/neural-architect.git)
cd neural-architect


2. Install dependencies

pip install streamlit google-generativeai pandas plotly fpdf python-dotenv


3. Set up your environment variables

Create a .env file in the root directory and add your Google Gemini API key:

GOOGLE_API_KEY="your_api_key_here"


4. Run the application

streamlit run neural_architect_minimal.py


🧠 How the Context-Aware Assistant Works

Unlike standard chatbots, Neural Architect's assistant is injected with Live UI State. When you adjust the "Confidence Threshold" slider in the settings panel, that variable is dynamically passed into the LLM's system instructions. This allows the AI to accurately answer questions about suppressed findings and current configurations without the user ever explicitly typing them.

📄 License

This project is licensed under the MIT License.
