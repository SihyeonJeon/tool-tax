from __future__ import annotations

import json
import os
import queue
import shlex
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable

from . import __version__
from .extract import with_tax
from .model import ToolRecord


class MCPStdioError(RuntimeError):
    def __init__(self, message: str, code: int = -32000, data: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data


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


def read_response(
    lines: queue.Queue[str | None],
    request_id: int,
    deadline: float,
    on_message: Callable[[JsonObject], None] | None = None,
) -> JsonObject:
    while True:
        message = read_json_message(lines, deadline)
        if message.get("id") != request_id:
            if on_message is not None:
                on_message(message)
            continue
        if "error" in message:
            error = message["error"]
            if isinstance(error, dict):
                code = error.get("code", -32000)
                if not isinstance(code, int):
                    code = -32000
                raise MCPStdioError(str(error.get("message") or error), code=code, data=error.get("data"))
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
        call_timeout: float = 60.0,
        protocol_version: str = "2025-06-18",
        cwd: Path | None = None,
        verbose: bool = False,
        env: dict[str, str] | None = None,
    ) -> None:
        if not command:
            raise MCPStdioError("missing MCP server command")
        self.command = command
        self.timeout = timeout
        self.call_timeout = call_timeout
        self.protocol_version = protocol_version
        self.cwd = cwd
        self.verbose = verbose
        self.env = env
        self.process: subprocess.Popen[str] | None = None
        self.lines: queue.Queue[str | None] | None = None
        self.next_id = 1
        self.initialize_result: JsonObject | None = None
        self.tool_list_changed = False

    @property
    def source(self) -> str:
        return command_label(self.command)

    def start(self) -> JsonObject:
        if self.process is not None:
            return self.initialize_result or {}
        self.process = subprocess.Popen(
            self.command,
            cwd=str(self.cwd) if self.cwd else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None if self.verbose else subprocess.DEVNULL,
            env={**os.environ, **self.env} if self.env else None,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )
        self.lines = start_stdout_reader(self.process)
        try:
            self.initialize_result = self.request(
                "initialize",
                {
                    "protocolVersion": self.protocol_version,
                    "capabilities": {},
                    "clientInfo": {"name": "tool-tax", "version": __version__},
                },
                timeout=self.timeout,
            )
            self.notify("notifications/initialized")
        except Exception:
            self.close()
            raise
        return self.initialize_result

    def _handle_unsolicited(self, message: JsonObject) -> None:
        if message.get("method") == "notifications/tools/list_changed":
            self.tool_list_changed = True

    def request(self, method: str, params: JsonObject | None = None, timeout: float | None = None) -> JsonObject:
        self.start() if self.process is None else None
        if self.process is None or self.lines is None:
            raise MCPStdioError("MCP server did not start")
        request_id = self.next_id
        self.next_id += 1
        message: JsonObject = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        send_message(self.process, message)
        return read_response(
            self.lines,
            request_id,
            time.monotonic() + (self.timeout if timeout is None else timeout),
            on_message=self._handle_unsolicited,
        )

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
        seen_cursors: set[str] = set()
        while True:
            if cursor:
                if cursor in seen_cursors:
                    raise MCPStdioError("MCP tools/list returned a repeated cursor")
                seen_cursors.add(cursor)
            params = {"cursor": cursor} if cursor else {}
            result = self.request("tools/list", params, timeout=self.timeout)
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
        return self.request("tools/call", params, timeout=self.call_timeout)

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
    call_timeout: float = 60.0,
    protocol_version: str = "2025-06-18",
    cwd: Path | None = None,
    verbose: bool = False,
    env: dict[str, str] | None = None,
) -> tuple[list[ToolRecord], list[str]]:
    if not command:
        raise MCPStdioError("missing MCP server command")
    client = MCPStdioClient(
        command,
        timeout=timeout,
        call_timeout=call_timeout,
        protocol_version=protocol_version,
        cwd=cwd,
        verbose=verbose,
        env=env,
    )
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
