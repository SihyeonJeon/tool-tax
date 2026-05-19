# Compared

`tool-tax` is for tool-catalog context cost: MCP tools, JSON/YAML tool
manifests, OpenAPI operations, and CI checks for schema growth.

| Need | Use `tool-tax`? | Notes |
| --- | --- | --- |
| See how many tokens an MCP server exposes at startup | Yes | `tool-tax mcp -- <server>` |
| Replace a large MCP catalog with a lazy schema index | Yes | `tool-tax proxy -- <server>` |
| Fail a PR when tool schemas grow too much | Yes | `tool-tax scan` or `tool-tax diff` |
| Compress normal chat prompts | No | Use a prompt-compression tool instead |
| Measure exact provider billing | No | `tool-tax` uses local estimates |
| Run a full MCP gateway with auth/resources/prompts | No | The proxy only covers stdio `tools/list` and `tools/call` |

## Differentiator

Most token tools focus on prompts and responses. `tool-tax` focuses on the
schema tax paid before the user asks a question: the tool catalog itself.

The lazy proxy makes that difference concrete. A direct MCP server exposes every
upstream tool schema in `tools/list`; `tool-tax proxy` exposes three wrapper
tools and lets the agent fetch full schemas only when needed.

