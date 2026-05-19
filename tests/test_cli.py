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

    def test_diff_json_output(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "diff.json"
            code = main(
                [
                    "diff",
                    "tests/fixtures/diff/base-tools.json",
                    "tests/fixtures/diff/head-tools.json",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["added_count"], 1)
            self.assertEqual(payload["summary"]["changed_count"], 1)
            self.assertGreater(payload["summary"]["delta_tax_tokens"], 0)

    def test_diff_budget_failure(self) -> None:
        with redirect_stdout(StringIO()):
            code = main(
                [
                    "diff",
                    "tests/fixtures/diff/base-tools.json",
                    "tests/fixtures/diff/head-tools.json",
                    "--max-delta-tokens",
                    "1",
                ]
            )
        self.assertEqual(code, 2)

    def test_comment_pr_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            body = Path(td) / "report.md"
            body.write_text("# Report\n", encoding="utf-8")
            with redirect_stdout(StringIO()) as stdout:
                code = main(["comment-pr", "--body-file", str(body), "--repo", "owner/repo", "--pr", "7", "--dry-run"])
            self.assertEqual(code, 0)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(payload["repo"], "owner/repo")
            self.assertEqual(payload["pr"], 7)

    def test_scan_openapi_slice_by_operation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "slice.json"
            code = main(
                [
                    "scan",
                    "examples/openapi.json",
                    "--operation",
                    "create_*",
                    "--format",
                    "json",
                    "--out",
                    str(out),
                ]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["summary"]["tool_count"], 1)
            self.assertEqual(payload["tools"][0]["name"], "create_run")


if __name__ == "__main__":
    unittest.main()
