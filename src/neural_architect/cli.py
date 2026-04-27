"""Command-line interface.

    $ neural-architect analyze incident.log
    $ neural-architect analyze incident.log --format markdown
    $ neural-architect analyze incident.log --format stix > bundle.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

from neural_architect import __version__
from neural_architect.core.analyzer import Analyzer
from neural_architect.exporters import to_markdown_report, to_stix_bundle
from neural_architect.llm.gemini_client import GeminiUnavailableError


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(
        prog="neural-architect",
        description="AI-powered DFIR. Reconstruct attack chains from raw logs.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_analyze = sub.add_parser("analyze", help="Analyze a log file")
    p_analyze.add_argument("path", type=Path, help="Path to a log file")
    p_analyze.add_argument(
        "--format",
        choices=["json", "markdown", "stix"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    p_analyze.add_argument("--incident-id", help="Optional incident ID")

    args = parser.parse_args(argv)

    if args.cmd == "analyze":
        return _cmd_analyze(args)
    return 1


def _cmd_analyze(args: argparse.Namespace) -> int:
    if not args.path.exists():
        print(f"error: {args.path} does not exist", file=sys.stderr)
        return 2

    raw = args.path.read_text(errors="replace")

    try:
        analyzer = Analyzer()
    except GeminiUnavailableError as e:
        print(f"error: {e}", file=sys.stderr)
        return 3

    try:
        chain = analyzer.analyze(raw, incident_id=args.incident_id)
    except Exception as e:  # noqa: BLE001
        print(f"analysis failed: {e}", file=sys.stderr)
        return 4

    if args.format == "markdown":
        print(to_markdown_report(chain))
    elif args.format == "stix":
        print(to_stix_bundle(chain).serialize(pretty=True))
    else:
        print(json.dumps(chain.model_dump(mode="json"), indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
