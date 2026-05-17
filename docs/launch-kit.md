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
pipx install git+https://github.com/SihyeonJeon/tool-tax.git
tool-tax scan examples
tool-tax pack examples --out .tool-tax
```

```text
Tools: 5
Full tool tax: 956 est. tokens
Slim index: 236 est. tokens
Potential savings: 720 est. tokens (75.3%)
```

## Short Post

I made `tool-tax`, a small dependency-free CLI for MCP and agent tool catalogs.

It scans JSON/OpenAPI tool definitions, estimates the up-front schema token tax,
ranks the heaviest tools, and writes a slim `tool-index.json` so full schemas can
be loaded later.

Repo: https://github.com/SihyeonJeon/tool-tax

Useful if your agent ships with a growing MCP/tool list and you want a CI check
before the catalog silently bloats.

## Show HN-Style Title

Show HN: tool-tax, a CLI that measures hidden token cost in agent tool catalogs

## Technical Post

Most agent repos track model choice, prompt length, and eval scores. Fewer track
the context spent before the first user request: tool schemas.

`tool-tax` gives that cost a number:

- scan MCP-style JSON, nested tool manifests, and OpenAPI operations
- rank expensive tools
- produce Markdown/JSON reports
- fail CI on catalog budget regressions
- generate a small progressive-loading index plus full schema files

The first release is intentionally narrow: no runtime proxy, no billing claims,
and no prompt-compression claims. It is a measuring tool.

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
