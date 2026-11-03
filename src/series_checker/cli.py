"""Command-line interface for the series consistency checker."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .detector import detect_all, detect_characters, detect_places, detect_timeline
from .models import Finding


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="series-checker",
        description=(
            "Check a manuscript file for inconsistent character names, "
            "places, and timeline details. Local-first: no keys, no network."
        ),
    )
    parser.add_argument(
        "file",
        help="Path to the manuscript text file to check.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--characters",
        action="store_true",
        help="Only check character name consistency.",
    )
    group.add_argument(
        "--places",
        action="store_true",
        help="Only check place name consistency.",
    )
    group.add_argument(
        "--timeline",
        action="store_true",
        help="Only check timeline/date consistency.",
    )
    group.add_argument(
        "--all",
        action="store_true",
        help="Run all checks (default).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit findings as JSON instead of human-readable text.",
    )
    return parser


def _format_finding(finding: Finding) -> str:
    return (
        f"[{finding.kind}] line {finding.line}: {finding.detail}\n"
        f"      suggestion: {finding.suggestion}"
    )


def run_checks(text: str, checks: List[str]) -> List[Finding]:
    findings: List[Finding] = []
    if "characters" in checks:
        findings.extend(detect_characters(text))
    if "places" in checks:
        findings.extend(detect_places(text))
    if "timeline" in checks:
        findings.extend(detect_timeline(text))
    return findings


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        with open(args.file, "r", encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"error: cannot read {args.file}: {exc}", file=sys.stderr)
        return 2

    checks = ["characters", "places", "timeline"]
    if args.characters:
        checks = ["characters"]
    elif args.places:
        checks = ["places"]
    elif args.timeline:
        checks = ["timeline"]

    findings = run_checks(text, checks)

    if args.json:
        import json

        print(json.dumps([f.to_dict() for f in findings], indent=2))
    else:
        if not findings:
            print(f"{args.file}: no consistency conflicts found.")
        else:
            print(f"{args.file}: {len(findings)} consistency conflict(s) found:\n")
            for finding in findings:
                print(_format_finding(finding))
                print()

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
