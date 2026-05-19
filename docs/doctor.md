# Doctor

`tool-tax doctor` inspects MCP config files and reports the tool-schema budget
for each configured stdio server.

It is the quickest way to answer:

- How many tools does this agent config expose?
- Which MCP server contributes the most schema text?
- Would a slim index have high upside?
- Should CI fail when the configured tool surface grows?

## Usage

```bash
tool-tax doctor --mcp-config .mcp.json
tool-tax doctor --mcp-config .cursor/mcp.json --format json
tool-tax doctor --mcp-config .mcp.json --max-tokens 12000
```

Without `--mcp-config`, `doctor` looks for common project files:

- `.mcp.json`
- `mcp.json`
- `.cursor/mcp.json`
- `.vscode/mcp.json`

## Config Shape

`doctor` supports Claude Code/Cursor-style `mcpServers` JSON:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }
}
```

Only stdio servers are probed. URL-based HTTP/SSE servers are reported as
skipped.

## Security Boundary

By default, `doctor` executes the configured stdio server commands so it can
call `initialize` and `tools/list`. Use `--no-probe` to parse config files
without starting any subprocesses:

```bash
tool-tax doctor --mcp-config .mcp.json --no-probe
```

Only probe MCP commands that you trust.
