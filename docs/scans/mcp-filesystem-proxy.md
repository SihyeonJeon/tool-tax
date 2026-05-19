# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 3 |
| Full tool tax | 260 est. tokens |
| Slim index | 136 est. tokens |
| Slim-index savings | 124 est. tokens (47.7%) |
| Worst tool | 103 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `tool_tax_call_tool` | 103 | 46 | `mcp-stdio:python3 -m tool_tax.mcp_proxy --timeout 30 -- npx -y @modelcontextprotocol/server-filesystem /tmp/tools/2` |
| `tool_tax_list_tools` | 83 | 46 | `mcp-stdio:python3 -m tool_tax.mcp_proxy --timeout 30 -- npx -y @modelcontextprotocol/server-filesystem /tmp/tools/0` |
| `tool_tax_get_schema` | 74 | 44 | `mcp-stdio:python3 -m tool_tax.mcp_proxy --timeout 30 -- npx -y @modelcontextprotocol/server-filesystem /tmp/tools/1` |

## What To Do

- Current catalog is small enough, but track it in CI before it grows.
- Slim index savings are modest; focus on response/output compression next.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
