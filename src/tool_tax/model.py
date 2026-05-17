from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolRecord:
    name: str
    description: str
    schema: dict[str, Any]
    source_path: str
    pointer: str
    kind: str
    raw: dict[str, Any]
    tax_tokens: int = 0
    index_tokens: int = 0

    @property
    def schema_ref(self) -> str:
        safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in self.name)
        return f"schemas/{safe}.json"


@dataclass(frozen=True)
class ScanSummary:
    tool_count: int
    total_tax_tokens: int
    total_index_tokens: int
    estimated_savings_tokens: int
    estimated_savings_percent: float
    worst_tool_tokens: int
    grade: str

