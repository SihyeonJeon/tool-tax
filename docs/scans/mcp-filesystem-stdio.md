# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 14 |
| Full tool tax | 2,102 est. tokens |
| Slim index | 647 est. tokens |
| Slim-index savings | 1,455 est. tokens (69.2%) |
| Worst tool | 242 est. tokens |

## Heaviest Tools

| Tool | Tax | Index | Source |
| --- | ---: | ---: | --- |
| `edit_file` | 242 | 49 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/5` |
| `read_text_file` | 225 | 47 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/1` |
| `search_files` | 203 | 46 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/11` |
| `read_multiple_files` | 174 | 45 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/3` |
| `directory_tree` | 174 | 48 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/9` |
| `list_directory_with_sizes` | 169 | 47 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/8` |
| `read_file` | 146 | 44 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/0` |
| `move_file` | 138 | 47 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/10` |
| `write_file` | 121 | 47 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/4` |
| `list_directory` | 117 | 46 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/7` |
| `create_directory` | 115 | 45 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/6` |
| `get_file_info` | 111 | 42 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/12` |
| `read_media_file` | 86 | 49 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/2` |
| `list_allowed_directories` | 81 | 45 | `mcp-stdio:npx -y @modelcontextprotocol/server-filesystem /tmp/tools/13` |

## What To Do

- Current catalog is small enough, but track it in CI before it grows.
- Progressive loading has high upside for this catalog.
- Use --max-tokens and --max-tool-tokens to catch schema creep in pull requests.
