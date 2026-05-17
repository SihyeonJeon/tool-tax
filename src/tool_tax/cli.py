from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .extract import extract_tools
from .report import summarize, to_json, to_markdown, write_pack, write_report


def parse_paths(values: list[str]) -> list[Path]:
    return [Path(value) for value in values]


def cmd_scan(args: argparse.Namespace) -> int:
    records, errors = extract_tools(parse_paths(args.paths))
    payload = to_json(records, errors) if args.format == "json" else to_markdown(records, errors)
    write_report(payload, Path(args.out).resolve() if args.out else None)
    summary = summarize(records)
    failed = False
    if args.max_tokens is not None and summary.total_tax_tokens > args.max_tokens:
        failed = True
    if args.max_tool_tokens is not None and summary.worst_tool_tokens > args.max_tool_tokens:
        failed = True
    if args.fail_on_grade:
        ranks = {"lean": 0, "warm": 1, "expensive": 2, "brutal": 3}
        failed = ranks[summary.grade] >= ranks[args.fail_on_grade]
    return 2 if failed else 0


def cmd_pack(args: argparse.Namespace) -> int:
    records, errors = extract_tools(parse_paths(args.paths))
    if errors and not args.ignore_errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    write_pack(records, Path(args.out).resolve())
    summary = summarize(records)
    print(
        f"packed {summary.tool_count} tools: "
        f"{summary.total_tax_tokens:,} -> {summary.total_index_tokens:,} est. tokens "
        f"({summary.estimated_savings_percent:.1f}% smaller)"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tool-tax",
        description="Measure the hidden token bill of MCP and agent tool catalogs.",
    )
    parser.add_argument("--version", action="version", version=f"tool-tax {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan JSON/YAML/OpenAPI/tool catalogs")
    scan.add_argument("paths", nargs="+", help="files or directories to scan")
    scan.add_argument("--format", choices=["md", "json"], default="md")
    scan.add_argument("--out", help="write report to file")
    scan.add_argument("--max-tokens", type=int, help="fail if total tool tax is above this")
    scan.add_argument("--max-tool-tokens", type=int, help="fail if any one tool is above this")
    scan.add_argument("--fail-on-grade", choices=["lean", "warm", "expensive", "brutal"])
    scan.set_defaults(func=cmd_scan)

    pack = sub.add_parser("pack", help="write slim tool index and schema files")
    pack.add_argument("paths", nargs="+", help="files or directories to scan")
    pack.add_argument("--out", required=True, help="output directory")
    pack.add_argument("--ignore-errors", action="store_true")
    pack.set_defaults(func=cmd_pack)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
