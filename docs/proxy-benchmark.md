# Proxy Benchmark

`tool-tax proxy` is an experimental MCP stdio server that sits in front of an
upstream MCP stdio server. Instead of exposing every upstream tool schema at
startup, it exposes three wrapper tools:

- `tool_tax_list_tools`
- `tool_tax_get_schema`
- `tool_tax_call_tool`

That changes the upfront schema cost from "all upstream tools" to "three proxy
tools". Full upstream schemas are fetched only when the agent asks for one.

| Upstream server | Direct upfront tax | Proxy upfront tax | Reduction |
| --- | ---: | ---: | ---: |
| MCP Filesystem | 2,102 | 260 | 87.6% |
| MCP Memory | 1,324 | 260 | 80.4% |
| MCP Sequential Thinking | 858 | 260 | 69.7% |
| MCP Everything | 1,499 | 260 | 82.7% |

## Reproduce

```bash
tool-tax mcp -- npx -y @modelcontextprotocol/server-filesystem /tmp
tool-tax mcp -- tool-tax proxy -- npx -y @modelcontextprotocol/server-filesystem /tmp
```

## Limits

This is a narrow stdio proxy for `tools/list` and `tools/call`. It is not a
full MCP gateway for resources, prompts, streamable HTTP, auth, sampling,
elicitation, or subscriptions.
