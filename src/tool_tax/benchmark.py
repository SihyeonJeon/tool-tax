from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


BENCHMARK_SCOPE_NOTE = (
    "public MCP/OpenAPI catalog scan benchmark; local estimator only, not provider billing or runtime savings"
)
METRIC_MAP = {
    "Tools": "tool_count",
    "Full tool tax": "total_tax_tokens",
    "Slim index": "total_index_tokens",
    "Worst tool": "worst_tool_tokens",
}


def build_benchmark(manifest_path: Path) -> dict[str, Any]:
    manifest = _read_manifest(manifest_path)
    root = manifest_path.parent
    rows = []
    for entry in manifest["catalogs"]:
        report_path = _resolve_report(root, Path(str(entry["report"])))
        report = _read_report_summary(report_path)
        rows.append(
            {
                "name": str(entry["name"]),
                "kind": str(entry.get("kind", "catalog")),
                "source": str(entry.get("source", "")),
                "report": str(entry["report"]),
                "proxy_for": entry.get("proxy_for"),
                **report,
            }
        )
    summary = _summary(rows)
    return {
        "metadata": {
            "name": manifest.get("name", manifest_path.stem),
            "date": str(manifest.get("date", "")),
            "evidence_grade": "public_catalog_scan",
            "claim_allowed": False,
            "scope_note": str(manifest.get("scope_note", BENCHMARK_SCOPE_NOTE)),
            "manifest": str(manifest_path),
        },
        "summary": summary,
        "catalogs": rows,
        "proxy_pairs": _proxy_pairs(rows),
        "insights": _insights(rows, summary),
    }


def benchmark_to_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# Public Catalog Benchmark",
        "",
        payload["metadata"]["scope_note"],
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Catalogs | {summary['catalog_count']} |",
        f"| Tools | {summary['tool_count']:,} |",
        f"| Full tool tax | {summary['total_tax_tokens']:,} est. tokens |",
        f"| Slim index | {summary['total_index_tokens']:,} est. tokens |",
        f"| Slim-index savings | {summary['estimated_savings_tokens']:,} est. tokens ({summary['estimated_savings_percent']:.1f}%) |",
        f"| Brutal catalogs | {summary['brutal_catalog_count']} |",
        "",
        "## Catalogs",
        "",
        "| Catalog | Kind | Tools | Full tool tax | Slim index | Savings | Worst tool | Grade |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for row in payload["catalogs"]:
        lines.append(
            f"| {row['name']} | {row['kind']} | {row['tool_count']:,} | "
            f"{row['total_tax_tokens']:,} | {row['total_index_tokens']:,} | "
            f"{row['estimated_savings_percent']:.1f}% | {row['worst_tool_tokens']:,} | {row['grade']} |"
        )
    if payload["proxy_pairs"]:
        lines.extend([
            "",
            "## Direct vs Proxy",
            "",
            "| Direct catalog | Proxy catalog | Direct tax | Proxy tax | Reduction |",
            "| --- | --- | ---: | ---: | ---: |",
        ])
        for pair in payload["proxy_pairs"]:
            lines.append(
                f"| {pair['direct']} | {pair['proxy']} | "
                f"{pair['direct_tax_tokens']:,} | {pair['proxy_tax_tokens']:,} | "
                f"{pair['reduction_percent']:.1f}% |"
            )
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {item}" for item in payload["insights"])
    lines.append("")
    return "\n".join(lines)


def benchmark_to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _read_manifest(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        if path.suffix.lower() == ".json":
            data = json.load(handle)
        else:
            data = yaml.safe_load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("catalogs"), list):
        raise ValueError(f"{path}: benchmark manifest must contain a catalogs list")
    return data


def _resolve_report(root: Path, report_path: Path) -> Path:
    if report_path.is_absolute():
        return report_path
    candidate = root / report_path
    if candidate.exists():
        return candidate
    return root.parent / report_path


def _read_report_summary(path: Path) -> dict[str, Any]:
    if path.suffix.lower() == ".json":
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        summary = data["summary"]
        return {
            "tool_count": int(summary["tool_count"]),
            "total_tax_tokens": int(summary["total_tax_tokens"]),
            "total_index_tokens": int(summary["total_index_tokens"]),
            "estimated_savings_tokens": int(summary["estimated_savings_tokens"]),
            "estimated_savings_percent": float(summary["estimated_savings_percent"]),
            "worst_tool_tokens": int(summary["worst_tool_tokens"]),
            "grade": str(summary["grade"]),
        }
    return _parse_markdown_report(path)


def _parse_markdown_report(path: Path) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    grade = "unknown"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("Grade:"):
            match = re.search(r"\*\*([^*]+)\*\*", line)
            grade = match.group(1) if match else line.split(":", 1)[1].strip()
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] not in {*METRIC_MAP, "Slim-index savings"}:
            continue
        if cells[0] == "Slim-index savings":
            metrics["estimated_savings_tokens"] = _first_int(cells[1])
            metrics["estimated_savings_percent"] = _first_float(cells[1])
        else:
            metrics[METRIC_MAP[cells[0]]] = _first_int(cells[1])
    required = {
        "tool_count",
        "total_tax_tokens",
        "total_index_tokens",
        "estimated_savings_tokens",
        "estimated_savings_percent",
        "worst_tool_tokens",
    }
    missing = sorted(required - set(metrics))
    if missing:
        raise ValueError(f"{path}: missing benchmark metrics: {missing}")
    metrics["grade"] = grade
    return metrics


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(row["total_tax_tokens"] for row in rows)
    index = sum(row["total_index_tokens"] for row in rows)
    savings = max(0, total - index)
    heaviest = max(rows, key=lambda row: row["total_tax_tokens"], default={})
    worst_tool = max(rows, key=lambda row: row["worst_tool_tokens"], default={})
    return {
        "catalog_count": len(rows),
        "tool_count": sum(row["tool_count"] for row in rows),
        "total_tax_tokens": total,
        "total_index_tokens": index,
        "estimated_savings_tokens": savings,
        "estimated_savings_percent": (savings / total * 100) if total else 0.0,
        "brutal_catalog_count": sum(1 for row in rows if row["grade"] == "brutal"),
        "heaviest_catalog": heaviest.get("name"),
        "heaviest_catalog_tokens": heaviest.get("total_tax_tokens", 0),
        "worst_tool_catalog": worst_tool.get("name"),
        "worst_tool_tokens": worst_tool.get("worst_tool_tokens", 0),
    }


def _proxy_pairs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_name = {row["name"]: row for row in rows}
    pairs = []
    for row in rows:
        direct_name = row.get("proxy_for")
        if not direct_name or direct_name not in by_name:
            continue
        direct = by_name[direct_name]
        reduction = max(0, direct["total_tax_tokens"] - row["total_tax_tokens"])
        pairs.append(
            {
                "direct": direct_name,
                "proxy": row["name"],
                "direct_tax_tokens": direct["total_tax_tokens"],
                "proxy_tax_tokens": row["total_tax_tokens"],
                "reduction_tokens": reduction,
                "reduction_percent": (reduction / direct["total_tax_tokens"] * 100)
                if direct["total_tax_tokens"]
                else 0.0,
            }
        )
    return pairs


def _insights(rows: list[dict[str, Any]], summary: dict[str, Any]) -> list[str]:
    notes = [
        f"{summary['catalog_count']} catalogs expose {summary['tool_count']:,} tools and {summary['total_tax_tokens']:,} estimated schema tokens.",
        f"A slim index would reduce the benchmark corpus by {summary['estimated_savings_percent']:.1f}% before exact schemas are fetched.",
        f"{summary['heaviest_catalog']} is the heaviest catalog in this benchmark.",
    ]
    if summary["brutal_catalog_count"]:
        notes.append(f"{summary['brutal_catalog_count']} catalogs are graded brutal; these need slicing, lazy loading, or CI budgets.")
    worst = summary["worst_tool_catalog"]
    notes.append(f"The largest single-tool schema appears in {worst} at {summary['worst_tool_tokens']:,} estimated tokens.")
    return notes


def _first_int(text: str) -> int:
    match = re.search(r"[-+]?\d[\d,]*", text)
    if not match:
        raise ValueError(f"no integer in metric cell: {text}")
    return int(match.group(0).replace(",", ""))


def _first_float(text: str) -> float:
    match = re.search(r"[-+]?\d+(?:\.\d+)?%", text)
    if not match:
        raise ValueError(f"no percent in metric cell: {text}")
    return float(match.group(0).rstrip("%"))
