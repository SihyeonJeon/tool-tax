from __future__ import annotations

import json
import queue
import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

from . import __version__
from .extract import with_tax
from .model import ToolRecord


class MCPStdioError(RuntimeError):
    pass


def command_label(command: list[str]) -> str:
    return "mcp-stdio:" + " ".join(shlex.quote(part) for part in command)


def send_message(process: subprocess.Popen[str], message: dict[str, Any]) -> None:
    if process.stdin is None:
        raise MCPStdioError("MCP server stdin is closed")
    process.stdin.write(json.dumps(message, ensure_ascii=False, separators=(",", ":")) + "\n")
    process.stdin.flush()


def start_stdout_reader(process: subprocess.Popen[str]) -> queue.Queue[str | None]:
    lines: queue.Queue[str | None] = queue.Queue()

    def read_stdout() -> None:
        try:
            if process.stdout is not None:
                for line in process.stdout:
                    lines.put(line)
        finally:
            lines.put(None)

    threading.Thread(target=read_stdout, daemon=True).start()
    return lines


def read_response(lines: queue.Queue[str | None], request_id: int, deadline: float) -> dict[str, Any]:
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise MCPStdioError(f"timed out waiting for MCP response id {request_id}")
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty as exc:
            raise MCPStdioError(f"timed out waiting for MCP response id {request_id}") from exc
        if line is None:
            raise MCPStdioError(f"MCP server exited before response id {request_id}")
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict) or message.get("id") != request_id:
            continue
        if "error" in message:
            error = message["error"]
            if isinstance(error, dict):
                raise MCPStdioError(str(error.get("message") or error))
            raise MCPStdioError(str(error))
        result = message.get("result")
        if not isinstance(result, dict):
            raise MCPStdioError(f"MCP response id {request_id} has no object result")
        return result


def close_process(process: subprocess.Popen[str]) -> None:
    if process.stdin is not None:
        try:
            process.stdin.close()
        except OSError:
            pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=1)
    if process.stdout is not None:
        try:
            process.stdout.close()
        except OSError:
            pass


def tool_record_from_mcp(tool: dict[str, Any], source: str, index: int) -> ToolRecord:
    name = str(tool.get("name") or f"tool_{index}")
    description = str(tool.get("description") or "")
    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    if not isinstance(schema, dict):
        schema = {}
    return with_tax(
        ToolRecord(
            name=name,
            description=description,
            schema=schema,
            source_path=source,
            pointer=f"/tools/{index}",
            kind="mcp",
            raw=tool,
        )
    )


def list_mcp_stdio_tools(
    command: list[str],
    timeout: float = 10.0,
    protocol_version: str = "2025-06-18",
    cwd: Path | None = None,
) -> tuple[list[ToolRecord], list[str]]:
    if not command:
        raise MCPStdioError("missing MCP server command")
    process = subprocess.Popen(
        command,
        cwd=str(cwd) if cwd else None,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        bufsize=1,
    )
    lines = start_stdout_reader(process)
    source = command_label(command)
    records: list[ToolRecord] = []
    errors: list[str] = []
    request_id = 1
    try:
        send_message(
            process,
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "initialize",
                "params": {
                    "protocolVersion": protocol_version,
                    "capabilities": {},
                    "clientInfo": {"name": "tool-tax", "version": __version__},
                },
            },
        )
        read_response(lines, request_id, time.monotonic() + timeout)
        send_message(process, {"jsonrpc": "2.0", "method": "notifications/initialized"})

        cursor: str | None = None
        tool_index = 0
        while True:
            request_id += 1
            params = {"cursor": cursor} if cursor else {}
            send_message(process, {"jsonrpc": "2.0", "id": request_id, "method": "tools/list", "params": params})
            result = read_response(lines, request_id, time.monotonic() + timeout)
            tools = result.get("tools", [])
            if not isinstance(tools, list):
                raise MCPStdioError("MCP tools/list result has no tools array")
            for tool in tools:
                if isinstance(tool, dict):
                    records.append(tool_record_from_mcp(tool, source, tool_index))
                    tool_index += 1
            next_cursor = result.get("nextCursor")
            cursor = str(next_cursor) if next_cursor else None
            if not cursor:
                break
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{source}: {exc}")
    finally:
        close_process(process)
    return records, errors
