# Host Matrix

`tool-tax proxy` is host-specific. It helps when a host exposes full visible
tool schemas to the model prompt. It is weaker when the host already performs
lazy or cached MCP handling.

| Host shape | Evidence | Result |
| --- | --- | --- |
| Naive MCP host that repeats all visible schemas in prompt turns | [Naive MCP host benchmark](naive-mcp-host-benchmark.md) | proxy positive |
| Claude Code 2.1.143, single known filesystem tool task | [Claude Code E2E benchmark](claude-code-e2e-benchmark.md) | proxy negative |
| Cursor | not measured yet | TBD |
| VS Code/Copilot | not measured yet | TBD |
| Cline | not measured yet | TBD |
| Custom internal OpenAPI/tool host | use `tool-tax scan`, `doctor`, or the naive host script | measure first |

The main `tool-tax` value does not depend on proxy success. The stable product
surface is schema-budget observability:

- inspect MCP configs with `tool-tax doctor`;
- scan catalogs with `tool-tax scan`;
- block regressions with `tool-tax diff` and CI budgets;
- benchmark proxy behavior per host before making runtime savings claims.

## Config Coverage

`tool-tax doctor` can inspect the config files most likely to show MCP tool
bloat before it reaches the host:

| Host | Path |
| --- | --- |
| Claude Code project scope | `.mcp.json` |
| Claude Code local/user scope | `~/.claude.json` |
| Cursor project/global | `.cursor/mcp.json`, `~/.cursor/mcp.json` |
| VS Code workspace/user | `.vscode/mcp.json`, user profile `mcp.json` |
| Cline CLI/extension | `~/.cline/data/settings/cline_mcp_settings.json`, extension settings |

Run:

```bash
tool-tax doctor --include-global --no-probe
```

Remove `--no-probe` only after reviewing the commands that will execute.
