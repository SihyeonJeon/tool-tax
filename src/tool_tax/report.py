from __future__ import annotations

import json
from pathlib import Path

from .extract import compact_json, one_line
from .model import ScanSummary, ToolRecord


def grade(total_tokens: int) -> str:
    if total_tokens < 4_000:
        return "lean"
    if total_tokens < 12_000:
        return "warm"
    if total_tokens < 32_000:
        return "expensive"
    return "brutal"


def summarize(records: list[ToolRecord]) -> ScanSummary:
    total = sum(record.tax_tokens for record in records)
    index = sum(record.index_tokens for record in records)
    savings = max(0, total - index)
    percent = (savings / total * 100) if total else 0.0
    worst = max((record.tax_tokens for record in records), default=0)
    return ScanSummary(
        tool_count=len(records),
        total_tax_tokens=total,
        total_index_tokens=index,
        estimated_savings_tokens=savings,
        estimated_savings_percent=percent,
        worst_tool_tokens=worst,
        grade=grade(total),
    )


def to_json(records: list[ToolRecord], errors: list[str]) -> dict:
    summary = summarize(records)
    return {
        "summary": summary.__dict__,
        "recommendations": recommendations(records),
        "tools": [
            {
                "name": record.name,
                "description": record.description,
                "source_path": record.source_path,
                "pointer": record.pointer,
                "kind": record.kind,
                "tax_tokens": record.tax_tokens,
                "index_tokens": record.index_tokens,
                "index_savings_tokens": max(0, record.tax_tokens - record.index_tokens),
                "index_savings_percent": (
                    round((record.tax_tokens - record.index_tokens) / record.tax_tokens * 100, 2)
                    if record.tax_tokens
                    else 0
                ),
                "schema_ref": record.schema_ref,
            }
            for record in sorted(records, key=lambda item: item.tax_tokens, reverse=True)
        ],
        "errors": errors,
    }


def recommendations(records: list[ToolRecord]) -> list[str]:
    summary = summarize(records)
    notes: list[str] = []
    if summary.tool_count == 0:
        return ["No tools found. Point tool-tax at JSON tool manifests or OpenAPI files."]
    if summary.total_tax_tokens >= 12_000:
        notes.append("Do not always-load full schemas. Generate a slim index and lazy-load schemas.")
    else:
        notes.append("Current catalog is small enough, but track it in CI before it grows.")
    if summary.worst_tool_tokens >= 750:
        notes.append("Split or shorten the heaviest tool schema; one tool exceeds 750 estimated tokens.")
    if summary.estimated_savings_percent >= 50:
        notes.append("Progressive loading has high upside for this catalog.")
    else:
        notes.append("Slim index savings are modest; focus on response/output compression next.")
    notes.append("Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.")
    return notes


def to_markdown(records: list[ToolRecord], errors: list[str]) -> str:
    summary = summarize(records)
    lines = [
        "# Tool Tax Report",
        "",
        f"Grade: **{summary.grade}**",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Tools | {summary.tool_count} |",
        f"| Full tool tax | {summary.total_tax_tokens:,} est. tokens |",
        f"| Slim index | {summary.total_index_tokens:,} est. tokens |",
        f"| Slim-index savings | {summary.estimated_savings_tokens:,} est. tokens ({summary.estimated_savings_percent:.1f}%) |",
        f"| Worst tool | {summary.worst_tool_tokens:,} est. tokens |",
        "",
        "## Heaviest Tools",
        "",
        "| Tool | Tax | Index | Source |",
        "| --- | ---: | ---: | --- |",
    ]
    for record in sorted(records, key=lambda item: item.tax_tokens, reverse=True)[:20]:
        lines.append(
            f"| `{record.name}` | {record.tax_tokens:,} | {record.index_tokens:,} | "
            f"`{record.source_path}{record.pointer}` |"
        )
    if errors:
        lines.extend(["", "## Read Errors", ""])
        lines.extend(f"- `{error}`" for error in errors)
    lines.extend(["", "## What To Do", ""])
    lines.extend(f"- {note}" for note in recommendations(records))
    lines.append("")
    return "\n".join(lines)


def write_report(payload: str | dict, out: Path | None) -> None:
    text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def write_pack(records: list[ToolRecord], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    schema_dir = out_dir / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for record in sorted(records, key=lambda item: item.name):
        ref = record.schema_ref
        (out_dir / ref).write_text(compact_json(record.schema) + "\n", encoding="utf-8")
        index.append(
            {
                "name": record.name,
                "description": one_line(record.description, 96),
                "schema_ref": ref,
                "source_path": record.source_path,
                "source_pointer": record.pointer,
                "full_tax_tokens": record.tax_tokens,
                "index_tokens": record.index_tokens,
            }
        )
    (out_dir / "tool-index.json").write_text(
        json.dumps({"tools": index}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
