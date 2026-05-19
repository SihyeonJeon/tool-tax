#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from tool_tax import __version__  # noqa: E402
from tool_tax.mcp_stdio import JsonObject, MCPStdioClient  # noqa: E402
from tool_tax.tokenize import estimate_tokens  # noqa: E402


DEFAULT_UPSTREAM = ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]


@dataclass
class PromptTurn:
    name: str
    tools: list[JsonObject]
    task: str
    transcript: list[JsonObject]

    def prompt(self) -> str:
        return json.dumps(
            {
                "system": (
                    "You are a minimal MCP agent host. The complete available tool "
                    "catalog is included in every model turn."
                ),
                "task": self.task,
                "tools": self.tools,
                "transcript": self.transcript,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

    def tokens(self) -> int:
        return estimate_tokens(self.prompt())


def as_compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def tool_catalog_tokens(tools: list[JsonObject]) -> int:
    return estimate_tokens(as_compact_json({"tools": tools}))


def result_tokens(result: JsonObject) -> int:
    return estimate_tokens(as_compact_json(result))


def scenario_summary(name: str, turns: list[PromptTurn]) -> JsonObject:
    turn_rows = [{"name": turn.name, "tokens": turn.tokens()} for turn in turns]
    return {
        "case": name,
        "turns": len(turns),
        "total_prompt_tokens": sum(row["tokens"] for row in turn_rows),
        "max_turn_prompt_tokens": max((row["tokens"] for row in turn_rows), default=0),
        "turn_rows": turn_rows,
    }


def compare_case(case: str, direct: JsonObject, proxy: JsonObject) -> JsonObject:
    delta = proxy["total_prompt_tokens"] - direct["total_prompt_tokens"]
    reduction = -delta / direct["total_prompt_tokens"] * 100 if direct["total_prompt_tokens"] else 0.0
    return {
        "case": case,
        "direct_total_prompt_tokens": direct["total_prompt_tokens"],
        "proxy_total_prompt_tokens": proxy["total_prompt_tokens"],
        "delta_tokens": delta,
        "proxy_reduction_percent": round(reduction, 2),
        "direct_turns": direct["turns"],
        "proxy_turns": proxy["turns"],
        "direct_max_turn_prompt_tokens": direct["max_turn_prompt_tokens"],
        "proxy_max_turn_prompt_tokens": proxy["max_turn_prompt_tokens"],
    }


def proxy_call(client: MCPStdioClient, name: str, arguments: JsonObject | None = None) -> JsonObject:
    payload: JsonObject = {"name": name}
    if arguments is not None:
        payload["arguments"] = arguments
    return client.call_tool("tool_tax_call_tool", payload)


def run_benchmark(upstream: list[str], timeout: float, call_timeout: float) -> JsonObject:
    direct = MCPStdioClient(upstream, timeout=timeout, call_timeout=call_timeout)
    proxy_command = [
        sys.executable,
        "-m",
        "tool_tax.mcp_proxy",
        "--timeout",
        str(timeout),
        "--call-timeout",
        str(call_timeout),
        "--",
        *upstream,
    ]
    proxy = MCPStdioClient(proxy_command, timeout=timeout, call_timeout=call_timeout)
    scenarios: list[JsonObject] = []

    try:
        direct_tools = direct.list_tools()
        proxy_tools = proxy.list_tools()

        task_ready = "Do not call a tool. Reply ready."
        direct_startup = scenario_summary(
            "startup_direct",
            [PromptTurn("initial", direct_tools, task_ready, [])],
        )
        proxy_startup = scenario_summary(
            "startup_proxy",
            [PromptTurn("initial", proxy_tools, task_ready, [])],
        )
        scenarios.append(compare_case("startup_only", direct_startup, proxy_startup))

        task_known = "Call list_allowed_directories and answer with the directories."
        direct_known_result = direct.call_tool("list_allowed_directories", {})
        direct_known_transcript = [{"tool": "list_allowed_directories", "result": direct_known_result}]
        direct_known = scenario_summary(
            "known_tool_direct",
            [
                PromptTurn("select_tool", direct_tools, task_known, []),
                PromptTurn("final_answer", direct_tools, task_known, direct_known_transcript),
            ],
        )
        proxy_known_result = proxy_call(proxy, "list_allowed_directories", {})
        proxy_known_transcript = [
            {
                "tool": "tool_tax_call_tool",
                "arguments": {"name": "list_allowed_directories", "arguments": {}},
                "result": proxy_known_result,
            }
        ]
        proxy_known = scenario_summary(
            "known_tool_proxy",
            [
                PromptTurn("select_tool", proxy_tools, task_known, []),
                PromptTurn("final_answer", proxy_tools, task_known, proxy_known_transcript),
            ],
        )
        scenarios.append(compare_case("known_tool_call", direct_known, proxy_known))

        task_discover = "Find the tool that lists allowed directories, call it, and answer with the directories."
        direct_discover_result = direct.call_tool("list_allowed_directories", {})
        direct_discover_transcript = [{"tool": "list_allowed_directories", "result": direct_discover_result}]
        direct_discover = scenario_summary(
            "discover_direct",
            [
                PromptTurn("select_tool", direct_tools, task_discover, []),
                PromptTurn("final_answer", direct_tools, task_discover, direct_discover_transcript),
            ],
        )
        proxy_index = proxy.call_tool("tool_tax_list_tools", {})
        proxy_discover_result = proxy_call(proxy, "list_allowed_directories", {})
        proxy_discover_transcript = [
            {"tool": "tool_tax_list_tools", "result": proxy_index},
            {
                "tool": "tool_tax_call_tool",
                "arguments": {"name": "list_allowed_directories", "arguments": {}},
                "result": proxy_discover_result,
            },
        ]
        proxy_discover = scenario_summary(
            "discover_proxy",
            [
                PromptTurn("list_upstream_tools", proxy_tools, task_discover, []),
                PromptTurn("select_tool", proxy_tools, task_discover, proxy_discover_transcript[:1]),
                PromptTurn("final_answer", proxy_tools, task_discover, proxy_discover_transcript),
            ],
        )
        scenarios.append(compare_case("discover_then_call", direct_discover, proxy_discover))

        return {
            "date": date.today().isoformat(),
            "tool_tax_version": __version__,
            "benchmark": "naive-mcp-host",
            "upstream_command": upstream,
            "method": (
                "Simulates a minimal MCP host that includes the complete visible "
                "tool catalog in every model prompt turn."
            ),
            "direct_tool_count": len(direct_tools),
            "proxy_tool_count": len(proxy_tools),
            "direct_catalog_tokens": tool_catalog_tokens(direct_tools),
            "proxy_catalog_tokens": tool_catalog_tokens(proxy_tools),
            "direct_known_result_tokens": result_tokens(direct_known_result),
            "proxy_known_result_tokens": result_tokens(proxy_known_result),
            "scenarios": scenarios,
        }
    finally:
        direct.close()
        proxy.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark a naive MCP host with direct vs tool-tax proxy tools.")
    parser.add_argument("--out", type=Path, help="write JSON summary to this path")
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--call-timeout", type=float, default=30.0)
    parser.add_argument("command", nargs=argparse.REMAINDER, help="upstream MCP command after --")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    upstream = list(args.command)
    if upstream and upstream[0] == "--":
        upstream = upstream[1:]
    payload = run_benchmark(upstream or DEFAULT_UPSTREAM, args.timeout, args.call_timeout)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
