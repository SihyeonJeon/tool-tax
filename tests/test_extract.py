from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tool_tax.extract import extract_tools
from tool_tax.report import summarize, to_json


class ExtractTests(unittest.TestCase):
    def test_extracts_tool_like_json(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "tools.json"
            path.write_text(
                json.dumps(
                    {
                        "tools": [
                            {
                                "name": "read_file",
                                "description": "Read a file",
                                "inputSchema": {"type": "object", "properties": {"path": {"type": "string"}}},
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            records, errors = extract_tools([path])
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].name, "read_file")
        self.assertGreater(records[0].tax_tokens, records[0].index_tokens)

    def test_extracts_openapi_operation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "openapi.json"
            path.write_text(
                json.dumps(
                    {
                        "openapi": "3.1.0",
                        "paths": {
                            "/items": {
                                "post": {
                                    "operationId": "create_item",
                                    "summary": "Create item",
                                    "parameters": [{"name": "x", "in": "query", "schema": {"type": "string"}}],
                                }
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            records, errors = extract_tools([path])
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].kind, "openapi")
        self.assertEqual(records[0].name, "create_item")

    def test_extracts_yaml_tool_manifest(self) -> None:
        records, errors = extract_tools([Path("examples/mcp-tools.yml")])
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].source_path, "examples/mcp-tools.yml")
        self.assertEqual({record.name for record in records}, {"docs_search", "docs_read"})

    def test_summary_and_json_report(self) -> None:
        records, errors = extract_tools([Path("examples/mcp-tools.json")])
        summary = summarize(records)
        payload = to_json(records, errors)
        self.assertEqual(errors, [])
        self.assertEqual(summary.tool_count, 4)
        self.assertEqual(payload["summary"]["tool_count"], 4)
        self.assertGreater(len(payload["recommendations"]), 0)
        self.assertIn("index_savings_percent", payload["tools"][0])
        self.assertGreater(summary.estimated_savings_percent, 0)


if __name__ == "__main__":
    unittest.main()
