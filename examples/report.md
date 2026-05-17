# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 7 |
| Full tool tax | 1,144 est. tokens |
| Slim index | 309 est. tokens |
| Potential savings | 835 est. tokens (73.0%) |
| Worst tool | 255 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `github_search_issues` | 255 | 47 | `examples/mcp-tools.json/tools/0` |
| `create_run` | 215 | 49 | `examples/openapi.json/paths//runs/post` |
| `shell_run` | 202 | 48 | `examples/mcp-tools.json/tools/3` |
| `browser_snapshot` | 149 | 45 | `examples/mcp-tools.json/tools/2` |
| `github_create_issue` | 135 | 47 | `examples/mcp-tools.json/tools/1` |
| `docs_read` | 97 | 36 | `examples/mcp-tools.yml/tools/1` |
| `docs_search` | 91 | 37 | `examples/mcp-tools.yml/tools/0` |

## What To Do

- Current catalog is small enough, but track it in CI before it grows.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
