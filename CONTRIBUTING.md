# Contributing to Neural Architect

Thanks for considering a contribution. This project is an analyst-augmentation tool, so the bar for changes is correctness and clarity over cleverness - a wrong reconstruction is worse than no reconstruction.

## What's especially welcome

- **Additional golden samples for the eval harness.** New attack scenarios with hand-labeled MITRE techniques. See [`eval/golden/`](eval/golden/) for the schema.
- **Additional log-format parsers.** Sysmon EVTX, CrowdStrike, Defender, Okta, AWS CloudTrail - anything common in real SOCs. Add them in [`src/neural_architect/core/log_parser.py`](src/neural_architect/core/log_parser.py) and wire them into `_PARSERS`.
- **Improvements to the analyst system prompt.** The model's output quality is dominated by the system prompt in [`src/neural_architect/llm/prompts.py`](src/neural_architect/llm/prompts.py). Better prompts that reduce hallucination on sparse logs are very welcome.
- **Bug fixes**, especially anything that produces a wrong `AttackChain` from valid input.

## What's a harder sell

- New UI features that aren't backed by an analyst use case.
- Pulling in a heavy dependency for something a dozen lines of stdlib could do.
- Changes that make the eval harness less rigorous.

## Development setup

```bash
git clone https://github.com/Ravioli201/neural-architect
cd neural-architect

python -m venv .venv
source .venv/bin/activate          # macOS / Linux
# .venv\Scripts\activate           # Windows

pip install -r requirements.txt

cp .env.example .env
# Add your Gemini API key
```

Run the test suite before opening a PR:

```bash
PYTHONPATH=src pytest
ruff check src tests
```

If you change anything in `src/neural_architect/core/` or `src/neural_architect/llm/`, please also run the eval harness on the bundled samples and include the result in your PR description:

```bash
python -m eval.benchmark --runs 3
```

## PR checklist

- [ ] `pytest` passes
- [ ] `ruff check src tests` passes
- [ ] New or modified parsers / extractors have tests in [`tests/`](tests/)
- [ ] Public-facing changes are reflected in the README
- [ ] If you changed prompts, eval results are in the PR description
- [ ] No real victim data, real customer logs, or real IOCs in samples or tests - synthetic only

## Reporting bugs

Open an issue with:

- a minimal log snippet that reproduces the problem (sanitize first - no real IOCs)
- the `AttackChain` JSON output (or the error / traceback)
- expected vs. actual behavior

## Security issues

For anything that could be exploited (prompt-injection escaping the analyst sandbox, log payloads that crash the service, secrets exposure, etc.) - please **do not** open a public issue. See [`SECURITY.md`](SECURITY.md).

## License

By contributing, you agree your contributions will be licensed under the project's [MIT License](LICENSE).