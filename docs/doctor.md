# Doctor

`tool-tax doctor` inspects MCP config files and reports the tool-schema budget
for each configured stdio server.

It is the quickest way to answer:

- How many tools does this agent config expose?
- Which MCP server contributes the most schema text?
- Would a slim index have high upside?
- Does the config contain risky command, env, or filesystem scope patterns?
- Should CI fail when the configured tool surface grows?

## Usage

```bash
tool-tax doctor --mcp-config .mcp.json
tool-tax doctor --mcp-config .cursor/mcp.json --format json
tool-tax doctor --mcp-config .mcp.json --max-tokens 12000
tool-tax doctor --include-global --no-probe
tool-tax doctor --mcp-config .mcp.json --no-probe --fail-on-risk-level high
```

Without `--mcp-config`, `doctor` looks for common project files:

- `.mcp.json`
- `mcp.json`
- `.cursor/mcp.json`
- `.vscode/mcp.json`

With `--include-global`, it also checks common user-level locations:

- `~/.claude.json`
- `~/.cursor/mcp.json`
- `~/.cline/mcp.json`
- `~/.cline/data/settings/cline_mcp_settings.json`
- VS Code user `mcp.json` on macOS/Linux
- Cline VS Code extension `cline_mcp_settings.json` on macOS/Linux

For Claude Code `~/.claude.json`, `doctor` reads the current project entry by
default. Use `--all-projects` if you intentionally want to inspect every
project entry stored in that file.

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

It also supports VS Code-style top-level `servers` JSON.

Only stdio servers are probed. Disabled servers and URL-based HTTP/SSE servers
are reported as skipped.

## Config Risk Lint

`doctor` lints config shape before probing a server. The risk check is local and
works with `--no-probe`.

It flags:

- literal values assigned to sensitive env keys such as `TOKEN`, `SECRET`,
  `PASSWORD`, `API_KEY`, and `COOKIE`;
- shell-eval commands such as `bash -c` or `powershell -Command`;
- shell command chains and pipes;
- unpinned package runners such as `npx -y some-package`;
- filesystem MCP servers scoped to `/`, the user home directory, or the whole
  workspace.

For CI:

```bash
tool-tax doctor --mcp-config .mcp.json --no-probe --fail-on-risk-level medium
```

`--fail-on-risk-level` accepts `low`, `medium`, or `high` and exits with code 2
when the config reaches that severity.

## Host Notes

| Host | Project config | User config | Notes |
| --- | --- | --- | --- |
| Claude Code | `.mcp.json` | `~/.claude.json` | User/local scope may be nested under `projects`. |
| Cursor | `.cursor/mcp.json` | `~/.cursor/mcp.json` | Supports `${workspaceFolder}`, `${userHome}`, and `${env:NAME}` placeholders. |
| VS Code | `.vscode/mcp.json` | user profile `mcp.json` | Uses top-level `servers` instead of `mcpServers`. |
| Cline | manual/project configs vary | `~/.cline/data/settings/cline_mcp_settings.json` | Disabled servers are not probed. |

Sources: [Claude Code MCP](https://code.claude.com/docs/en/mcp),
[Cursor MCP](https://docs.cursor.com/en/context/mcp),
[VS Code MCP configuration](https://code.visualstudio.com/docs/copilot/reference/mcp-configuration),
[Cline configuration](https://docs.cline.bot/getting-started/config).

Example host configs live in [examples/host-configs](../examples/host-configs).

For a real config probe, see the
[Doctor host config benchmark](doctor-host-config-benchmark.md).

For a no-probe config lint sample, see the
[Doctor risk lint sample](benchmarks/doctor-risk-lint-2026-05-25.md).

## Security Boundary

By default, `doctor` executes the configured stdio server commands so it can
call `initialize` and `tools/list`. Use `--no-probe` to parse config files
without starting any subprocesses:

```bash
tool-tax doctor --mcp-config .mcp.json --no-probe
```

Only probe MCP commands that you trust.
