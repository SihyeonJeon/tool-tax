# Launch Kit

Short, factual posts work best for this repo. Do not ask for stars, do not mass
mention maintainers, and do not automate reactions, follows, forks, watches, or
comments. Share only where agent tooling, MCP, context engineering, or CI budget
checks are already on topic.

## One-Line Pitch

`tool-tax` measures the hidden token cost of agent tool catalogs and writes a
smaller progressive-loading index.

## Demo

```bash
pipx install tool-tax
tool-tax scan examples
tool-tax mcp -- npx -y @modelcontextprotocol/server-filesystem /tmp
tool-tax pack examples --out .tool-tax
```

```text
Tools: 7
Full tool tax: 1,144 est. tokens
Slim index: 309 est. tokens
Potential savings: 835 est. tokens (73.0%)
```

## Short Post

I made `tool-tax`, a small CLI for MCP and agent tool catalogs.

It scans JSON/YAML/OpenAPI tool definitions, can probe live MCP stdio servers,
estimates the up-front schema token tax, diffs pull-request changes, and writes
a slim `tool-index.json` so full schemas can be loaded later.

Repo: https://github.com/SihyeonJeon/tool-tax

Useful if your agent ships with a growing MCP/tool list and you want a CI check
before the catalog silently bloats.

## Show HN-Style Title

Show HN: tool-tax, a CLI that measures hidden token cost in agent tool catalogs

## Technical Post

Most agent repos track model choice, prompt length, and eval scores. Fewer track
the context spent before the first user request: tool schemas.

`tool-tax` gives that cost a number:

- scan MCP-style JSON/YAML, nested tool manifests, and OpenAPI operations
- probe live MCP stdio servers with `initialize` + `tools/list`
- rank expensive tools
- produce Markdown/JSON reports
- diff base/head catalogs for pull requests
- fail CI on catalog budget regressions
- post/update a GitHub PR report comment when configured
- generate a small progressive-loading index plus full schema files

The first release is intentionally narrow: no runtime proxy, no billing claims,
and no prompt-compression claims. It is a measuring tool.

Measured examples:

- MCP Filesystem: 2,102 -> 647 est. tokens, 69.2% smaller
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
