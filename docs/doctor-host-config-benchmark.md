# Doctor Host Config Benchmark

This benchmark checks the main `tool-tax doctor` path: read an agent-host MCP
config file, start the configured stdio server, call `initialize` and
`tools/list`, then report the schema budget before the host loads those tools.

## Setup

- Date: 2026-05-20
- `tool-tax`: 0.7.0
- Config shape: VS Code-style top-level `servers`
- Config: [vscode-filesystem.mcp.json](../examples/host-configs/vscode-filesystem.mcp.json)
- Server: `npx -y @modelcontextprotocol/server-filesystem /tmp`
- Raw data: [doctor-vscode-filesystem-2026-05-20.json](benchmarks/doctor-vscode-filesystem-2026-05-20.json)

## Result

| Metric | Value |
| --- | ---: |
| Configs | 1 |
| Servers | 1 |
| Probed servers | 1 |
| Tools | 14 |
| Full tool tax | 2,102 est. tokens |
| Slim index | 647 est. tokens |
| Slim-index savings | 1,455 est. tokens (69.2%) |
| Worst tool | 242 est. tokens |

Heaviest tools:

| Tool | Tax |
| --- | ---: |
| `edit_file` | 242 |
| `read_text_file` | 225 |
| `search_files` | 203 |
| `read_multiple_files` | 174 |
| `directory_tree` | 174 |

## Interpretation

This is the practical install path: point `doctor` at a host config and it tells
you which MCP server adds schema weight. The result is not a billing claim. It
is a reproducible schema-size report for the tool catalog returned by
`tools/list`.

Use `--no-probe` first when inspecting user-level configs:

```bash
tool-tax doctor --include-global --no-probe
```

Remove `--no-probe` only after reviewing the commands that will execute.

## Reproduce

```bash
PYTHONPATH=src python3 -m tool_tax.cli doctor \
  --mcp-config examples/host-configs/vscode-filesystem.mcp.json \
  --format json \
  --timeout 30 \
  --out docs/benchmarks/doctor-vscode-filesystem-$(date +%Y-%m-%d).json
```
