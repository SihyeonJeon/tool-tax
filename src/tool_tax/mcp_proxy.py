from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from . import __version__
from .extract import one_line
from .mcp_stdio import JsonObject, MCPStdioClient, MCPStdioError, tool_record_from_mcp
from .model import ToolRecord


PROXY_TOOLS: list[JsonObject] = [
    {
        "name": "tool_tax_list_tools",
        "description": (
            "List upstream MCP tools as a slim index with descriptions, schema references, "
            "and estimated schema token cost. Use this before choosing an upstream tool."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Optional case-insensitive substring filter for tool names or descriptions.",
                }
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "tool_tax_get_schema",
        "description": "Fetch the full input schema for one upstream MCP tool only when it is needed.",
        "inputSchema": {
            "type": "object",
            "properties": {"name": {"type": "string", "description": "Exact upstream tool name."}},
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "tool_tax_call_tool",
        "description": "Call one upstream MCP tool by exact name with JSON arguments after selecting it from the index.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Exact upstream tool name."},
                "arguments": {"type": "object", "description": "Arguments for the upstream tool."},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
]


def text_result(payload: Any) -> JsonObject:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2)
    result: JsonObject = {"content": [{"type": "text", "text": text}]}
    if isinstance(payload, dict):
        result["structuredContent"] = payload
    return result


def error_result(message: str) -> JsonObject:
    return {"content": [{"type": "text", "text": message}], "isError": True}


class ToolTaxProxy:
    def __init__(self, command: list[str], timeout: float, protocol_version: str) -> None:
        self.client = MCPStdioClient(command, timeout=timeout, protocol_version=protocol_version)
        self.protocol_version = protocol_version
        self.records: list[ToolRecord] | None = None

    def close(self) -> None:
        self.client.close()

    def write(self, message: JsonObject) -> None:
        print(json.dumps(message, ensure_ascii=False, separators=(",", ":")), flush=True)

    def write_result(self, request_id: Any, result: JsonObject) -> None:
        self.write({"jsonrpc": "2.0", "id": request_id, "result": result})

    def write_error(self, request_id: Any, code: int, message: str) -> None:
        self.write({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})

    def ensure_records(self) -> list[ToolRecord]:
        if self.records is None:
            self.records = [
                tool_record_from_mcp(tool, self.client.source, index)
                for index, tool in enumerate(self.client.list_tools())
            ]
        return self.records

    def slim_index(self, query: str = "") -> JsonObject:
        needle = query.casefold().strip()
        tools = []
        for record in self.ensure_records():
            haystack = f"{record.name}\n{record.description}".casefold()
            if needle and needle not in haystack:
                continue
            tools.append(
                {
                    "name": record.name,
                    "description": one_line(record.description, 140),
                    "schema_ref": record.schema_ref,
                    "full_schema_tokens": record.tax_tokens,
                    "index_tokens": record.index_tokens,
                }
            )
        return {"tools": tools, "tool_count": len(tools)}

    def schema_for(self, name: str) -> JsonObject | None:
        for record in self.ensure_records():
            if record.name == name:
                return {
                    "name": record.name,
                    "description": record.description,
                    "inputSchema": record.schema,
                    "full_schema_tokens": record.tax_tokens,
                    "index_tokens": record.index_tokens,
                    "source": record.source_path,
                }
        return None

    def call_proxy_tool(self, name: str, arguments: JsonObject) -> JsonObject:
        if name == "tool_tax_list_tools":
            query = arguments.get("query")
            return text_result(self.slim_index(str(query) if query is not None else ""))
        if name == "tool_tax_get_schema":
            tool_name = arguments.get("name")
            if not isinstance(tool_name, str):
                return error_result("missing required string argument: name")
            schema = self.schema_for(tool_name)
            if schema is None:
                return error_result(f"unknown upstream tool: {tool_name}")
            return text_result(schema)
        if name == "tool_tax_call_tool":
            tool_name = arguments.get("name")
            upstream_args = arguments.get("arguments", {})
            if not isinstance(tool_name, str):
                return error_result("missing required string argument: name")
            if not isinstance(upstream_args, dict):
                return error_result("arguments must be an object")
            return self.client.call_tool(tool_name, upstream_args)
        raise MCPStdioError(f"unknown proxy tool: {name}")

    def handle_request(self, message: JsonObject) -> None:
        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        if not isinstance(params, dict):
            params = {}
        if method == "initialize":
            requested_version = params.get("protocolVersion")
            self.write_result(
                request_id,
                {
                    "protocolVersion": str(requested_version or self.protocol_version),
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "tool-tax-proxy", "version": __version__},
                },
            )
            return
        if method == "tools/list":
            self.write_result(request_id, {"tools": PROXY_TOOLS})
            return
        if method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            if not isinstance(tool_name, str):
                self.write_error(request_id, -32602, "tools/call requires params.name")
                return
            if not isinstance(arguments, dict):
                self.write_error(request_id, -32602, "tools/call params.arguments must be an object")
                return
            try:
                self.write_result(request_id, self.call_proxy_tool(tool_name, arguments))
            except MCPStdioError as exc:
                self.write_error(request_id, -32602, str(exc))
            return
        if isinstance(request_id, (int, str)):
            self.write_error(request_id, -32601, f"method not found: {method}")

    def serve(self) -> int:
        try:
            for raw in sys.stdin:
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(message, dict):
                    self.handle_request(message)
        finally:
            self.close()
        return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tool-tax-proxy",
        description="Run an MCP stdio proxy that exposes a slim tool index and lazy schema loading.",
    )
    parser.add_argument("--timeout", type=float, default=10.0, help="seconds to wait for upstream MCP responses")
    parser.add_argument("--protocol-version", default="2025-06-18", help="MCP protocol version sent upstream")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="upstream MCP server command after --")
    args = parser.parse_args(argv)
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("missing upstream MCP server command after --")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return ToolTaxProxy(args.command, args.timeout, args.protocol_version).serve()


if __name__ == "__main__":
    raise SystemExit(main())
