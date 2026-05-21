# tool-tax

**Find the token tax hiding in your MCP config.**

`tool-tax doctor` reads Claude Code, Cursor, VS Code, and Cline MCP configs,
probes stdio servers with `tools/list`, and shows how much tool-schema text your
agent may load before the user asks a question.

It also scans JSON/YAML tool manifests and OpenAPI files, diffs catalog changes
in CI, writes a slim progressive-loading index, and can test whether a
lazy-schema stdio proxy helps your host.

![tool-tax live MCP demo](https://raw.githubusercontent.com/SihyeonJeon/tool-tax/main/docs/assets/tool-tax-demo.gif)

```bash
pipx install tool-tax

tool-tax doctor --mcp-config .mcp.json
tool-tax doctor --include-global --no-probe
tool-tax scan examples
tool-tax diff old-tools.json new-tools.json
tool-tax pack examples --out .tool-tax
```

Example result:

```text
Servers: 1
Tools: 14
Total tool tax: 2,102 est. tokens
Slim index: 647 est. tokens
Savings: 1,455 est. tokens (69.2%)
```

## Why

Agents keep getting more tools. MCP servers, browser tools, GitHub tools,
database tools, and internal APIs all ship long schemas. If every schema is
loaded up front, your agent pays a context tax before it starts working.

`tool-tax` gives that tax a number and lets CI enforce a budget.

## Install If

- You use Claude Code, Cursor, or another agent with multiple MCP servers.
- You expose internal OpenAPI routes or tool catalogs to an agent.
- You want CI to catch tool-schema bloat before it lands in a pull request.
- You need evidence before claiming that a lazy proxy saves runtime context.

## Do Not Use If

- You need a provider billing meter. `est. tokens` are local estimates.
- You need a full MCP gateway for resources, prompts, streamable HTTP, or auth.
- You are trying to compress normal chat prompts or model responses.

## What It Does

- Finds tool definitions in JSON, YAML, and OpenAPI files.
- Inspects project and user MCP config files for Claude Code, Cursor, VS Code,
  and Cline.
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
pipx install git+https://github.com/SihyeonJeon/tool-tax.git@v0.7.1
```

From a clone:

```bash
git clone https://github.com/SihyeonJeon/tool-tax.git
cd tool-tax
python3 -m pip install -e .
```

Installs one runtime dependency: `PyYAML`.

## Use

Inspect an MCP config:

```bash
tool-tax doctor --mcp-config .mcp.json
tool-tax doctor --mcp-config .cursor/mcp.json --format json
tool-tax doctor --include-global --no-probe
```

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
tool-tax proxy --call-timeout 120 -- npx -y @modelcontextprotocol/server-filesystem /tmp
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
- uses: SihyeonJeon/tool-tax@v0.7.1
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
| Slim-index savings | 835 est. tokens (73.0%) |
| Worst tool | 255 est. tokens |
```

## Supports

- Live MCP stdio servers
- MCP config files with `mcpServers` or VS Code-style `servers`
- Lazy-schema MCP stdio proxy
- MCP-style JSON/YAML tool arrays
- Agent tool manifests with `name`, `description`, and `inputSchema`
- OpenAPI `paths` operations
- OpenAPI slicing by `--tag`, `--path`, and `--operation`
- Nested JSON catalogs
- GitHub Step Summary and PR comment reports

## Benchmarks

These are local estimates for upfront schema text, not provider billing totals.
See [Estimator](docs/estimator.md) for the method and limits.

| Catalog | Tools | Full tool tax | Slim index | Slim-index savings |
| --- | ---: | ---: | ---: | ---: |
| Live MCP Filesystem | 14 | 2,102 | 647 | 69.2% |
| Live MCP Memory | 9 | 1,324 | 340 | 74.3% |
| Live MCP Sequential Thinking | 1 | 858 | 46 | 94.6% |
| GitHub REST API | 1,184 | 366,962 | 70,996 | 80.7% |
| Stripe OpenAPI | 587 | 649,797 | 28,047 | 95.7% |

Direct-vs-proxy upfront schema tax:

| Upstream MCP server | Direct upfront tax | Proxy upfront tax | Reduction |
| --- | ---: | ---: | ---: |
| Filesystem | 2,102 | 260 | 87.6% |
| Memory | 1,324 | 260 | 80.4% |
| Sequential Thinking | 858 | 260 | 69.7% |

Host-level benchmarks:

| Host shape | Result | Link |
| --- | --- | --- |
| VS Code-style MCP config with Filesystem server | doctor reports 14 tools and 2,102 est. schema tokens | [Doctor host config benchmark](docs/doctor-host-config-benchmark.md) |
| Naive host that repeats visible tool schemas in prompts | proxy positive: 90.8% lower startup prompt tokens | [Naive MCP host benchmark](docs/naive-mcp-host-benchmark.md) |
| Claude Code 2.1.143 single known-tool task | proxy negative: one extra turn and higher measured cost | [Claude Code E2E benchmark](docs/claude-code-e2e-benchmark.md) |

## Repo Shape

```text
src/tool_tax/   # library + CLI
tests/          # unittest smoke coverage
examples/       # sample MCP/OpenAPI catalogs and reports
docs/           # usage docs, benchmarks, and public scan reports
```

## What It Is Not

- Not a provider billing meter.
- Not prompt compression for normal chat messages.
- Not a security sandbox for untrusted MCP servers.
- Not a full MCP gateway.
- Not a universal runtime token saver across all agent hosts.

It measures the up-front schema tax, creates a smaller index, catches catalog
growth in CI, and includes an experimental stdio proxy that exposes three
wrapper tools so upstream schemas can be fetched only when needed. The proxy is
intentionally narrow: stdio, `tools/list`, and `tools/call`.

## More

- [Roadmap](ROADMAP.md)
- [Estimator](docs/estimator.md)
- [Compared](docs/compared.md)
- [Changelog](CHANGELOG.md)
- [Doctor](docs/doctor.md)
- [Doctor host config benchmark](docs/doctor-host-config-benchmark.md)
- [Host matrix](docs/host-matrix.md)
- [Naive MCP host benchmark](docs/naive-mcp-host-benchmark.md)
- [Claude Code E2E benchmark](docs/claude-code-e2e-benchmark.md)
- [Public scan gallery](docs/scans/README.md)
- [Proxy benchmark](docs/proxy-benchmark.md)

## License

MIT
