from __future__ import annotations

import json
import os
import re
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
    source_label: str
    display_command: list[str]
    cwd: Path | None = None
    env: dict[str, str] | None = None
    transport: str = "stdio"
    disabled: bool = False


DEFAULT_CONFIG_NAMES = (
    ".mcp.json",
    "mcp.json",
    ".cursor/mcp.json",
    ".vscode/mcp.json",
)
GLOBAL_CONFIG_NAMES = (
    ".cursor/mcp.json",
    ".claude.json",
    ".cline/mcp.json",
    ".cline/data/settings/cline_mcp_settings.json",
    "Library/Application Support/Code/User/mcp.json",
    "Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
    ".config/Code/User/mcp.json",
    ".config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json",
)
VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def discover_config_paths(cwd: Path, include_global: bool = False, home: Path | None = None) -> list[Path]:
    paths = [path for name in DEFAULT_CONFIG_NAMES if (path := cwd / name).exists()]
    if include_global:
        root = home or Path.home()
        paths.extend(path for name in GLOBAL_CONFIG_NAMES if (path := root / name).exists())
    seen: set[Path] = set()
    unique: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(path)
    return unique


def _string_map(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    return {str(key): str(item) for key, item in value.items()}


def _expand_string(value: str, context_dir: Path, home: Path, redact: bool = False) -> str:
    def replace(match: re.Match[str]) -> str:
        expression = match.group(1)
        if expression == "workspaceFolder":
            return str(context_dir)
        if expression == "workspaceFolderBasename":
            return context_dir.name
        if expression == "userHome":
            return str(home)
        if expression in {"pathSeparator", "/"}:
            return os.sep
        if expression.startswith("env:"):
            name = expression[4:]
            return f"${{{expression}}}" if redact else os.environ.get(name, "")
        if ":-" in expression:
            name, default = expression.split(":-", 1)
            return f"${{{name}}}" if redact and name in os.environ else os.environ.get(name, default)
        return f"${{{expression}}}" if redact and expression in os.environ else os.environ.get(expression, "")

    return VAR_PATTERN.sub(replace, value)


def _expand_list(values: list[str], context_dir: Path, home: Path, redact: bool = False) -> list[str]:
    return [_expand_string(value, context_dir, home, redact=redact) for value in values]


def _server_command(raw: JsonObject, context_dir: Path, home: Path) -> tuple[list[str], list[str]] | None:
    command = raw.get("command")
    if not isinstance(command, str) or not command:
        return None
    args = raw.get("args", [])
    if not isinstance(args, list):
        args = []
    command_parts = [command, *(str(arg) for arg in args)]
    return (
        _expand_list(command_parts, context_dir, home, redact=False),
        _expand_list(command_parts, context_dir, home, redact=True),
    )


def _server_transport(raw: JsonObject) -> str:
    transport = raw.get("type") or raw.get("transport")
    if transport:
        normalized = str(transport).lower()
        if normalized in {"streamablehttp", "streamable-http", "http", "sse"}:
            return "remote"
        return normalized
    if raw.get("url"):
        return "remote"
    return "stdio"


def _context_dir_for_path(path: Path, project_root: Path | None, home: Path) -> Path:
    expanded = path.expanduser()
    parent = expanded.parent
    if expanded.name == "mcp.json" and parent.name in {".cursor", ".vscode", ".cline"}:
        return parent.parent
    if project_root is not None and expanded.resolve().is_relative_to(home.expanduser().resolve()):
        return project_root
    return parent


def _servers_contexts(
    payload: JsonObject,
    path: Path,
    project_root: Path | None,
    all_projects: bool,
    home: Path,
) -> tuple[list[tuple[str, dict[str, Any], Path]], list[str]]:
    contexts: list[tuple[str, dict[str, Any], Path]] = []
    errors: list[str] = []
    root_servers = payload.get("mcpServers") or payload.get("servers")
    if isinstance(root_servers, dict):
        contexts.append((str(path), root_servers, _context_dir_for_path(path, project_root, home)))

    projects = payload.get("projects")
    if isinstance(projects, dict):
        root = project_root.resolve() if project_root is not None else None
        for project_name, raw_project in projects.items():
            if not isinstance(raw_project, dict):
                continue
            project_servers = raw_project.get("mcpServers") or raw_project.get("servers")
            if not isinstance(project_servers, dict):
                continue
            project_path = Path(str(project_name)).expanduser()
            if not project_path.is_absolute():
                project_path = (path.parent / project_path).resolve()
            if not all_projects and root is not None and project_path.resolve() != root:
                continue
            label = f"{path}#projects[{project_name}]"
            contexts.append((label, project_servers, project_path))

    if not contexts and not isinstance(projects, dict):
        errors.append(f"{path}: no mcpServers object found")
    return contexts, errors


def _expanded_env(raw: JsonObject, context_dir: Path, home: Path) -> dict[str, str] | None:
    env = _string_map(raw.get("env"))
    if env is None:
        return None
    return {key: _expand_string(value, context_dir, home) for key, value in env.items()}


def load_mcp_config(
    path: Path,
    project_root: Path | None = None,
    all_projects: bool = False,
    home: Path | None = None,
) -> tuple[list[MCPConfigServer], list[str]]:
    errors: list[str] = []
    home = home or Path.home()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return [], [f"{path}: {exc}"]
    if not isinstance(payload, dict):
        return [], [f"{path}: root must be a JSON object"]
    contexts, context_errors = _servers_contexts(payload, path, project_root, all_projects, home)
    errors.extend(context_errors)
    configs: list[MCPConfigServer] = []
    for source_label, servers, context_dir in contexts:
        for name, raw in servers.items():
            if not isinstance(raw, dict):
                errors.append(f"{source_label}: server {name} must be an object")
                continue
            transport = _server_transport(raw)
            disabled = raw.get("disabled") is True
            if transport not in {"stdio", "command"}:
                configs.append(
                    MCPConfigServer(
                        name=str(name),
                        command=[],
                        source_path=path,
                        source_label=source_label,
                        display_command=[],
                        transport=transport,
                        disabled=disabled,
                    )
                )
                continue
            command_pair = _server_command(raw, context_dir, home)
            if command_pair is None:
                errors.append(f"{source_label}: server {name} has no command")
                continue
            command, display_command = command_pair
            cwd_value = raw.get("cwd")
            cwd = Path(_expand_string(str(cwd_value), context_dir, home)).expanduser() if cwd_value else None
            if cwd is not None and not cwd.is_absolute():
                cwd = (context_dir / cwd).resolve()
            configs.append(
                MCPConfigServer(
                    name=str(name),
                    command=command,
                    source_path=path,
                    source_label=source_label,
                    display_command=display_command,
                    cwd=cwd,
                    env=_expanded_env(raw, context_dir, home),
                    transport="stdio",
                    disabled=disabled,
                )
            )
    return configs, errors


def load_configs(
    paths: list[Path],
    project_root: Path | None = None,
    all_projects: bool = False,
    home: Path | None = None,
) -> tuple[list[MCPConfigServer], list[str]]:
    configs: list[MCPConfigServer] = []
    errors: list[str] = []
    for path in paths:
        loaded, load_errors = load_mcp_config(path, project_root=project_root, all_projects=all_projects, home=home)
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
        "config_path": config.source_label,
        "transport": config.transport,
        "command": command_label(config.display_command) if config.display_command else "",
    }
    if config.disabled:
        return {**base, "status": "disabled", "reason": "disabled in config"}
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
    project_root: Path | None = None,
    all_projects: bool = False,
    home: Path | None = None,
) -> JsonObject:
    configs, errors = load_configs(paths, project_root=project_root, all_projects=all_projects, home=home)
    rows = [server_row(config, probe, timeout, protocol_version, verbose) for config in configs]
    total_tax = sum(int(row.get("total_tax_tokens", 0)) for row in rows)
    total_index = sum(int(row.get("total_index_tokens", 0)) for row in rows)
    ok_rows = [row for row in rows if row.get("status") == "ok"]
    error_rows = [row for row in rows if row.get("status") == "error"]
    skipped_rows = [row for row in rows if row.get("status") in {"skipped", "disabled"}]
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
