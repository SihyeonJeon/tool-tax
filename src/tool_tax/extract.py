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
YAML_SUFFIXES = {".yaml", ".yml"}
DOCUMENT_SUFFIXES = {".json", *YAML_SUFFIXES}


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


def strip_yaml_comment(line: str) -> str:
    in_single = False
    in_double = False
    for index, char in enumerate(line):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == "#" and not in_single and not in_double:
            return line[:index]
    return line


def yaml_lines(source: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    for line in source.splitlines():
        if "\t" in line:
            raise ValueError("tabs are not supported in YAML indentation")
        cleaned = strip_yaml_comment(line).rstrip()
        if not cleaned.strip():
            continue
        lines.append((len(cleaned) - len(cleaned.lstrip(" ")), cleaned.lstrip(" ")))
    return lines


def parse_yaml_scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return ""
    if value in {"null", "Null", "NULL", "~"}:
        return None
    if value in {"true", "True", "TRUE"}:
        return True
    if value in {"false", "False", "FALSE"}:
        return False
    if (
        (value.startswith('"') and value.endswith('"'))
        or (value.startswith("'") and value.endswith("'"))
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_yaml_scalar(part.strip()) for part in inner.split(",")]
    if value.startswith("{") and value.endswith("}"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def yaml_mapping_separator_index(text: str) -> int:
    in_single = False
    in_double = False
    for index, char in enumerate(text):
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        elif char == ":" and not in_single and not in_double:
            if index == len(text) - 1 or text[index + 1].isspace():
                return index
    return -1


def split_yaml_mapping_entry(text: str) -> tuple[str, str]:
    separator = yaml_mapping_separator_index(text)
    if separator < 0:
        raise ValueError(f"expected mapping entry, got {text!r}")
    key = text[:separator]
    value = text[separator + 1 :]
    key = key.strip()
    if not key:
        raise ValueError(f"empty mapping key in {text!r}")
    return key, value.strip()


def parse_yaml_block(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[Any, int]:
    if index >= len(lines):
        return {}, index
    current_indent, text = lines[index]
    if current_indent < indent:
        return {}, index
    if text.startswith("- "):
        return parse_yaml_sequence(lines, index, current_indent)
    return parse_yaml_mapping(lines, index, current_indent)


def parse_yaml_block_scalar(
    lines: list[tuple[int, str]], index: int, indent: int, folded: bool
) -> tuple[str, int]:
    values: list[str] = []
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        values.append(text)
        index += 1
    if folded:
        return " ".join(values), index
    return "\n".join(values), index


def parse_yaml_mapping(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[dict[str, Any], int]:
    result: dict[str, Any] = {}
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"unexpected indentation before {text!r}")
        if text.startswith("- "):
            break
        key, value_text = split_yaml_mapping_entry(text)
        index += 1
        if value_text in {"|", ">"}:
            if index < len(lines) and lines[index][0] > indent:
                result[key], index = parse_yaml_block_scalar(
                    lines, index, lines[index][0], value_text == ">"
                )
            else:
                result[key] = ""
            continue
        if value_text:
            result[key] = parse_yaml_scalar(value_text)
            continue
        if index < len(lines) and lines[index][0] > indent:
            result[key], index = parse_yaml_block(lines, index, lines[index][0])
        else:
            result[key] = {}
    return result, index


def parse_yaml_sequence(lines: list[tuple[int, str]], index: int, indent: int) -> tuple[list[Any], int]:
    result: list[Any] = []
    while index < len(lines):
        current_indent, text = lines[index]
        if current_indent < indent:
            break
        if current_indent > indent:
            raise ValueError(f"unexpected indentation before {text!r}")
        if not text.startswith("- "):
            break
        item_text = text[2:].strip()
        index += 1
        if not item_text:
            if index < len(lines) and lines[index][0] > indent:
                item, index = parse_yaml_block(lines, index, lines[index][0])
            else:
                item = None
            result.append(item)
            continue
        if yaml_mapping_separator_index(item_text) >= 0:
            key, value_text = split_yaml_mapping_entry(item_text)
            item_map: dict[str, Any] = {
                key: parse_yaml_scalar(value_text) if value_text else {}
            }
            if index < len(lines) and lines[index][0] > indent:
                nested, index = parse_yaml_mapping(lines, index, lines[index][0])
                item_map.update(nested)
            result.append(item_map)
        else:
            result.append(parse_yaml_scalar(item_text))
    return result, index


def load_yaml(path: Path) -> Any:
    lines = yaml_lines(path.read_text(encoding="utf-8"))
    if not lines:
        return {}
    data, index = parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError(f"could not parse YAML near {lines[index][1]!r}")
    return data


def load_document(path: Path) -> Any:
    if path.suffix.lower() in YAML_SUFFIXES:
        return load_yaml(path)
    return load_json(path)


def candidate_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() in DOCUMENT_SUFFIXES:
            files.append(path)
        elif path.is_dir():
            files.extend(
                sorted(
                    p
                    for p in path.rglob("*")
                    if (
                        p.is_file()
                        and p.suffix.lower() in DOCUMENT_SUFFIXES
                        and ".git" not in p.parts
                    )
                )
            )
    return sorted(set(files))


def extract_tools(paths: list[Path]) -> tuple[list[ToolRecord], list[str]]:
    records: list[ToolRecord] = []
    errors: list[str] = []
    for path in candidate_files(paths):
        try:
            data = load_document(path)
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
