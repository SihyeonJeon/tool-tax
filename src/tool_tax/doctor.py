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
    display_env: dict[str, str] | None = None
    context_dir: Path | None = None
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
SENSITIVE_ENV_PATTERN = re.compile(
    r"(TOKEN|SECRET|PASSWORD|PASS|API[_-]?KEY|CREDENTIAL|AUTH|PRIVATE|SESSION|COOKIE)",
    re.IGNORECASE,
)
RISK_RANKS = {"none": 0, "low": 1, "medium": 2, "high": 3}
SHELL_COMMANDS = {"sh", "bash", "zsh", "fish", "cmd", "powershell", "pwsh"}
REMOTE_PACKAGE_RUNNERS = {"npx", "bunx", "uvx", "pipx"}


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


def _display_env(raw: JsonObject, context_dir: Path, home: Path) -> dict[str, str] | None:
    env = _string_map(raw.get("env"))
    if env is None:
        return None
    return {key: _expand_string(value, context_dir, home, redact=True) for key, value in env.items()}


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
                        context_dir=context_dir,
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
                    display_env=_display_env(raw, context_dir, home),
                    context_dir=context_dir,
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


def lint_config_risks(config: MCPConfigServer, home: Path | None = None) -> list[JsonObject]:
    if config.disabled:
        return []
    findings: list[JsonObject] = []
    if config.transport != "stdio":
        return findings
    home = home or Path.home()
    findings.extend(_lint_env(config))
    findings.extend(_lint_command(config))
    findings.extend(_lint_filesystem_scope(config, home))
    return findings


def risk_grade(findings: list[JsonObject]) -> str:
    if not findings:
        return "none"
    return max((str(finding["severity"]) for finding in findings), key=lambda item: RISK_RANKS[item])


def _risk(
    code: str,
    severity: str,
    message: str,
    *,
    evidence: str | None = None,
) -> JsonObject:
    out: JsonObject = {
        "code": code,
        "severity": severity,
        "message": message,
    }
    if evidence:
        out["evidence"] = evidence
    return out


def _lint_env(config: MCPConfigServer) -> list[JsonObject]:
    env = config.display_env or {}
    findings: list[JsonObject] = []
    for key, value in env.items():
        if not SENSITIVE_ENV_PATTERN.search(key):
            continue
        evidence = f"env.{key}"
        if value and "${" not in value:
            findings.append(
                _risk(
                    "LITERAL_SECRET_ENV",
                    "high",
                    "sensitive environment variable appears to be stored as a literal config value",
                    evidence=evidence,
                )
            )
        else:
            findings.append(
                _risk(
                    "SENSITIVE_ENV_FORWARD",
                    "medium",
                    "server receives a sensitive environment variable",
                    evidence=evidence,
                )
            )
    return findings


def _lint_command(config: MCPConfigServer) -> list[JsonObject]:
    command = config.display_command or config.command
    if not command:
        return []
    executable = Path(command[0]).name.lower()
    findings: list[JsonObject] = []
    if executable in SHELL_COMMANDS and _uses_shell_eval(command):
        findings.append(
            _risk(
                "SHELL_EVAL_COMMAND",
                "high",
                "server command runs through a shell evaluation flag",
                evidence=command_label(command[:3]),
            )
        )
        shell_script = " ".join(command[2:])
        if _has_shell_chain(shell_script):
            findings.append(
                _risk(
                    "SHELL_CHAIN_COMMAND",
                    "high",
                    "shell command contains chaining or pipe syntax",
                    evidence=_clip(shell_script),
                )
            )
    if executable in REMOTE_PACKAGE_RUNNERS:
        package = _runner_package(command)
        if package and not _package_is_pinned(package):
            findings.append(
                _risk(
                    "UNPINNED_PACKAGE_RUNNER",
                    "medium",
                    f"{executable} launches an unpinned package",
                    evidence=package,
                )
            )
    return findings


def _lint_filesystem_scope(config: MCPConfigServer, home: Path) -> list[JsonObject]:
    command = config.command
    display = config.display_command or command
    joined = " ".join(display).lower()
    if "filesystem" not in joined and "file-system" not in joined:
        return []
    findings: list[JsonObject] = []
    context_dir = (config.context_dir or config.source_path.parent).expanduser().resolve()
    home_resolved = home.expanduser().resolve()
    for raw in command[1:]:
        if raw.startswith("-"):
            continue
        path = _path_candidate(raw)
        if path is None:
            continue
        label = _matching_display_arg(raw, command, display)
        if path == Path("/"):
            findings.append(
                _risk(
                    "FILESYSTEM_ROOT_SCOPE",
                    "high",
                    "filesystem server is scoped to the root directory",
                    evidence=label,
                )
            )
        elif path == home_resolved:
            findings.append(
                _risk(
                    "FILESYSTEM_HOME_SCOPE",
                    "high",
                    "filesystem server is scoped to the user home directory",
                    evidence=label,
                )
            )
        elif path == context_dir:
            findings.append(
                _risk(
                    "FILESYSTEM_WORKSPACE_SCOPE",
                    "medium",
                    "filesystem server is scoped to the whole workspace",
                    evidence=label,
                )
            )
    return findings


def _uses_shell_eval(command: list[str]) -> bool:
    flags = {part.lower() for part in command[1:3]}
    return bool(flags & {"-c", "/c", "-command", "-encodedcommand"})


def _has_shell_chain(value: str) -> bool:
    return any(token in value for token in ("|", "&&", "||", ";", "$(", "`"))


def _runner_package(command: list[str]) -> str | None:
    for arg in command[1:]:
        if arg == "--":
            continue
        if arg.startswith("-"):
            continue
        return arg
    return None


def _package_is_pinned(package: str) -> bool:
    if package.startswith("@"):
        parts = package.split("/")
        return len(parts) >= 2 and "@" in parts[-1]
    return "@" in package


def _path_candidate(value: str) -> Path | None:
    if value in {".", "~"}:
        return Path(value).expanduser().resolve()
    if value.startswith("~/"):
        return Path(value).expanduser().resolve()
    path = Path(value).expanduser()
    if not path.is_absolute():
        return None
    return path.resolve()


def _matching_display_arg(raw: str, command: list[str], display: list[str]) -> str:
    try:
        index = command.index(raw)
    except ValueError:
        return raw
    if index < len(display):
        return display[index]
    return raw


def _clip(value: str, max_len: int = 96) -> str:
    return value if len(value) <= max_len else value[: max_len - 3] + "..."


def server_row(
    config: MCPConfigServer,
    probe: bool,
    timeout: float,
    protocol_version: str,
    verbose: bool,
) -> JsonObject:
    risks = lint_config_risks(config)
    base: JsonObject = {
        "name": config.name,
        "config_path": config.source_label,
        "transport": config.transport,
        "command": command_label(config.display_command) if config.display_command else "",
        "risk_count": len(risks),
        "risk_grade": risk_grade(risks),
        "risk_findings": risks,
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
    risk_counts = {
        level: sum(1 for row in rows for finding in row.get("risk_findings", []) if finding.get("severity") == level)
        for level in ("low", "medium", "high")
    }
    risk_count = sum(risk_counts.values())
    max_risk = max((str(row.get("risk_grade", "none")) for row in rows), key=lambda item: RISK_RANKS[item], default="none")
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
            "risk_count": risk_count,
            "risk_low_count": risk_counts["low"],
            "risk_medium_count": risk_counts["medium"],
            "risk_high_count": risk_counts["high"],
            "risk_grade": max_risk,
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
        f"| Config risks | {summary['risk_count']} ({summary['risk_grade']}) |",
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
    risk_rows = [
        (row, finding)
        for row in payload["servers"]
        for finding in row.get("risk_findings", [])
    ]
    if risk_rows:
        lines.extend(
            [
                "",
                "## Config Risks",
                "",
                "| Server | Severity | Code | Finding |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row, finding in risk_rows:
            evidence = f" `{_md_cell(finding['evidence'])}`" if finding.get("evidence") else ""
            lines.append(
                f"| `{row['name']}` | {finding['severity']} | `{finding['code']}` | "
                f"{_md_cell(finding['message'])}{evidence} |"
            )
    errors = list(payload.get("errors") or [])
    for row in payload["servers"]:
        errors.extend(row.get("errors", []))
    if errors:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- `{error}`" for error in errors)
    lines.append("")
    return "\n".join(lines)


def _md_cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
