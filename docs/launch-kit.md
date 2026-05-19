# Launch Kit

Short, factual posts work best for this repo. Do not ask for stars, do not mass
mention maintainers, and do not automate reactions, follows, forks, watches, or
comments. Share only where agent tooling, MCP, context engineering, or CI budget
checks are already on topic.

## One-Line Pitch

`tool-tax doctor` finds the token tax hiding in Claude Code, Cursor, VS Code,
and Cline MCP configs.

## Demo

GIF: `docs/assets/tool-tax-demo.gif`

```bash
pipx install tool-tax
tool-tax doctor --include-global --no-probe
tool-tax doctor --mcp-config .mcp.json
```

```text
Servers: 1
Tools: 14
Full tool tax: 2,102 est. tokens
Slim index: 647 est. tokens
Slim-index savings: 1,455 est. tokens (69.2%)
```

## Short Post

I made `tool-tax`, a small CLI for MCP configs and agent tool catalogs.

The main command is `tool-tax doctor`: it reads Claude Code, Cursor, VS Code,
and Cline MCP configs, safely lists configured servers with `--no-probe`, and
can probe trusted stdio servers with `initialize` + `tools/list` to report the
schema tax before those tools hit context.

Repo: https://github.com/SihyeonJeon/tool-tax

Useful if your local agent setup has a growing MCP list and you want a concrete
number before the catalog silently bloats.

## Show HN-Style Title

Show HN: tool-tax, a CLI that finds hidden token cost in MCP configs

## Technical Post

Most agent repos track model choice, prompt length, and eval scores. Fewer track
the context spent before the first user request: tool schemas.

`tool-tax` gives that cost a number:

- inspect Claude Code, Cursor, VS Code, and Cline MCP configs
- preview user-level configs with `doctor --include-global --no-probe`
- probe trusted MCP stdio servers with `initialize` + `tools/list`
- scan MCP-style JSON/YAML, nested tool manifests, and OpenAPI operations
- rank expensive tools
- produce Markdown/JSON reports
- diff base/head catalogs for pull requests
- fail CI on catalog budget regressions
- post/update a GitHub PR report comment when configured
- generate a small progressive-loading index plus full schema files
- run a stdio proxy that exposes only three wrapper tools up front

The proxy is intentionally narrow: stdio only, `tools/list`, and `tools/call`.
No billing claims and no prompt-compression claims.

Measured examples:

- VS Code-style MCP Filesystem config: 14 tools, 2,102 est. schema tokens
- MCP Filesystem: 2,102 -> 647 est. tokens, 69.2% smaller
- MCP Filesystem through proxy: 2,102 -> 260 est. upfront tokens, 87.6% smaller
- MCP Memory: 1,324 -> 340 est. tokens, 74.3% smaller
- MCP Sequential Thinking: 858 -> 46 est. tokens, 94.6% smaller
- GitHub REST API: 366,962 -> 70,996 est. tokens, 80.7% smaller

## Where To Share Manually

- personal GitHub profile README or pinned repository
- a short demo post in MCP/agent-tooling communities where project links are
  allowed
- Show HN only if the repo has a clear runnable demo
- relevant discussions when someone asks how to measure MCP/tool schema bloat

## Avoid

- star requests
- star-for-star, follow-for-follow, watch/fork/reaction automation
- unsolicited comments in unrelated issues or PRs
- posting the same text across many repos or communities
- claiming real provider savings from the estimator alone
