# Deploying Neural Architect

You want a "Live demo →" link in your README. Here's how to get one without paying anything.

## Option 1 — Streamlit Community Cloud (recommended for the demo)

**Free, 5-minute setup, perfect for a passion project.**

1. Push the repo to GitHub (you already have it there).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app**, select your repo, and point it at the entry file:
   ```
   src/neural_architect/ui/streamlit_app.py
   ```
4. In **Advanced settings → Secrets**, paste:
   ```toml
   GEMINI_API_KEY = "your_key_here"
   ```
   (Streamlit Cloud reads this as if it were a `.streamlit/secrets.toml` file.)
5. Set the Python version to **3.12** and let it deploy.
6. Once live, the URL looks like `https://neural-architect.streamlit.app`. Add it to the README at the **Live demo** anchor.

### Important: rate-limit the public demo

If you publish a live demo with your own API key, anyone can burn through your Gemini quota. Two options:

**Option A — make users bring their own key.** The Streamlit UI already has an API-key field in the sidebar. Leave the env var unset on the deployed app. Users who want to try it paste their own key. This is the safest choice.

**Option B — keep your key, but add a usage cap.** Set up budget alerts in [Google Cloud billing](https://console.cloud.google.com/billing) and a hard quota in [AI Studio](https://aistudio.google.com). Pin a banner in the UI explaining the demo is rate-limited. Acceptable if you're okay paying a few dollars a month for visibility.

I'd start with Option A.

## Option 2 — Render (for the FastAPI service)

If you want the `/analyze` endpoint reachable too:

1. https://render.com → **New → Web Service**.
2. Point at the repo. Render auto-detects the `Dockerfile`.
3. Set the start command:
   ```
   uvicorn neural_architect.api.main:app --host 0.0.0.0 --port $PORT
   ```
4. Add `GEMINI_API_KEY` as an environment variable.
5. Free tier sleeps after 15 minutes of inactivity (cold start ~30s). Fine for a demo, not for production.

## Option 3 — Hugging Face Spaces

Also free, also one-click for Streamlit. Works well if you want the project to surface in HF search.

1. Create a new Space → SDK = Streamlit.
2. Connect to the GitHub repo or push directly.
3. Set `GEMINI_API_KEY` as a Space secret.
4. Move the entrypoint to a top-level `app.py` that just does:
   ```python
   from neural_architect.ui.streamlit_app import *  # noqa
   ```
   (HF Spaces expects the entrypoint at the repo root.)

## Local-first alternative

If you don't want to deploy at all, that's fine. The README already shows the local quick-start, and the demo video does the heavy lifting. But a "Live demo →" link in the README converts curious viewers ~3x more than a local-only project. Worth the 5 minutes.

## Once deployed

- Add the demo URL to the README (replace the `[Live demo](#-live-demo)` anchor with the actual URL).
- Add it to the **About** field on the GitHub repo.
- Add it to the LinkedIn post.
- Pre-load the public demo with one of the sample logs already in the textarea so visitors can hit the button immediately, without reading instructions.
