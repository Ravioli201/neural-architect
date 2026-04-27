# Security Policy

Neural Architect is a security tool. We take vulnerabilities in the project itself seriously, and we'd rather hear about them privately than read about them on Twitter.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security problems.**

Instead, use GitHub's private vulnerability reporting:

1. Go to the [Security tab](https://github.com/Ravioli201/neural-architect/security) of this repo.
2. Click **Report a vulnerability**.
3. Fill in the form with as much detail as you can.

If that doesn't work for you, contact the maintainer directly through the email address listed on their GitHub profile.

## What to include

- A description of the issue and its impact.
- Steps to reproduce, ideally with a minimal proof-of-concept.
- The version / commit hash you tested against.
- Any suggested mitigation.

## What we're particularly interested in

- **Prompt injection** that lets an attacker controlling log content cause the analyst to take harmful actions, exfiltrate secrets via the model, or escape the analyst persona.
- **Resource exhaustion** - log payloads that crash the API, blow the context window in surprising ways, or burn unbounded LLM tokens.
- **Secrets exposure** - anything that could cause `GEMINI_API_KEY` or other env vars to leak through logs, error messages, or model output.
- **Path traversal / unsafe deserialization** in the log parsers, IOC extractor, or exporters.
- **Dependency CVEs** that materially affect this project's runtime.

## What's out of scope

- Issues in the bundled sample logs (they're synthetic and clearly labeled as such).
- The fact that the model can be wrong. It can. The `model_notes` field is meant to be read.
- Vulnerabilities in upstream dependencies - please report those upstream and let us know if we need to bump a pin.

## Disclosure

We aim to acknowledge reports within **72 hours**, give a substantive response within **7 days**, and ship a fix or mitigation within **30 days** for confirmed issues. If you want to coordinate public disclosure, tell us your preferred timeline in the report.

## Thanks

Responsible reporters will be credited in release notes unless they request otherwise.