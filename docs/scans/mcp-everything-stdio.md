# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 13 |
| Full tool tax | 1,499 est. tokens |
| Slim index | 598 est. tokens |
| Slim-index savings | 901 est. tokens (60.1%) |
| Worst tool | 278 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `gzip-file-as-resource` | 278 | 57 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/8` |
| `simulate-research-query` | 169 | 52 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/12` |
| `get-annotated-message` | 152 | 48 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/1` |
| `get-resource-reference` | 131 | 47 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/4` |
| `trigger-long-running-operation` | 127 | 49 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/11` |
| `get-structured-content` | 115 | 48 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/5` |
| `get-sum` | 114 | 38 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/6` |
| `get-resource-links` | 112 | 48 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/3` |
| `echo` | 85 | 33 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/0` |
| `toggle-simulated-logging` | 56 | 47 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/9` |
| `get-env` | 54 | 43 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/2` |
| `toggle-subscriber-updates` | 54 | 45 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/10` |
| `get-tiny-image` | 52 | 43 | `mcp-stdio:npx -y @modelcontextprotocol/server-everything/tools/7` |

## What To Do

- Current catalog is small enough, but track it in CI before it grows.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
