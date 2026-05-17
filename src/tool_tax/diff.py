from __future__ import annotations

import json

from .extract import compact_json
from .model import DiffRecord, DiffSummary, ToolRecord
from .report import summarize


def source_label(record: ToolRecord | None) -> str:
    if record is None:
        return ""
    return f"{record.source_path}{record.pointer}"


def fingerprint(record: ToolRecord) -> str:
    return compact_json(
        {
            "description": record.description,
            "kind": record.kind,
            "schema": record.schema,
        }
    )


def by_name(records: list[ToolRecord]) -> dict[str, ToolRecord]:
    grouped: dict[str, ToolRecord] = {}
    for record in sorted(records, key=lambda item: (item.name, item.source_path, item.pointer)):
        existing = grouped.get(record.name)
        if existing is None or record.tax_tokens > existing.tax_tokens:
            grouped[record.name] = record
    return grouped


def compare_records(base_records: list[ToolRecord], head_records: list[ToolRecord]) -> tuple[DiffSummary, list[DiffRecord]]:
    base = by_name(base_records)
    head = by_name(head_records)
    rows: list[DiffRecord] = []
    unchanged = 0

    for name in sorted(set(base) | set(head)):
        old = base.get(name)
        new = head.get(name)
        if old is None and new is not None:
            status = "added"
        elif old is not None and new is None:
            status = "removed"
        elif old is not None and new is not None and fingerprint(old) != fingerprint(new):
            status = "changed"
        else:
            unchanged += 1
            continue

        base_tax = old.tax_tokens if old else 0
        head_tax = new.tax_tokens if new else 0
        base_index = old.index_tokens if old else 0
        head_index = new.index_tokens if new else 0
        rows.append(
            DiffRecord(
                status=status,
                name=name,
                base_tax_tokens=base_tax,
                head_tax_tokens=head_tax,
                delta_tax_tokens=head_tax - base_tax,
                base_index_tokens=base_index,
                head_index_tokens=head_index,
                delta_index_tokens=head_index - base_index,
                base_source=source_label(old),
                head_source=source_label(new),
            )
        )

    base_summary = summarize(base_records)
    head_summary = summarize(head_records)
    summary = DiffSummary(
        base_tool_count=base_summary.tool_count,
        head_tool_count=head_summary.tool_count,
        added_count=sum(1 for row in rows if row.status == "added"),
        removed_count=sum(1 for row in rows if row.status == "removed"),
        changed_count=sum(1 for row in rows if row.status == "changed"),
        unchanged_count=unchanged,
        base_tax_tokens=base_summary.total_tax_tokens,
        head_tax_tokens=head_summary.total_tax_tokens,
        delta_tax_tokens=head_summary.total_tax_tokens - base_summary.total_tax_tokens,
        base_index_tokens=base_summary.total_index_tokens,
        head_index_tokens=head_summary.total_index_tokens,
        delta_index_tokens=head_summary.total_index_tokens - base_summary.total_index_tokens,
        worst_tool_delta_tokens=max((row.delta_tax_tokens for row in rows), default=0),
    )
    return summary, sorted(rows, key=lambda row: (row.delta_tax_tokens, row.name), reverse=True)


def signed(value: int) -> str:
    return f"{value:+,}"


def to_diff_json(
    base_records: list[ToolRecord],
    head_records: list[ToolRecord],
    errors: list[str],
) -> dict:
    summary, rows = compare_records(base_records, head_records)
    return {
        "summary": summary.__dict__,
        "tools": [row.__dict__ for row in rows],
        "errors": errors,
    }


def to_diff_markdown(
    base_records: list[ToolRecord],
    head_records: list[ToolRecord],
    errors: list[str],
) -> str:
    summary, rows = compare_records(base_records, head_records)
    lines = [
        "# Tool Tax Diff",
        "",
        "| Metric | Base | Head | Delta |",
        "| --- | ---: | ---: | ---: |",
        f"| Tools | {summary.base_tool_count:,} | {summary.head_tool_count:,} | {signed(summary.head_tool_count - summary.base_tool_count)} |",
        f"| Full tool tax | {summary.base_tax_tokens:,} | {summary.head_tax_tokens:,} | {signed(summary.delta_tax_tokens)} |",
        f"| Slim index | {summary.base_index_tokens:,} | {summary.head_index_tokens:,} | {signed(summary.delta_index_tokens)} |",
        f"| Changed tools | - | - | {summary.changed_count:,} |",
        f"| Added tools | - | - | {summary.added_count:,} |",
        f"| Removed tools | - | - | {summary.removed_count:,} |",
        "",
        "## Tool Changes",
        "",
        "| Status | Tool | Base | Head | Delta | Source |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    if not rows:
        lines.append("| unchanged | - | 0 | 0 | +0 | - |")
    for row in rows[:30]:
        source = row.head_source or row.base_source
        lines.append(
            f"| {row.status} | `{row.name}` | {row.base_tax_tokens:,} | "
            f"{row.head_tax_tokens:,} | {signed(row.delta_tax_tokens)} | `{source}` |"
        )
    if errors:
        lines.extend(["", "## Read Errors", ""])
        lines.extend(f"- `{error}`" for error in errors)
    lines.append("")
    return "\n".join(lines)


def dump_diff_json(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
