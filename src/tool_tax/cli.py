from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from . import __version__
from .benchmark import benchmark_to_json, benchmark_to_markdown, build_benchmark
from .diff import dump_diff_json, to_diff_json, to_diff_markdown
from .doctor import discover_config_paths, doctor_markdown, doctor_report
from .extract import ExtractOptions, extract_tools
from .github_comment import DEFAULT_MARKER, resolve_pr_number, upsert_pr_comment
from .mcp_stdio import list_mcp_stdio_tools
from .mcp_proxy import ToolTaxProxy
from .report import summarize, to_json, to_markdown, write_pack, write_report


def parse_paths(values: list[str]) -> list[Path]:
    return [Path(value) for value in values]


def extract_options(args: argparse.Namespace) -> ExtractOptions:
    return ExtractOptions(
        openapi_tags=tuple(args.tag or ()),
        openapi_paths=tuple(args.path or ()),
        openapi_operations=tuple(args.operation or ()),
    )


def add_openapi_slice_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--tag", action="append", help="only include OpenAPI operations with this tag")
    parser.add_argument("--path", action="append", help="only include OpenAPI paths matching this prefix or glob")
    parser.add_argument("--operation", action="append", help="only include OpenAPI operationId matching this prefix or glob")


def append_step_summary(markdown: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        print("WARNING: GITHUB_STEP_SUMMARY is not set", file=sys.stderr)
        return
    with Path(summary_path).open("a", encoding="utf-8") as fh:
        fh.write(markdown.rstrip() + "\n")


def cmd_scan(args: argparse.Namespace) -> int:
    records, errors = extract_tools(parse_paths(args.paths), extract_options(args))
    payload = to_json(records, errors) if args.format == "json" else to_markdown(records, errors)
    write_report(payload, Path(args.out).resolve() if args.out else None)
    if args.github_step_summary:
        append_step_summary(to_markdown(records, errors))
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


def budget_failed(args: argparse.Namespace, total_tokens: int, worst_tool_tokens: int, grade: str) -> bool:
    if args.max_tokens is not None and total_tokens > args.max_tokens:
        return True
    if args.max_tool_tokens is not None and worst_tool_tokens > args.max_tool_tokens:
        return True
    if getattr(args, "fail_on_grade", None):
        ranks = {"lean": 0, "warm": 1, "expensive": 2, "brutal": 3}
        return ranks[grade] >= ranks[args.fail_on_grade]
    return False


def cmd_mcp(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("ERROR: missing MCP server command after --", file=sys.stderr)
        return 1
    records, errors = list_mcp_stdio_tools(
        command,
        timeout=args.timeout,
        protocol_version=args.protocol_version,
        verbose=args.verbose,
    )
    payload = to_json(records, errors) if args.format == "json" else to_markdown(records, errors)
    write_report(payload, Path(args.out).resolve() if args.out else None)
    if args.github_step_summary:
        append_step_summary(to_markdown(records, errors))
    if args.pack_out:
        write_pack(records, Path(args.pack_out).resolve())
    summary = summarize(records)
    if errors and not records:
        return 1
    failed = budget_failed(args, summary.total_tax_tokens, summary.worst_tool_tokens, summary.grade)
    return 2 if failed else 0


def cmd_proxy(args: argparse.Namespace) -> int:
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        print("ERROR: missing upstream MCP server command after --", file=sys.stderr)
        return 1
    return ToolTaxProxy(command, args.timeout, args.protocol_version, args.call_timeout, args.verbose).serve()


def cmd_doctor(args: argparse.Namespace) -> int:
    paths = (
        [Path(path).expanduser() for path in args.mcp_config]
        if args.mcp_config
        else discover_config_paths(Path.cwd(), include_global=args.include_global)
    )
    if not paths:
        print("ERROR: no MCP config found. Pass --mcp-config PATH.", file=sys.stderr)
        return 1
    payload = doctor_report(
        paths,
        probe=not args.no_probe,
        timeout=args.timeout,
        protocol_version=args.protocol_version,
        verbose=args.verbose,
        project_root=Path.cwd(),
        all_projects=args.all_projects,
    )
    output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n" if args.format == "json" else doctor_markdown(payload)
    write_report(output, Path(args.out).resolve() if args.out else None)
    if args.github_step_summary:
        append_step_summary(doctor_markdown(payload))
    summary = payload["summary"]
    if summary["error_count"] and not any(server.get("status") == "ok" for server in payload["servers"]):
        return 1
    failed = False
    if args.max_tokens is not None and summary["total_tax_tokens"] > args.max_tokens:
        failed = True
    if args.max_server_tokens is not None:
        failed = any(server.get("total_tax_tokens", 0) > args.max_server_tokens for server in payload["servers"])
    if args.fail_on_grade:
        ranks = {"lean": 0, "warm": 1, "expensive": 2, "brutal": 3}
        failed = ranks[summary["grade"]] >= ranks[args.fail_on_grade]
    return 2 if failed else 0


def cmd_diff(args: argparse.Namespace) -> int:
    options = extract_options(args)
    base_records, base_errors = extract_tools([Path(args.base)], options)
    head_records, head_errors = extract_tools([Path(args.head)], options)
    errors = [f"base: {error}" for error in base_errors] + [f"head: {error}" for error in head_errors]
    if args.format == "json":
        payload = to_diff_json(base_records, head_records, errors)
        write_report(dump_diff_json(payload), Path(args.out).resolve() if args.out else None)
    else:
        payload = to_diff_markdown(base_records, head_records, errors)
        write_report(payload, Path(args.out).resolve() if args.out else None)
    if args.github_step_summary:
        append_step_summary(to_diff_markdown(base_records, head_records, errors))
    summary = to_diff_json(base_records, head_records, errors)["summary"]
    failed = False
    if args.fail_on_increase and summary["delta_tax_tokens"] > 0:
        failed = True
    if args.max_delta_tokens is not None and summary["delta_tax_tokens"] > args.max_delta_tokens:
        failed = True
    if args.max_tool_delta_tokens is not None and summary["worst_tool_delta_tokens"] > args.max_tool_delta_tokens:
        failed = True
    return 2 if failed else 0


def cmd_pack(args: argparse.Namespace) -> int:
    records, errors = extract_tools(parse_paths(args.paths), extract_options(args))
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


def cmd_comment_pr(args: argparse.Namespace) -> int:
    repo = args.repo or os.environ.get("GITHUB_REPOSITORY")
    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    pr_number = args.pr or resolve_pr_number()
    report = Path(args.body_file).read_text(encoding="utf-8")
    if args.dry_run:
        print(json.dumps({"repo": repo, "pr": pr_number, "body": report}, ensure_ascii=False, indent=2))
        return 0
    missing = []
    if not repo:
        missing.append("--repo or GITHUB_REPOSITORY")
    if not pr_number:
        missing.append("--pr or pull_request event payload")
    if not token:
        missing.append("--token, GITHUB_TOKEN, or GH_TOKEN")
    if missing:
        print("ERROR: missing " + ", ".join(missing), file=sys.stderr)
        return 1
    result = upsert_pr_comment(repo, pr_number, report, token, args.marker)
    print(f"{result['action']} PR comment: {result['url']}")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    payload = build_benchmark(Path(args.manifest))
    output = benchmark_to_json(payload) if args.format == "json" else benchmark_to_markdown(payload)
    write_report(output, Path(args.out).resolve() if args.out else None)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tool-tax",
        description="Schema budget linter for MCP, OpenAPI, and agent tool catalogs.",
    )
    parser.add_argument("--version", action="version", version=f"tool-tax {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="scan JSON/OpenAPI/tool catalogs")
    scan.add_argument("paths", nargs="+", help="files or directories to scan")
    scan.add_argument("--format", choices=["md", "json"], default="md")
    scan.add_argument("--out", help="write report to file")
    scan.add_argument("--max-tokens", type=int, help="fail if total tool tax is above this")
    scan.add_argument("--max-tool-tokens", type=int, help="fail if any one tool is above this")
    scan.add_argument("--fail-on-grade", choices=["lean", "warm", "expensive", "brutal"])
    scan.add_argument("--github-step-summary", action="store_true", help="append Markdown report to GitHub step summary")
    add_openapi_slice_options(scan)
    scan.set_defaults(func=cmd_scan)

    mcp = sub.add_parser("mcp", help="scan a live MCP stdio server")
    mcp.add_argument("--format", choices=["md", "json"], default="md")
    mcp.add_argument("--out", help="write report to file")
    mcp.add_argument("--pack-out", help="write slim index and schema files from live MCP tools")
    mcp.add_argument("--timeout", type=float, default=10.0, help="seconds to wait for initialize/tools responses")
    mcp.add_argument("--protocol-version", default="2025-06-18", help="MCP protocol version sent at initialize")
    mcp.add_argument("--verbose", action="store_true", help="let upstream MCP server stderr pass through")
    mcp.add_argument("--max-tokens", type=int, help="fail if total tool tax is above this")
    mcp.add_argument("--max-tool-tokens", type=int, help="fail if any one tool is above this")
    mcp.add_argument("--fail-on-grade", choices=["lean", "warm", "expensive", "brutal"])
    mcp.add_argument("--github-step-summary", action="store_true", help="append Markdown report to GitHub step summary")
    mcp.add_argument("command", nargs=argparse.REMAINDER, help="MCP server command after --")
    mcp.set_defaults(func=cmd_mcp)

    proxy = sub.add_parser("proxy", help="run a slim-index MCP stdio proxy")
    proxy.add_argument("--timeout", type=float, default=10.0, help="seconds to wait for upstream initialize/list responses")
    proxy.add_argument("--call-timeout", type=float, default=60.0, help="seconds to wait for upstream tools/call responses")
    proxy.add_argument("--protocol-version", default="2025-06-18", help="MCP protocol version sent upstream")
    proxy.add_argument("--verbose", action="store_true", help="let upstream MCP server stderr pass through")
    proxy.add_argument("command", nargs=argparse.REMAINDER, help="upstream MCP server command after --")
    proxy.set_defaults(func=cmd_proxy)

    doctor = sub.add_parser("doctor", help="inspect MCP configs and report tool-schema tax")
    doctor.add_argument("--mcp-config", action="append", default=[], help="MCP config JSON path; defaults to common project files")
    doctor.add_argument("--include-global", action="store_true", help="also inspect common user-level MCP config files")
    doctor.add_argument("--all-projects", action="store_true", help="include all project entries when reading Claude ~/.claude.json")
    doctor.add_argument("--format", choices=["md", "json"], default="md")
    doctor.add_argument("--out", help="write report to file")
    doctor.add_argument("--no-probe", action="store_true", help="parse configs without executing MCP server commands")
    doctor.add_argument("--timeout", type=float, default=10.0, help="seconds to wait for MCP initialize/tools responses")
    doctor.add_argument("--protocol-version", default="2025-06-18", help="MCP protocol version sent at initialize")
    doctor.add_argument("--verbose", action="store_true", help="let upstream MCP server stderr pass through")
    doctor.add_argument("--max-tokens", type=int, help="fail if total configured MCP tool tax is above this")
    doctor.add_argument("--max-server-tokens", type=int, help="fail if one configured MCP server is above this")
    doctor.add_argument("--fail-on-grade", choices=["lean", "warm", "expensive", "brutal"])
    doctor.add_argument("--github-step-summary", action="store_true", help="append Markdown report to GitHub step summary")
    doctor.set_defaults(func=cmd_doctor)

    diff = sub.add_parser("diff", help="compare base and head tool catalogs")
    diff.add_argument("base", help="base file or directory")
    diff.add_argument("head", help="head file or directory")
    diff.add_argument("--format", choices=["md", "json"], default="md")
    diff.add_argument("--out", help="write diff report to file")
    diff.add_argument("--fail-on-increase", action="store_true", help="fail if total tool tax increases")
    diff.add_argument("--max-delta-tokens", type=int, help="fail if total token delta exceeds this")
    diff.add_argument("--max-tool-delta-tokens", type=int, help="fail if one tool grows more than this")
    diff.add_argument("--github-step-summary", action="store_true", help="append Markdown diff to GitHub step summary")
    add_openapi_slice_options(diff)
    diff.set_defaults(func=cmd_diff)

    pack = sub.add_parser("pack", help="write slim tool index and schema files")
    pack.add_argument("paths", nargs="+", help="files or directories to scan")
    pack.add_argument("--out", required=True, help="output directory")
    pack.add_argument("--ignore-errors", action="store_true")
    add_openapi_slice_options(pack)
    pack.set_defaults(func=cmd_pack)

    comment = sub.add_parser("comment-pr", help="create or update a GitHub PR comment from a report")
    comment.add_argument("--body-file", required=True, help="Markdown report file")
    comment.add_argument("--repo", help="owner/repo, defaults to GITHUB_REPOSITORY")
    comment.add_argument("--pr", type=int, help="pull request number")
    comment.add_argument("--token", help="GitHub token, defaults to GITHUB_TOKEN or GH_TOKEN")
    comment.add_argument("--marker", default=DEFAULT_MARKER, help="hidden marker for updating an existing comment")
    comment.add_argument("--dry-run", action="store_true", help="print resolved comment payload without calling GitHub")
    comment.set_defaults(func=cmd_comment_pr)

    benchmark = sub.add_parser("benchmark", help="summarize multiple scan reports from a manifest")
    benchmark.add_argument("manifest", help="YAML or JSON benchmark manifest")
    benchmark.add_argument("--format", choices=["md", "json"], default="md")
    benchmark.add_argument("--out", help="write benchmark report to file")
    benchmark.set_defaults(func=cmd_benchmark)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
