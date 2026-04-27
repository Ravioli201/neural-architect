# 60-second demo video script

Record this with [Loom](https://loom.com), [Screen Studio](https://screen.studio), or OBS. **No voiceover required** — captions on screen do the talking. Music is optional but a low-key ambient track helps. Don't overdo the cursor movement.

Aim for **55–65 seconds total**. LinkedIn auto-loops anything under 60s, which doubles effective watch time.

---

## Pre-flight

- Use a clean browser window. No bookmark bar, no extensions tab, no notifications.
- Set the Streamlit app to a window size of about **1280×800** so it looks good on mobile feeds.
- Have one of the sample logs already loaded into the textarea so you don't waste seconds typing.
- Hide your real Gemini API key — type it before recording starts, then refresh once on camera so the key dot-mask is visible but you don't show the value.

---

## Storyboard

| Time | Visual | Caption (overlay text) |
|------|--------|------------------------|
| 0:00–0:03 | Hero card filling the screen — "Neural Architect / AI-powered digital forensics" | **"SOC analysts spend hours stitching log events into a story."** |
| 0:03–0:07 | Cursor scrolls down past the textarea showing pasted Sysmon-style logs | **"Drop in raw telemetry —"** |
| 0:07–0:10 | Cursor hits the **🔍 Reconstruct Attack Chain** button | **"— hit one button."** |
| 0:10–0:18 | Status box visible: "Detecting log format… Extracting IOCs… Asking Gemini to reconstruct…" Cuts to results loading. | **"Gemini 2.5 Flash reconstructs the attack chain in seconds."** |
| 0:18–0:25 | The four metric tiles (Incident, Severity, Events, MITRE techniques) appear; cursor pauses on **CRITICAL** | (no caption — let the metrics breathe) |
| 0:25–0:34 | Slow scroll down through the timeline cards — phishing → execution → persistence → credential access → lateral move → impact. MITRE technique IDs visible. | **"Every event mapped to MITRE ATT&CK with rationale."** |
| 0:34–0:40 | Scroll continues to the MITRE coverage bar chart and IOC table | **"IOCs deduplicated, cross-referenced, ready to export."** |
| 0:40–0:48 | Click **🛡️ STIX 2.1 bundle** — file save dialog flashes briefly | **"One-click export to STIX 2.1, Markdown, or JSON."** |
| 0:48–0:55 | Hard cut to the GitHub repo page — README hero visible | **"Open source. MIT. Eval harness included."** |
| 0:55–0:60 | Repo URL fills the screen | **"github.com/Ravioli201/neural-architect"** |

---

## Production notes

- **Cut, don't transition.** Hard cuts read as confident; fades and wipes look amateur.
- **Speed up dead time.** If the model takes 4 seconds, speed that span to 2x. The viewer doesn't care that latency is real — they care about the rhythm.
- **Captions in a single typeface, sentence case, max two lines.** Inter, SF Pro, or Söhne all work. White on a translucent dark pill is the safest readable choice on autoplay-with-no-sound feeds.
- **No music with vocals.** Most viewers watch on mute; for the few who don't, instrumental beats anything with lyrics.
- **End on the URL static for 5 full seconds.** Most viewers screenshot.

---

## If you want a 30s edit too

Same storyboard, drop:
- The hero-card opener (start with the textarea already loaded)
- The MITRE coverage chart
- The export click

Cut directly from "reconstruction complete" to the GitHub repo. 30s versions get higher completion rates and LinkedIn rewards completion.

---

## Asset to embed in the README

Once you've recorded, also export a **3-second silent GIF** of the moment the reconstruction renders (the timeline cards animating in). Drop it at `assets/demo.gif` — the README already references that path. A GIF in the README hero section is the single biggest "this is real" signal a passive viewer gets.
