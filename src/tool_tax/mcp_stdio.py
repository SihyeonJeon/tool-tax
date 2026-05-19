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


JsonObject = dict[str, Any]


def command_label(command: list[str]) -> str:
    return "mcp-stdio:" + " ".join(shlex.quote(part) for part in command)


def send_message(process: subprocess.Popen[str], message: JsonObject) -> None:
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


def read_json_message(lines: queue.Queue[str | None], deadline: float) -> JsonObject:
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise MCPStdioError("timed out waiting for MCP response")
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty as exc:
            raise MCPStdioError("timed out waiting for MCP response") from exc
        if line is None:
            raise MCPStdioError("MCP server exited before response")
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(message, dict):
            continue
        return message


def read_response(lines: queue.Queue[str | None], request_id: int, deadline: float) -> JsonObject:
    while True:
        message = read_json_message(lines, deadline)
        if message.get("id") != request_id:
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


class MCPStdioClient:
    def __init__(
        self,
        command: list[str],
        timeout: float = 10.0,
        protocol_version: str = "2025-06-18",
        cwd: Path | None = None,
    ) -> None:
        if not command:
            raise MCPStdioError("missing MCP server command")
        self.command = command
        self.timeout = timeout
        self.protocol_version = protocol_version
        self.cwd = cwd
        self.process: subprocess.Popen[str] | None = None
        self.lines: queue.Queue[str | None] | None = None
        self.next_id = 1

    @property
    def source(self) -> str:
        return command_label(self.command)

    def start(self) -> None:
        if self.process is not None:
            return
        self.process = subprocess.Popen(
            self.command,
            cwd=str(self.cwd) if self.cwd else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.lines = start_stdout_reader(self.process)
        self.request(
            "initialize",
            {
                "protocolVersion": self.protocol_version,
                "capabilities": {},
                "clientInfo": {"name": "tool-tax", "version": __version__},
            },
        )
        self.notify("notifications/initialized")

    def request(self, method: str, params: JsonObject | None = None) -> JsonObject:
        self.start() if self.process is None else None
        if self.process is None or self.lines is None:
            raise MCPStdioError("MCP server did not start")
        request_id = self.next_id
        self.next_id += 1
        message: JsonObject = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        send_message(self.process, message)
        return read_response(self.lines, request_id, time.monotonic() + self.timeout)

    def notify(self, method: str, params: JsonObject | None = None) -> None:
        if self.process is None:
            self.start()
        if self.process is None:
            raise MCPStdioError("MCP server did not start")
        message: JsonObject = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            message["params"] = params
        send_message(self.process, message)

    def list_tools(self) -> list[JsonObject]:
        tools: list[JsonObject] = []
        cursor: str | None = None
        while True:
            params = {"cursor": cursor} if cursor else {}
            result = self.request("tools/list", params)
            batch = result.get("tools", [])
            if not isinstance(batch, list):
                raise MCPStdioError("MCP tools/list result has no tools array")
            tools.extend(tool for tool in batch if isinstance(tool, dict))
            next_cursor = result.get("nextCursor")
            cursor = str(next_cursor) if next_cursor else None
            if not cursor:
                return tools

    def call_tool(self, name: str, arguments: JsonObject | None = None) -> JsonObject:
        params: JsonObject = {"name": name}
        if arguments is not None:
            params["arguments"] = arguments
        return self.request("tools/call", params)

    def close(self) -> None:
        if self.process is not None:
            close_process(self.process)
            self.process = None
            self.lines = None


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
    client = MCPStdioClient(command, timeout=timeout, protocol_version=protocol_version, cwd=cwd)
    source = client.source
    records: list[ToolRecord] = []
    errors: list[str] = []
    try:
        for tool_index, tool in enumerate(client.list_tools()):
            records.append(tool_record_from_mcp(tool, source, tool_index))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"{source}: {exc}")
    finally:
        client.close()
    return records, errors
