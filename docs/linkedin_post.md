# LinkedIn launch — three drafts

Pick one. Don't post all three. Each is tuned to a different audience.

The rules I followed:
- Hook in the first 2 lines (LinkedIn truncates at ~210 chars on mobile)
- One concrete technical detail you actually built — not buzzwords
- One link, at the end
- No "I'm thrilled to announce" energy
- Sounds like a person, not a press release

---

## Draft A — Builder voice (recommended for engineers / security folks)

> SOC analysts spend most of their day answering one question: *what actually happened?*
>
> They stare at pages of Sysmon events, auth logs, and EDR alerts trying to stitch them into a story, map them to MITRE, and write it up. By the time they're done, the attacker has had hours to keep going.
>
> So I built Neural Architect — a passion project that compresses that work from hours to seconds.
>
> Drop in raw telemetry, get back a reconstructed attack chain, scored MITRE ATT&CK techniques, deduped IOCs, and a SOC-ready STIX 2.1 bundle.
>
> The interesting part wasn't the model. It was figuring out that **you can't just throw 50 KB of logs at an LLM and hope.** Raw logs go through a deterministic preprocessing pass first — format detection, regex IOC extraction, timeline normalization — and only then hit Gemini 2.5 Flash with a Pydantic-schema-constrained prompt. The model gets structured anchors, returns structured output, and we never spend tokens on work that regex does better.
>
> I also shipped an eval harness with golden labels and precision/recall/F1 scoring, because most LLM security demos have zero rigor and I didn't want this to be another one.
>
> Open source, MIT, code + sample logs + eval methodology in the repo:
> 👉 https://github.com/Ravioli201/neural-architect
>
> Feedback welcome — especially from anyone who's done DFIR work.
>
> #cybersecurity #DFIR #MITREATTACK #LLM #incidentresponse

---

## Draft B — Story voice (recommended for general LinkedIn audience)

> Built something this weekend that I'm pretty proud of.
>
> Problem: a junior SOC analyst's first hour every morning is reading logs and asking *what happened here?* Sysmon, syslog, EDR, web access logs — pages of it. The attacker doesn't wait while they piece it together.
>
> Neural Architect takes the raw telemetry and reconstructs the attack chain in seconds. Timeline, MITRE ATT&CK mapping, indicators of compromise, recommended actions, exportable as a STIX 2.1 bundle that drops straight into MISP or OpenCTI.
>
> Built on Gemini 2.5 Flash, with a deterministic preprocessing layer in front of the model so it stays grounded in actual evidence instead of making things up.
>
> Three things I'm happy with:
> – It ships with an eval harness. Most AI security demos don't measure anything.
> – The output is typed (Pydantic) and schema-constrained, so it's actually consumable by other tools.
> – It runs as a Streamlit UI, a FastAPI service, or a CLI — same engine.
>
> Repo, samples, architecture write-up, and eval methodology all here:
> 👉 https://github.com/Ravioli201/neural-architect
>
> Always learning. Tear it apart in the comments.

---

## Draft C — Short / mobile-optimized (if you want it punchy)

> Most SOC work is asking the same question: *what happened?*
>
> So I built Neural Architect: drop in raw logs, get back a reconstructed attack chain mapped to MITRE ATT&CK in seconds.
>
> Built on Gemini 2.5 Flash with deterministic preprocessing so the model stays grounded. Ships with an eval harness, three sample incidents, STIX 2.1 export, and a Streamlit UI.
>
> Open source, MIT.
>
> 👉 https://github.com/Ravioli201/neural-architect
>
> #cybersecurity #DFIR #MITREATTACK

---

## Posting checklist

Before you hit post:

1. **Pin a comment** with the demo video link (LinkedIn deprioritizes posts that send people off-platform; the link in a comment hurts reach less than a link in the post body).
2. **Upload the demo video as native LinkedIn video**, not a YouTube embed. Native video gets ~5x the reach.
3. **Post Tuesday–Thursday, 9–11am your timezone.** Engagement window matters.
4. **First-hour engagement matters most** — message 3–5 people you trust before posting and ask them to engage when it goes up.
5. **Reply to every comment in the first 4 hours** — even just "appreciate it." Comments-by-author count toward the algorithm.
6. **Don't edit the post in the first hour.** Edits suppress reach during the critical window.

## Things to NOT do

- Don't say "revolutionary" or "game-changing" — security people roll their eyes
- Don't claim it's "production-ready" — it's a passion project, own that
- Don't pretend you discovered something — be honest that you're learning out loud
- Don't tag Anthropic / Google / random influencers hoping for a repost — comes across thirsty
- Don't repost it 3 days later if engagement was low — let it breathe
