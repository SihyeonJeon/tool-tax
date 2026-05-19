# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 9 |
| Full tool tax | 1,324 est. tokens |
| Slim index | 340 est. tokens |
| Potential savings | 984 est. tokens (74.3%) |
| Worst tool | 208 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `delete_relations` | 208 | 35 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/5` |
| `create_entities` | 206 | 36 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/0` |
| `create_relations` | 205 | 45 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/1` |
| `add_observations` | 181 | 38 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/2` |
| `delete_observations` | 177 | 37 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/4` |
| `delete_entities` | 103 | 39 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/3` |
| `open_nodes` | 102 | 38 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/8` |
| `search_nodes` | 96 | 39 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/7` |
| `read_graph` | 46 | 33 | `mcp-stdio:npx -y @modelcontextprotocol/server-memory/tools/6` |

## What To Do

- Current catalog is small enough, but track it in CI before it grows.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
