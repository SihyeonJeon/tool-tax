# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 1 |
| Full tool tax | 858 est. tokens |
| Slim index | 46 est. tokens |
| Slim-index savings | 812 est. tokens (94.6%) |
| Worst tool | 858 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `sequentialthinking` | 858 | 46 | `mcp-stdio:npx -y @modelcontextprotocol/server-sequential-thinking/tools/0` |

## What To Do

- Current catalog is small enough, but track it in CI before it grows.
- Split or shorten the heaviest tool schema; one tool exceeds 750 estimated tokens.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
