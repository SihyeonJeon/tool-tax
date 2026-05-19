from __future__ import annotations

import json
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


def write(message: dict) -> None:
    print(json.dumps(message, separators=(",", ":")), flush=True)


for raw in sys.stdin:
    message = json.loads(raw)
    method = message.get("method")
    if method == "initialize":
        write(
            {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "fixture-mcp", "version": "0.1.0"},
                },
            }
        )
    elif method == "tools/list":
        write({"jsonrpc": "2.0", "id": message["id"], "result": {"tools": TOOLS}})
