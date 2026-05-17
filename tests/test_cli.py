from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from tool_tax.cli import main


class CliTests(unittest.TestCase):
    def test_scan_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.json"
            code = main(["scan", "examples/mcp-tools.json", "--format", "json", "--out", str(out)])
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["tool_count"], 4)

    def test_budget_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "report.json"
            code = main(
                [
                    "scan",
                    "examples/mcp-tools.json",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                    "--max-tokens",
                    "1",
                ]
            )
            self.assertEqual(code, 2)
            self.assertTrue(out.exists())

    def test_pack_writes_index_and_schemas(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with redirect_stdout(StringIO()):
                code = main(["pack", "examples/mcp-tools.json", "--out", td])
            self.assertEqual(code, 0)
            self.assertTrue((Path(td) / "tool-index.json").exists())
            payload = json.loads((Path(td) / "tool-index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(payload["tools"]), 4)


if __name__ == "__main__":
    unittest.main()
