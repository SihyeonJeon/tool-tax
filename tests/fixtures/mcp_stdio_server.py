from __future__ import annotations

import json
import os
import sys


TOOLS = [
    {
        "name": "search_docs",
        "description": "Search internal documentation by query and optional namespace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "namespace": {"type": "string"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "read_doc",
        "description": "Read one documentation page by stable id.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
]

EXTRA_TOOL = {
    "name": "fresh_tool",
    "description": "A tool added after a list_changed notification.",
    "inputSchema": {"type": "object", "properties": {"value": {"type": "string"}}},
}


def write(message: dict) -> None:
    print(json.dumps(message, separators=(",", ":")), flush=True)


list_calls = 0

for raw in sys.stdin:
    message = json.loads(raw)
    method = message.get("method")
    if method == "initialize":
        write(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {
                    "protocolVersion": os.environ.get("MCP_FIXTURE_PROTOCOL_VERSION", "2025-06-18"),
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "fixture-mcp", "version": "0.1.0"},
                },
            }
        )
    elif method == "tools/list":
        list_calls += 1
        params = message.get("params", {})
        cursor = params.get("cursor") if isinstance(params, dict) else None
        if os.environ.get("MCP_FIXTURE_PAGED") == "1":
            if cursor is None:
                write({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": TOOLS[:1], "nextCursor": "page-2"}})
            else:
                write({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": TOOLS[1:]}})
        elif os.environ.get("MCP_FIXTURE_LIST_CHANGED") == "1" and list_calls == 1:
            write({"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
            write({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": TOOLS}})
        elif os.environ.get("MCP_FIXTURE_LIST_CHANGED") == "1":
            write({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": [*TOOLS, EXTRA_TOOL]}})
        else:
            write({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": TOOLS}})
    elif method == "tools/call":
        params = message.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})
        if isinstance(arguments, dict) and arguments.get("fail"):
            write(
                {
                    "jsonrpc": "2.0",
                    "id": message["id"],
                    "error": {"code": -32042, "message": "fixture failure", "data": {"tool": name}},
                }
            )
            continue
        write(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({"called": name, "arguments": arguments}, sort_keys=True),
                        }
                    ],
                    "structuredContent": {"called": name, "arguments": arguments},
                },
            }
        )
