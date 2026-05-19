# Claude Code E2E Benchmark

This benchmark checks whether the raw MCP proxy savings show up inside a real
Claude Code CLI session.

Result: for Claude Code 2.1.143, the proxy is not an automatic win. The raw MCP
protocol scan still shows a large upfront schema reduction, but Claude Code's
own prompt cache, tool permission flow, and tool handling dominate this small
end-to-end run.

## Setup

- Date: 2026-05-19
- Claude Code: 2.1.143
- Model: `claude-sonnet-4-6`
- Upstream MCP server: `npx -y @modelcontextprotocol/server-filesystem /tmp`
- Output source: Claude Code `--output-format json` `modelUsage`
- Raw data: [claude-code-e2e-2026-05-19.json](benchmarks/claude-code-e2e-2026-05-19.json)

The reported `total input context tokens` are:

```text
inputTokens + cacheCreationInputTokens + cacheReadInputTokens
```

This is a context-exposure metric, not a provider billing formula. Prompt-cache
reads and prompt-cache writes have different prices.

## Protocol Baseline

At the raw MCP `tools/list` level, `tool-tax proxy` still reduces the exposed
filesystem tool schema:

| Mode | Upfront schema tax |
| --- | ---: |
| Direct MCP Filesystem | 2,102 est. tokens |
| Through `tool-tax proxy` | 260 est. tokens |
| Reduction | 87.6% |

That measurement is host-agnostic. The E2E results below are host-specific.

## E2E Results

| Case | Direct | Proxy | Delta |
| --- | ---: | ---: | ---: |
| Startup-only total input context tokens | 14,748 | 14,603 | -145 (-1.0%) |
| Startup-only cost | $0.01555 | $0.01500 | -$0.00054 |
| Startup-only duration | 2.18s | 2.17s | -0.01s |
| Known-tool total input context tokens | 44,957 | 46,233 | +1,276 (+2.8%) |
| Known-tool cost | $0.02905 | $0.03615 | +$0.00710 |
| Known-tool duration | 6.99s | 8.79s | +1.79s |
| Known-tool turns | 3 | 4 | +1 |

## Interpretation

For a startup-only Claude Code session, the proxy only moved the measured
context by 145 tokens. That is much smaller than the raw MCP `tools/list`
schema delta. This suggests Claude Code is not simply pasting the entire raw
MCP catalog into the model prompt in this benchmark path.

For a task that already knows the exact filesystem tool to call, the direct
server was cheaper and faster. The proxy had to list upstream tools and then
call through `tool_tax_call_tool`, adding one turn and more output.

This is a useful negative result. It means `tool-tax proxy` should not be
marketed as a blanket Claude Code cost reducer. The stronger claim is:

- `tool-tax scan/mcp/diff` measures raw tool-schema bloat and CI regressions.
- `tool-tax proxy` helps hosts that expose full upstream schemas up front.
- For hosts with their own lazy MCP handling, measure first.

## Reproduce

```bash
bash scripts/claude-code-e2e-benchmark.sh
```

The script writes a summarized JSON file under `docs/benchmarks/`.

