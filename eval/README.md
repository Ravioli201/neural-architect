# Evaluation harness

This is the part most LLM demos skip. We don't.

## How it works

1. Each sample in `data/samples/` has a matching `eval/golden/<name>.json`
   that lists the MITRE techniques a competent analyst would expect to see
   in the reconstruction, plus the expected severity.
2. `eval/benchmark.py` runs the analyzer against every sample and computes
   precision, recall, and F1 against the golden labels.
3. Scoring defaults to **parent-technique level** (T1566.001 counts as a
   hit for T1566) because sub-technique granularity is where models tend
   to be optimistic. Use `--strict` to score sub-techniques exactly.
4. Latency is measured per-sample so we can spot regressions when prompts
   change.

## Run it

```bash
# single run
python -m eval.benchmark

# average over 3 runs (LLM output isn't deterministic)
python -m eval.benchmark --runs 3

# strict sub-technique scoring
python -m eval.benchmark --strict
```

Results are written to `eval/results/latest.json`.

## What we're measuring

- **Precision** — of the techniques the model called out, how many were
  actually expected? High precision means low false-positive rate.
- **Recall** — of the techniques an analyst expected, how many did the
  model find? High recall means the model isn't missing the obvious.
- **F1** — harmonic mean. The single number to watch.
- **Severity match** — a coarse sanity check; ransomware shouldn't come
  back as "low."

## Caveats

- The samples are synthetic and small. This is a smoke test, not a NIST
  benchmark. Treat results as "is the pipeline working?" not "is the
  model production-ready?"
- LLM output is non-deterministic. Use `--runs 3` (or more) for stable
  numbers.
- Adding more golden samples is the highest-leverage way to make this
  more meaningful — PRs welcome.
