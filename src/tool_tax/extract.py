from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .model import ToolRecord
from .tokenize import estimate_tokens


SCHEMA_KEYS = {
    "inputSchema",
    "input_schema",
    "parameters",
    "argsSchema",
    "argument_schema",
    "schema",
}

METHODS = {"get", "put", "post", "delete", "patch", "options", "head"}


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def one_line(text: str, limit: int = 120) -> str:
    clean = " ".join(str(text or "").split())
    if len(clean) <= limit:
        return clean
    return clean[: limit - 1].rstrip() + "…"


def tool_payload(name: str, description: str, schema: dict[str, Any]) -> str:
    return "\n".join([name, description, compact_json(schema)])


def index_payload(name: str, description: str, schema_ref: str) -> str:
    return compact_json(
        {
            "name": name,
            "description": one_line(description, 96),
            "schema_ref": schema_ref,
        }
    )


def with_tax(record: ToolRecord) -> ToolRecord:
    tax = estimate_tokens(tool_payload(record.name, record.description, record.schema))
    index = estimate_tokens(index_payload(record.name, record.description, record.schema_ref))
    return ToolRecord(
        name=record.name,
        description=record.description,
        schema=record.schema,
        source_path=record.source_path,
        pointer=record.pointer,
        kind=record.kind,
        raw=record.raw,
        tax_tokens=tax,
        index_tokens=index,
    )


def is_tool_like(obj: dict[str, Any]) -> bool:
    has_name = any(isinstance(obj.get(key), str) for key in ["name", "title", "operationId"])
    has_description = any(isinstance(obj.get(key), str) for key in ["description", "summary"])
    has_schema = any(key in obj for key in SCHEMA_KEYS)
    return has_name and (has_description or has_schema) and has_schema


def record_from_tool_like(obj: dict[str, Any], source: Path, pointer: str) -> ToolRecord:
    name = str(obj.get("name") or obj.get("operationId") or obj.get("title") or pointer.rsplit("/", 1)[-1])
    description = str(obj.get("description") or obj.get("summary") or "")
    schema: dict[str, Any] = {}
    for key in SCHEMA_KEYS:
        value = obj.get(key)
        if isinstance(value, dict):
            schema = value
            break
        if isinstance(value, list):
            schema = {"parameters": value}
            break
    return with_tax(
        ToolRecord(
            name=name,
            description=description,
            schema=schema,
            source_path=str(source),
            pointer=pointer,
            kind="tool",
            raw=obj,
        )
    )


def extract_openapi(data: dict[str, Any], source: Path) -> list[ToolRecord]:
    paths = data.get("paths")
    if not isinstance(paths, dict):
        return []
    records: list[ToolRecord] = []
    for path_name, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        for method, op in path_item.items():
            if method.lower() not in METHODS or not isinstance(op, dict):
                continue
            name = str(op.get("operationId") or f"{method}_{path_name}".strip("/").replace("/", "_") or method)
            desc = str(op.get("description") or op.get("summary") or "")
            schema = {
                "method": method.upper(),
                "path": path_name,
                "parameters": op.get("parameters", []),
                "requestBody": op.get("requestBody", {}),
            }
            records.append(
                with_tax(
                    ToolRecord(
                        name=name,
                        description=desc,
                        schema=schema,
                        source_path=str(source),
                        pointer=f"/paths/{path_name}/{method}",
                        kind="openapi",
                        raw=op,
                    )
                )
            )
    return records


def walk_json(obj: Any, source: Path, pointer: str = "") -> Iterable[ToolRecord]:
    if isinstance(obj, dict):
        if is_tool_like(obj):
            yield record_from_tool_like(obj, source, pointer or "/")
            return
        for key, value in obj.items():
            escaped = str(key).replace("~", "~0").replace("/", "~1")
            yield from walk_json(value, source, f"{pointer}/{escaped}")
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from walk_json(value, source, f"{pointer}/{index}")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def candidate_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".json":
            files.append(path)
        elif path.is_dir():
            files.extend(sorted(p for p in path.rglob("*.json") if ".git" not in p.parts))
    return sorted(set(files))


def extract_tools(paths: list[Path]) -> tuple[list[ToolRecord], list[str]]:
    records: list[ToolRecord] = []
    errors: list[str] = []
    for path in candidate_files(paths):
        try:
            data = load_json(path)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"{path}: {exc}")
            continue
        if isinstance(data, dict):
            openapi_records = extract_openapi(data, path)
            if openapi_records:
                records.extend(openapi_records)
                continue
        records.extend(walk_json(data, path))
    seen: set[tuple[str, str, str]] = set()
    unique: list[ToolRecord] = []
    for record in records:
        key = (record.source_path, record.pointer, record.name)
        if key not in seen:
            seen.add(key)
            unique.append(record)
    return unique, errors
