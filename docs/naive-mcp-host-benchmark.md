# Naive MCP Host Benchmark

This benchmark models the host behavior that `tool-tax proxy` is designed to
improve: a simple MCP agent host that includes the complete visible tool catalog
in every model prompt turn.

Result: in this host shape, the proxy is a clear win. The proxy replaces the
14-tool filesystem catalog with three wrapper tools, so repeated prompt turns
carry much less schema text.

## Setup

- Date: 2026-05-19
- `tool-tax`: 0.6.0
- Upstream MCP server: `npx -y @modelcontextprotocol/server-filesystem /tmp`
- Measurement: local `tool-tax` estimator over the simulated host prompt
- Raw data: [naive-mcp-host-2026-05-19.json](benchmarks/naive-mcp-host-2026-05-19.json)

The simulated host prompt contains:

- a short system instruction;
- the complete visible MCP `tools/list` catalog;
- the user task;
- prior tool-call transcript for that task.

This is not a provider billing claim. It is a reproducible context-size
benchmark for host implementations that expose all visible schemas to the model.

## Results

| Case | Direct | Proxy | Reduction |
| --- | ---: | ---: | ---: |
| Startup-only prompt tokens | 4,141 | 380 | 90.8% |
| Known-tool task prompt tokens | 8,349 | 848 | 89.8% |
| Discover-then-call prompt tokens | 8,367 | 6,861 | 18.0% |

Catalog size:

| Mode | Visible tools | Catalog tokens |
| --- | ---: | ---: |
| Direct MCP Filesystem | 14 | 4,091 |
| Through `tool-tax proxy` | 3 | 330 |

## Interpretation

The proxy helps most when the host repeatedly includes visible tool schemas in
the model prompt. That is the naive implementation pattern:

1. call MCP `tools/list`;
2. attach the visible tool schemas to the model prompt;
3. repeat that tool catalog on later model turns.

The known-tool case wins because both modes perform two prompt turns, but the
proxy repeats only three wrapper schemas. The discover-then-call case still
wins, but by less, because the proxy adds a `tool_tax_list_tools` turn and the
slim upstream index becomes part of the transcript.

Compare this with [Claude Code E2E Benchmark](claude-code-e2e-benchmark.md).
Claude Code 2.1.143 did not behave like this naive host in the measured path;
its own prompt cache and MCP handling dominated the raw schema difference.

The practical claim is therefore:

- `tool-tax proxy` is useful for hosts that expose full visible MCP schemas up
  front or repeat them across turns.
- For optimized hosts, measure the actual host path before claiming runtime
  savings.

## Reproduce

```bash
PYTHONPATH=src python3 scripts/naive-mcp-host-benchmark.py \
  --out docs/benchmarks/naive-mcp-host-$(date +%Y-%m-%d).json
```

The script runs both direct MCP Filesystem and `tool-tax proxy`, performs real
MCP tool calls, and writes a JSON summary.

To benchmark a different stdio server:

```bash
PYTHONPATH=src python3 scripts/naive-mcp-host-benchmark.py -- \
  python3 tests/fixtures/mcp_stdio_server.py
```
