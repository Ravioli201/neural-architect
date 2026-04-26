# What changed from v1

If you're comparing this against your original hackathon repo:

## Repo structure

**Before:**
```
neural-architect/
├── Downloads/
│   └── hackathon-soc/
│       └── hackathon-soc/
│           └── ai_service/
│               └── (all the actual code)
├── Analysis.jpg
├── Attack.jpg
└── .devcontainer/
```

**After:**
```
neural-architect/
├── README.md                    ← polished, with hero + diagram + demo
├── LICENSE
├── pyproject.toml               ← installable as a real Python package
├── requirements.txt
├── Dockerfile
├── .env.example
├── .gitignore
├── src/neural_architect/        ← actual code, properly namespaced
│   ├── core/
│   ├── llm/
│   ├── exporters/
│   ├── api/
│   ├── ui/
│   └── cli.py
├── data/samples/                ← three realistic synthetic incidents
├── eval/                        ← benchmark harness + golden labels
├── tests/                       ← pytest suite, 20 tests passing
├── docs/                        ← architecture, deployment, LinkedIn post, demo script
├── assets/                      ← architecture diagram (SVG)
├── scripts/                     ← run helpers
└── .github/workflows/ci.yml     ← matrix CI on 3.10/3.11/3.12
```

## What's new (not just rearranged)

| Capability | Before | After |
|------------|--------|-------|
| Log format support | (varied) | Auto-detect: JSONL, syslog, Apache, CSV, plain text |
| IOC extraction | Implicit, in-prompt | Deterministic regex pre-pass; merged with model output |
| Output format | (varied) | Pydantic-typed `AttackChain`, schema-constrained from Gemini |
| MITRE mapping | Mentioned | Per-event, with confidence and rationale |
| STIX 2.1 export | — | Spec-compliant bundle via `stix2` library |
| Markdown report | — | IR-style report ready for ticketing |
| FastAPI service | — | `/analyze`, `/export/stix`, `/export/markdown`, `/health` |
| CLI | — | `neural-architect analyze incident.log --format markdown` |
| Eval harness | — | precision / recall / F1 at parent-technique level, multi-run averaging |
| Tests | — | 20 pytest tests, CI matrix on 3 Python versions |
| Sample data | — | Three labeled synthetic incidents |
| Architecture diagram | — | Clean SVG, embedded in README and docs |
| Deployment guide | — | Streamlit Cloud / Render / HF Spaces walkthrough |
| LinkedIn post | — | Three drafts + posting checklist |
| Demo video script | — | Storyboard, captions, production notes |

## What you need to do once you copy this back

1. **Push the new structure to GitHub.** Replace what's there. The new tree is in `/mnt/user-data/outputs/neural-architect/`.
2. **Get a Gemini API key** at https://aistudio.google.com/apikey — copy it into `.env` for local testing.
3. **Run the tests once locally** to confirm nothing regressed:
   ```bash
   pip install -r requirements.txt
   PYTHONPATH=src pytest
   ```
4. **Run the analyzer once against a sample** to confirm the Gemini wiring works on your end:
   ```bash
   PYTHONPATH=src python -m neural_architect.cli analyze data/samples/web_exploit_to_rce.log
   ```
5. **Run the eval harness** and screenshot the result for the LinkedIn post — concrete numbers convert better than claims:
   ```bash
   python -m eval.benchmark --runs 3
   ```
6. **Deploy the Streamlit demo** following `docs/deployment.md`.
7. **Record the demo video** following `docs/demo_video_script.md`. Save the GIF to `assets/demo.gif`.
8. **Replace the placeholder demo GIF reference in the README** with your actual recording.
9. **Pick one of the three LinkedIn drafts** in `docs/linkedin_post.md` and post.

## Things I deliberately left for you to do

- The actual logic of your *original* analysis code (if it had bespoke parsing or a different model architecture). I built a clean, working baseline; if your v1 had clever pieces, port them into `src/neural_architect/core/analyzer.py` and the prompt in `src/neural_architect/llm/prompts.py`.
- The hero GIF / video — only you can record this against a real Gemini key.
- The "About" repo description on GitHub. Update it to match the new README tagline.
- Adding more golden samples to `eval/golden/`. Three is enough to ship; ten would be impressive.

## Things I'd recommend doing in week two

- Write a short blog post on the deterministic-preprocessing-then-LLM design choice. The architecture doc has the substance; turn it into a 600-word post on Medium / dev.to / your own blog. Cross-link from the README.
- Add streaming reconstruction (partial chains as the model generates) — it's a noticeable UX win and a great "v0.3" announcement.
- Submit the repo to https://github.com/topics/incident-response and https://github.com/topics/mitre-attack landing pages by adding the right topic tags.
