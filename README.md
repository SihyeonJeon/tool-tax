# tool-tax

**See how many tokens your agent tools burn before the user even asks a question.**

`tool-tax` scans MCP-style tool catalogs, JSON/YAML tool manifests, and OpenAPI
files. It can also probe a live MCP stdio server with `tools/list`. It shows
the full schema cost, ranks the heaviest tools, diffs catalog changes in pull
requests, writes a slim tool index for progressive loading, and can run a
small stdio proxy that lazy-loads upstream schemas.

![tool-tax live MCP demo](https://raw.githubusercontent.com/SihyeonJeon/tool-tax/main/docs/assets/tool-tax-demo.gif)

```bash
pipx install tool-tax

tool-tax mcp -- npx -y @modelcontextprotocol/server-filesystem /tmp
tool-tax scan examples
tool-tax diff old-tools.json new-tools.json
tool-tax pack examples --out .tool-tax
```

Example result:

```text
Tools: 14
Full tool tax: 2,102 est. tokens
Slim index: 647 est. tokens
Potential savings: 1,455 est. tokens (69.2%)
```

## Why

Agents keep getting more tools. MCP servers, browser tools, GitHub tools,
database tools, and internal APIs all ship long schemas. If every schema is
loaded up front, your agent pays a context tax before it starts working.

`tool-tax` gives that tax a number.

## What It Does

- Finds tool definitions in JSON, YAML, and OpenAPI files.
- Probes live MCP stdio servers through `initialize` + `tools/list`.
- Estimates token cost for each tool schema.
- Ranks the most expensive tools.
- Diffs base/head catalogs for PR budget checks.
- Generates a slim `tool-index.json` plus separate schema files.
- Runs a stdio proxy with `list_tools`, `get_schema`, and `call_tool` wrappers.
- Fails CI when the tool catalog grows past a budget.
- Posts or updates a GitHub PR report comment when configured.

## Install

From PyPI:

```bash
pipx install tool-tax
```

From GitHub:

```bash
pipx install git+https://github.com/SihyeonJeon/tool-tax.git@v0.5.0
```

From a clone:

```bash
git clone https://github.com/SihyeonJeon/tool-tax.git
cd tool-tax
python3 -m pip install -e .
```

Installs one runtime dependency: `PyYAML`.

## Use

Scan a repo:

```bash
tool-tax scan .
```

Scan a live MCP stdio server:

```bash
tool-tax mcp -- npx -y @modelcontextprotocol/server-filesystem /tmp
tool-tax mcp --pack-out .tool-tax-mcp -- npx -y @modelcontextprotocol/server-memory
```

Run the lazy-schema proxy:

```bash
tool-tax proxy -- npx -y @modelcontextprotocol/server-filesystem /tmp
```

Write Markdown and JSON reports:

```bash
tool-tax scan examples --format md --out tool-tax-report.md
tool-tax scan examples --format json --out tool-tax-report.json
```

Create a progressive-loading pack:

```bash
tool-tax pack examples --out .tool-tax
```

That writes:

```text
.tool-tax/
  tool-index.json       # small always-load index
  schemas/*.json        # full schemas loaded only when needed
```

Fail CI on tool bloat:

```bash
tool-tax scan mcp-tools.json --max-tokens 12000 --max-tool-tokens 750
```

Compare a pull request:

```bash
tool-tax diff base-tools.json head-tools.json --max-delta-tokens 500
```

Slice a large OpenAPI file before scanning or packing:

```bash
tool-tax scan openapi.json --tag payments
tool-tax scan openapi.json --path /v1/payment_intents
tool-tax pack openapi.json --operation "PostPayment*" --out .tool-tax-payments
```

Use it as a GitHub Action:

```yaml
- uses: SihyeonJeon/tool-tax@v0.5.0
  with:
    path: .
    max-tokens: "12000"
    max-tool-tokens: "750"
```

## Output

```md
# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 7 |
| Full tool tax | 1,144 est. tokens |
| Slim index | 309 est. tokens |
| Potential savings | 835 est. tokens (73.0%) |
| Worst tool | 255 est. tokens |
```

## Supports

- Live MCP stdio servers
- Lazy-schema MCP stdio proxy
- MCP-style JSON/YAML tool arrays
- Agent tool manifests with `name`, `description`, and `inputSchema`
- OpenAPI `paths` operations
- OpenAPI slicing by `--tag`, `--path`, and `--operation`
- Nested JSON catalogs
- GitHub Step Summary and PR comment reports

## Benchmarks

| Catalog | Tools | Full tool tax | Slim index | Potential savings |
| --- | ---: | ---: | ---: | ---: |
| Live MCP Filesystem | 14 | 2,102 | 647 | 69.2% |
| `tool-tax proxy` for MCP Filesystem | 3 | 260 | 136 | 47.7% |
| Live MCP Memory | 9 | 1,324 | 340 | 74.3% |
| Live MCP Sequential Thinking | 1 | 858 | 46 | 94.6% |
| GitHub REST API | 1,184 | 366,962 | 70,996 | 80.7% |
| Stripe OpenAPI | 587 | 649,797 | 28,047 | 95.7% |

Direct-vs-proxy upfront schema tax for MCP Filesystem: `2,102 -> 260` estimated
tokens, or **87.6% less upfront tool schema**.

## Repo Shape

```text
src/tool_tax/   # library + CLI
tests/          # unittest smoke coverage
examples/       # sample MCP/OpenAPI catalogs and reports
docs/           # trend scan and repo structure notes
```

## Claim

This tool does not claim provider bill reduction from the estimator alone. It
measures the up-front schema tax, creates a smaller index, and includes an
experimental stdio proxy that exposes three wrapper tools so upstream schemas
can be fetched only when needed.

The proxy is intentionally narrow: stdio, tools/list, and tools/call. It is not
a full MCP gateway for resources, prompts, streamable HTTP, or auth.

## More

- [Roadmap](ROADMAP.md)
- [Public scan gallery](docs/scans/README.md)
- [Proxy benchmark](docs/proxy-benchmark.md)
- [PyPI publish notes](docs/pypi-publish.md)
- [Star forecast and comparison set](docs/star-forecast-2026-05-17.md)
- [Launch kit](docs/launch-kit.md)
- [Trend scan](docs/trend-scan-2026-05-17.md)
- [Repo shape scan](docs/repo-shape-scan.md)

## License

MIT
