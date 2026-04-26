"""Top-level Streamlit entrypoint for Streamlit Cloud.

Streamlit Cloud doesn't know about our src/ layout, so we add it to
sys.path and then re-execute the real app.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

# Now execute the real app
exec((ROOT / "src" / "neural_architect" / "ui" / "streamlit_app.py").read_text(), {"__name__": "__main__", "__file__": str(ROOT / "src" / "neural_architect" / "ui" / "streamlit_app.py")})
