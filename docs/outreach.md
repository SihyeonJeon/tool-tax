# Outreach

Track legitimate distribution work here. Do not ask for stars, automate
reactions, or post unrelated comments.

## Submissions

| Date | Target | Type | Status | Notes |
| --- | --- | --- | --- | --- |
| 2026-05-20 | [punkpeye/awesome-mcp-devtools](https://github.com/punkpeye/awesome-mcp-devtools) | PR | [open](https://github.com/punkpeye/awesome-mcp-devtools/pull/169) | Added `tool-tax` to Testing Tools as an MCP config/schema-budget linter. |

## Candidate Lists

| Target | Fit | Next action |
| --- | --- | --- |
| `punkpeye/awesome-mcp-devtools` | High | Wait for PR review. Respond only to maintainer feedback. |
| `Puliczek/awesome-mcp-security` | Medium | Only submit if `tool-tax` adds stronger security-audit evidence. Current claim is schema budget, not security. |
| `punkpeye/awesome-mcp-servers` | Low | Do not submit. `tool-tax` is not an MCP server. |
| `punkpeye/awesome-mcp-clients` | Low | Do not submit. `tool-tax` is not an MCP client. |

## Manual Post Draft

```text
I made tool-tax, a small CLI for MCP configs and agent tool catalogs.

The main command is `tool-tax doctor`: it reads Claude Code, Cursor, VS Code,
and Cline MCP configs, safely lists configured servers with `--no-probe`, and
can probe trusted stdio servers with `initialize` + `tools/list` to report the
schema tax before those tools hit context.

Repo: https://github.com/SihyeonJeon/tool-tax
```
