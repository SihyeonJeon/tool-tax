from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .mcp_stdio import list_mcp_stdio_tools
from .report import grade, summarize


JsonObject = dict[str, Any]


@dataclass(frozen=True)
class MCPConfigServer:
    name: str
    command: list[str]
    source_path: Path
    cwd: Path | None = None
    env: dict[str, str] | None = None
    transport: str = "stdio"


DEFAULT_CONFIG_NAMES = (
    ".mcp.json",
    "mcp.json",
    ".cursor/mcp.json",
    ".vscode/mcp.json",
)


def discover_config_paths(cwd: Path) -> list[Path]:
    return [path for name in DEFAULT_CONFIG_NAMES if (path := cwd / name).exists()]


def _string_map(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): str(item) for key, item in value.items()}


def _server_command(raw: JsonObject) -> list[str] | None:
    command = raw.get("command")
    if not isinstance(command, str) or not command:
        return None
    args = raw.get("args", [])
    if not isinstance(args, list):
        args = []
    return [command, *(str(arg) for arg in args)]


def _server_transport(raw: JsonObject) -> str:
    transport = raw.get("type") or raw.get("transport")
    if transport:
        return str(transport).lower()
    if raw.get("url"):
        return "remote"
    return "stdio"


def load_mcp_config(path: Path) -> tuple[list[MCPConfigServer], list[str]]:
    errors: list[str] = []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [], [f"{path}: {exc}"]
    if not isinstance(payload, dict):
        return [], [f"{path}: root must be a JSON object"]
    servers = payload.get("mcpServers") or payload.get("servers")
    if not isinstance(servers, dict):
        return [], [f"{path}: no mcpServers object found"]
    configs: list[MCPConfigServer] = []
    for name, raw in servers.items():
        if not isinstance(raw, dict):
            errors.append(f"{path}: server {name} must be an object")
            continue
        transport = _server_transport(raw)
        if transport not in {"stdio", "command"}:
            configs.append(
                MCPConfigServer(
                    name=str(name),
                    command=[],
                    source_path=path,
                    transport=transport,
                )
            )
            continue
        command = _server_command(raw)
        if command is None:
            errors.append(f"{path}: server {name} has no command")
            continue
        cwd_value = raw.get("cwd")
        cwd = Path(str(cwd_value)).expanduser() if cwd_value else None
        if cwd is not None and not cwd.is_absolute():
            cwd = (path.parent / cwd).resolve()
        configs.append(
            MCPConfigServer(
                name=str(name),
                command=command,
                source_path=path,
                cwd=cwd,
                env=_string_map(raw.get("env")),
                transport="stdio",
            )
        )
    return configs, errors


def load_configs(paths: list[Path]) -> tuple[list[MCPConfigServer], list[str]]:
    configs: list[MCPConfigServer] = []
    errors: list[str] = []
    for path in paths:
        loaded, load_errors = load_mcp_config(path)
        configs.extend(loaded)
        errors.extend(load_errors)
    return configs, errors


def command_label(command: list[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def server_row(
    config: MCPConfigServer,
    probe: bool,
    timeout: float,
    protocol_version: str,
    verbose: bool,
) -> JsonObject:
    base: JsonObject = {
        "name": config.name,
        "config_path": str(config.source_path),
        "transport": config.transport,
        "command": command_label(config.command) if config.command else "",
    }
    if config.transport != "stdio":
        return {**base, "status": "skipped", "reason": f"unsupported transport: {config.transport}"}
    if not probe:
        return {**base, "status": "configured"}
    records, errors = list_mcp_stdio_tools(
        config.command,
        timeout=timeout,
        protocol_version=protocol_version,
        cwd=config.cwd,
        verbose=verbose,
        env=config.env,
    )
    summary = summarize(records)
    row: JsonObject = {
        **base,
        "status": "ok" if not errors else "error",
        "tool_count": summary.tool_count,
        "total_tax_tokens": summary.total_tax_tokens,
        "total_index_tokens": summary.total_index_tokens,
        "estimated_savings_tokens": summary.estimated_savings_tokens,
        "estimated_savings_percent": round(summary.estimated_savings_percent, 2),
        "worst_tool_tokens": summary.worst_tool_tokens,
        "grade": summary.grade,
        "heaviest_tools": [
            {"name": record.name, "tax_tokens": record.tax_tokens}
            for record in sorted(records, key=lambda item: item.tax_tokens, reverse=True)[:5]
        ],
    }
    if errors:
        row["errors"] = errors
    return row


def doctor_report(
    paths: list[Path],
    probe: bool,
    timeout: float = 10.0,
    protocol_version: str = "2025-06-18",
    verbose: bool = False,
) -> JsonObject:
    configs, errors = load_configs(paths)
    rows = [server_row(config, probe, timeout, protocol_version, verbose) for config in configs]
    total_tax = sum(int(row.get("total_tax_tokens", 0)) for row in rows)
    total_index = sum(int(row.get("total_index_tokens", 0)) for row in rows)
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    error_rows = [row for row in rows if row.get("status") == "error"]
    skipped_rows = [row for row in rows if row.get("status") == "skipped"]
    worst = max((int(row.get("worst_tool_tokens", 0)) for row in rows), default=0)
    return {
        "summary": {
            "config_count": len(paths),
            "server_count": len(rows),
            "probed_count": len(ok_rows) + len(error_rows),
            "skipped_count": len(skipped_rows),
            "error_count": len(error_rows) + len(errors),
            "total_tax_tokens": total_tax,
            "total_index_tokens": total_index,
            "estimated_savings_tokens": max(0, total_tax - total_index),
            "estimated_savings_percent": round(((total_tax - total_index) / total_tax * 100), 2)
            if total_tax
            else 0.0,
            "worst_tool_tokens": worst,
            "grade": grade(total_tax),
        },
        "servers": rows,
        "errors": errors,
    }


def doctor_markdown(payload: JsonObject) -> str:
    summary = payload["summary"]
    lines = [
        "# Tool Tax Doctor",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Configs | {summary['config_count']} |",
        f"| Servers | {summary['server_count']} |",
        f"| Probed | {summary['probed_count']} |",
        f"| Grade | {summary['grade']} |",
        f"| Total tool tax | {summary['total_tax_tokens']:,} est. tokens |",
        f"| Slim index | {summary['total_index_tokens']:,} est. tokens |",
        f"| Slim-index savings | {summary['estimated_savings_tokens']:,} est. tokens ({summary['estimated_savings_percent']:.1f}%) |",
        f"| Worst tool | {summary['worst_tool_tokens']:,} est. tokens |",
        "",
        "## MCP Servers",
        "",
        "| Server | Status | Tools | Tax | Worst | Config |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for row in payload["servers"]:
        lines.append(
            f"| `{row['name']}` | {row['status']} | {row.get('tool_count', 0)} | "
            f"{row.get('total_tax_tokens', 0):,} | {row.get('worst_tool_tokens', 0):,} | "
            f"`{row['config_path']}` |"
        )
    errors = list(payload.get("errors") or [])
    for row in payload["servers"]:
        errors.extend(row.get("errors", []))
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- `{error}`" for error in errors)
    lines.append("")
    return "\n".join(lines)
