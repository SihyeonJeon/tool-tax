# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 5 |
| Full tool tax | 956 est. tokens |
| Slim index | 236 est. tokens |
| Potential savings | 720 est. tokens (75.3%) |
| Worst tool | 255 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `github_search_issues` | 255 | 47 | `examples/mcp-tools.json/tools/0` |
| `create_run` | 215 | 49 | `examples/openapi.json/paths//runs/post` |
| `shell_run` | 202 | 48 | `examples/mcp-tools.json/tools/3` |
| `browser_snapshot` | 149 | 45 | `examples/mcp-tools.json/tools/2` |
| `github_create_issue` | 135 | 47 | `examples/mcp-tools.json/tools/1` |

## What To Do

- Keep the slim index in the always-loaded prompt.
- Load full schemas only after the model chooses a tool.
- Split tools whose schema alone costs more than 750 estimated tokens.
- Fail CI when full tool tax grows without a reason.
