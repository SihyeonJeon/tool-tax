from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tool_tax.benchmark import benchmark_to_markdown, build_benchmark
from tool_tax.cli import main


class BenchmarkTests(unittest.TestCase):
    def test_public_catalog_benchmark_summarizes_scan_gallery(self) -> None:
        payload = build_benchmark(Path("docs/benchmarks/public-catalogs.yml"))

        self.assertEqual(payload["summary"]["catalog_count"], 10)
        self.assertEqual(payload["summary"]["tool_count"], 3429)
        self.assertEqual(payload["summary"]["heaviest_catalog"], "Stripe OpenAPI")
        self.assertEqual(payload["summary"]["worst_tool_catalog"], "Stripe OpenAPI")
        self.assertEqual(payload["summary"]["brutal_catalog_count"], 4)
        pairs = {row["direct"]: row for row in payload["proxy_pairs"]}
        self.assertAlmostEqual(pairs["MCP Filesystem stdio"]["reduction_percent"], 87.63, places=2)

    def test_benchmark_markdown_contains_proxy_section(self) -> None:
        payload = build_benchmark(Path("docs/benchmarks/public-catalogs.yml"))
        markdown = benchmark_to_markdown(payload)

        self.assertIn("## Direct vs Proxy", markdown)
        self.assertIn("Stripe OpenAPI", markdown)
        self.assertIn("3,429", markdown)

    def test_benchmark_cli_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "benchmark.json"
            md_out = Path(tmp) / "benchmark.md"

            json_code = main(["benchmark", "docs/benchmarks/public-catalogs.yml", "--format", "json", "--out", str(json_out)])
            md_code = main(["benchmark", "docs/benchmarks/public-catalogs.yml", "--out", str(md_out)])

            self.assertEqual(json_code, 0)
            self.assertEqual(md_code, 0)
            self.assertEqual(json.loads(json_out.read_text(encoding="utf-8"))["summary"]["catalog_count"], 10)
            self.assertIn("Public Catalog Benchmark", md_out.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
