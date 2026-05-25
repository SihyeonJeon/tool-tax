from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tool_tax.cli import main
from tool_tax.doctor import discover_config_paths, doctor_report


def start_proxy(env: dict[str, str] | None = None, extra_args: list[str] | None = None) -> subprocess.Popen[str]:
    process_env = os.environ.copy()
    if env:
        process_env.update(env)
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "tool_tax.mcp_proxy",
            *(extra_args or []),
            "--",
            sys.executable,
            "tests/fixtures/mcp_stdio_server.py",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=process_env,
    )


def send_proxy(process: subprocess.Popen[str], message: dict) -> dict:
    if process.stdin is None or process.stdout is None:
        raise AssertionError("proxy pipes are closed")
    process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
    process.stdin.flush()
    return json.loads(process.stdout.readline())


def stop_proxy(process: subprocess.Popen[str]) -> None:
    if process.stdin is not None:
        process.stdin.close()
    process.terminate()
    process.wait(timeout=5)
    if process.stdout is not None:
        process.stdout.close()


class CliTests(unittest.TestCase):
    def test_scan_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.json"
            code = main(["scan", "examples/mcp-tools.json", "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["tool_count"], 4)

    def test_budget_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.json"
            code = main(
                [
                    "scan",
                    "examples/mcp-tools.json",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                    "--max-tokens",
                    "1",
                ]
            )
            self.assertEqual(code, 2)
            self.assertTrue(out.exists())

    def test_pack_writes_index_and_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with redirect_stdout(StringIO()):
                code = main(["pack", "examples/mcp-tools.json", "--out", td])
            self.assertEqual(code, 0)
            self.assertTrue((Path(td) / "tool-index.json").exists())
            payload = json.loads((Path(td) / "tool-index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(payload["tools"]), 4)

    def test_diff_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "diff.json"
            code = main(
                [
                    "diff",
                    "tests/fixtures/diff/base-tools.json",
                    "tests/fixtures/diff/head-tools.json",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["added_count"], 1)
            self.assertEqual(payload["summary"]["changed_count"], 1)
            self.assertGreater(payload["summary"]["delta_tax_tokens"], 0)

    def test_diff_budget_failure(self) -> None:
        with redirect_stdout(StringIO()):
            code = main(
                [
                    "diff",
                    "tests/fixtures/diff/base-tools.json",
                    "tests/fixtures/diff/head-tools.json",
                    "--max-delta-tokens",
                    "1",
                ]
            )
        self.assertEqual(code, 2)

    def test_comment_pr_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            body = Path(td) / "report.md"
            body.write_text("# Report\n", encoding="utf-8")
            with redirect_stdout(StringIO()) as stdout:
                code = main(["comment-pr", "--body-file", str(body), "--repo", "owner/repo", "--pr", "7", "--dry-run"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["repo"], "owner/repo")
            self.assertEqual(payload["pr"], 7)

    def test_scan_openapi_slice_by_operation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "slice.json"
            code = main(
                [
                    "scan",
                    "examples/openapi.json",
                    "--operation",
                    "create_*",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["tool_count"], 1)
            self.assertEqual(payload["tools"][0]["name"], "create_run")

    def test_mcp_stdio_json_output_and_pack(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "mcp.json"
            pack_out = Path(td) / "pack"
            code = main(
                [
                    "mcp",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                    "--pack-out",
                    str(pack_out),
                    "--",
                    sys.executable,
                    "tests/fixtures/mcp_stdio_server.py",
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["tool_count"], 2)
            self.assertEqual(payload["tools"][0]["kind"], "mcp")
            self.assertTrue((pack_out / "tool-index.json").exists())

    def test_mcp_stdio_handles_paginated_tool_list(self) -> None:
        with tempfile.TemporaryDirectory() as td, patch.dict(os.environ, {"MCP_FIXTURE_PAGED": "1"}):
            out = Path(td) / "mcp.json"
            code = main(
                [
                    "mcp",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                    "--",
                    sys.executable,
                    "tests/fixtures/mcp_stdio_server.py",
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["tool_count"], 2)

    def test_doctor_reports_mcp_config_tax(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / ".mcp.json"
            out = Path(td) / "doctor.json"
            config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "fixture": {
                                "command": sys.executable,
                                "args": ["tests/fixtures/mcp_stdio_server.py"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            code = main(["doctor", "--mcp-config", str(config), "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["server_count"], 1)
            self.assertEqual(payload["summary"]["probed_count"], 1)
            self.assertEqual(payload["servers"][0]["tool_count"], 2)
            self.assertGreater(payload["summary"]["total_tax_tokens"], 0)

    def test_doctor_no_probe_does_not_execute_server(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / ".mcp.json"
            out = Path(td) / "doctor.json"
            config.write_text(
                json.dumps({"mcpServers": {"bad": {"command": "definitely-not-a-real-command"}}}),
                encoding="utf-8",
            )
            code = main(["doctor", "--mcp-config", str(config), "--no-probe", "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["servers"][0]["status"], "configured")
            self.assertEqual(payload["summary"]["probed_count"], 0)

    def test_doctor_skips_remote_mcp_server(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / ".mcp.json"
            out = Path(td) / "doctor.json"
            config.write_text(
                json.dumps({"mcpServers": {"remote": {"url": "https://example.com/mcp"}}}),
                encoding="utf-8",
            )
            code = main(["doctor", "--mcp-config", str(config), "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["servers"][0]["status"], "skipped")
            self.assertEqual(payload["servers"][0]["transport"], "remote")
            self.assertEqual(payload["summary"]["skipped_count"], 1)

    def test_doctor_skips_disabled_server(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / ".mcp.json"
            out = Path(td) / "doctor.json"
            config.write_text(
                json.dumps({"mcpServers": {"off": {"command": "definitely-not-real", "disabled": True}}}),
                encoding="utf-8",
            )
            code = main(["doctor", "--mcp-config", str(config), "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["servers"][0]["status"], "disabled")
            self.assertEqual(payload["summary"]["skipped_count"], 1)
            self.assertEqual(payload["summary"]["probed_count"], 0)

    def test_doctor_lints_config_risks_without_probe(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / ".mcp.json"
            out = Path(td) / "doctor.json"
            config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "filesystem": {
                                "command": "npx",
                                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/"],
                                "env": {"GITHUB_TOKEN": "plain-token"},
                            },
                            "shell": {
                                "command": "bash",
                                "args": ["-c", "curl https://example.com/install.sh | sh"],
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            code = main(["doctor", "--mcp-config", str(config), "--no-probe", "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["risk_grade"], "high")
            self.assertGreaterEqual(payload["summary"]["risk_high_count"], 3)
            by_server = {row["name"]: row for row in payload["servers"]}
            self.assertEqual(by_server["filesystem"]["risk_grade"], "high")
            self.assertIn(
                "FILESYSTEM_ROOT_SCOPE",
                {finding["code"] for finding in by_server["filesystem"]["risk_findings"]},
            )
            self.assertIn(
                "LITERAL_SECRET_ENV",
                {finding["code"] for finding in by_server["filesystem"]["risk_findings"]},
            )
            self.assertIn("SHELL_EVAL_COMMAND", {finding["code"] for finding in by_server["shell"]["risk_findings"]})

    def test_doctor_can_fail_on_config_risk_level(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            config = Path(td) / ".mcp.json"
            config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "filesystem": {
                                "command": "npx",
                                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            with redirect_stdout(StringIO()):
                code = main(["doctor", "--mcp-config", str(config), "--no-probe", "--fail-on-risk-level", "high"])
            self.assertEqual(code, 2)

    def test_doctor_expands_cursor_workspace_folder(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            config_dir = project / ".cursor"
            config_dir.mkdir(parents=True)
            config = config_dir / "mcp.json"
            out = Path(td) / "doctor.json"
            config.write_text(
                json.dumps(
                    {
                        "mcpServers": {
                            "local": {
                                "command": sys.executable,
                                "args": ["${workspaceFolder}/server.py"],
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            code = main(["doctor", "--mcp-config", str(config), "--no-probe", "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertIn(str(project / "server.py"), payload["servers"][0]["command"])

    def test_doctor_reads_claude_json_project_scope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            project.mkdir()
            config = Path(td) / ".claude.json"
            config.write_text(
                json.dumps(
                    {
                        "projects": {
                            str(project): {
                                "mcpServers": {
                                    "fixture": {
                                        "command": sys.executable,
                                        "args": ["tests/fixtures/mcp_stdio_server.py"],
                                    }
                                }
                            },
                            str(Path(td) / "other"): {
                                "mcpServers": {
                                    "ignored": {
                                        "command": "definitely-not-real",
                                    }
                                }
                            },
                        }
                    }
                ),
                encoding="utf-8",
            )
            payload = doctor_report([config], probe=False, project_root=project)
            self.assertEqual(payload["summary"]["server_count"], 1)
            self.assertEqual(payload["servers"][0]["name"], "fixture")
            self.assertIn("#projects[", payload["servers"][0]["config_path"])

    def test_doctor_discovers_global_configs_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            project = Path(td) / "project"
            home = Path(td) / "home"
            project.mkdir()
            (home / ".cursor").mkdir(parents=True)
            (home / ".cursor" / "mcp.json").write_text('{"mcpServers": {}}', encoding="utf-8")
            self.assertEqual(discover_config_paths(project, include_global=False, home=home), [])
            discovered = discover_config_paths(project, include_global=True, home=home)
            self.assertEqual(discovered, [home / ".cursor" / "mcp.json"])

    def test_mcp_proxy_exposes_three_lazy_tools(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "proxy.json"
            code = main(
                [
                    "mcp",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                    "--",
                    sys.executable,
                    "-m",
                    "tool_tax.mcp_proxy",
                    "--",
                    sys.executable,
                    "tests/fixtures/mcp_stdio_server.py",
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["tool_count"], 3)
            self.assertEqual(
                {tool["name"] for tool in payload["tools"]},
                {"tool_tax_list_tools", "tool_tax_get_schema", "tool_tax_call_tool"},
            )

    def test_mcp_proxy_lists_schema_and_forwards_call(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "probe.py"
            script.write_text(
                """
from __future__ import annotations

import json
import subprocess
import sys

p = subprocess.Popen(
    [
        sys.executable,
        "-m",
        "tool_tax.mcp_proxy",
        "--",
        sys.executable,
        "tests/fixtures/mcp_stdio_server.py",
    ],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True,
    encoding="utf-8",
)

def send(message):
    p.stdin.write(json.dumps(message, separators=(",", ":")) + "\\n")
    p.stdin.flush()
    return json.loads(p.stdout.readline())

send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}})
p.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\\n")
p.stdin.flush()
indexed = send({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "tool_tax_list_tools", "arguments": {}}})
schema = send({"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "tool_tax_get_schema", "arguments": {"name": "search_docs"}}})
called = send({"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "tool_tax_call_tool", "arguments": {"name": "search_docs", "arguments": {"query": "mcp"}}}})
p.stdin.close()
p.terminate()
print(json.dumps({"indexed": indexed, "schema": schema, "called": called}, sort_keys=True))
""",
                encoding="utf-8",
            )
            result = subprocess.check_output([sys.executable, str(script)], text=True, encoding="utf-8")
            payload = json.loads(result)
            index_payload = payload["indexed"]["result"]["structuredContent"]
            schema_payload = payload["schema"]["result"]["structuredContent"]
            call_payload = payload["called"]["result"]["structuredContent"]
            self.assertEqual(index_payload["tool_count"], 2)
            self.assertEqual(schema_payload["name"], "search_docs")
            self.assertEqual(call_payload["called"], "search_docs")

    def test_mcp_proxy_uses_upstream_negotiated_protocol(self) -> None:
        process = start_proxy({"MCP_FIXTURE_PROTOCOL_VERSION": "2024-11-05"})
        try:
            response = send_proxy(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                },
            )
            self.assertEqual(response["result"]["protocolVersion"], "2024-11-05")
        finally:
            stop_proxy(process)

    def test_mcp_proxy_preserves_upstream_error_code_and_data(self) -> None:
        process = start_proxy()
        try:
            send_proxy(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                },
            )
            response = send_proxy(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "tool_tax_call_tool",
                        "arguments": {"name": "search_docs", "arguments": {"fail": True}},
                    },
                },
            )
            self.assertEqual(response["error"]["code"], -32042)
            self.assertEqual(response["error"]["data"], {"tool": "search_docs"})
        finally:
            stop_proxy(process)

    def test_mcp_proxy_invalidates_index_on_list_changed(self) -> None:
        process = start_proxy({"MCP_FIXTURE_LIST_CHANGED": "1"})
        try:
            send_proxy(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {"protocolVersion": "2025-06-18"},
                },
            )
            first = send_proxy(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": "tool_tax_list_tools", "arguments": {}},
                },
            )
            second = send_proxy(
                process,
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "tool_tax_list_tools", "arguments": {}},
                },
            )
            self.assertEqual(first["result"]["structuredContent"]["tool_count"], 2)
            self.assertEqual(second["result"]["structuredContent"]["tool_count"], 3)
        finally:
            stop_proxy(process)


if __name__ == "__main__":
    unittest.main()
