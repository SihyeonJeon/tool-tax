# tool-tax

**See how many tokens your agent tools burn before the user even asks a question.**

`tool-tax` scans MCP-style tool catalogs, JSON/YAML tool manifests, and OpenAPI
files. It shows the full schema cost, ranks the heaviest tools, diffs catalog
changes in pull requests, and writes a slim tool index for progressive loading.

```bash
pipx install git+https://github.com/SihyeonJeon/tool-tax.git

tool-tax scan examples
tool-tax diff old-tools.json new-tools.json
tool-tax pack examples --out .tool-tax
```

Example result:

```text
Tools: 7
Full tool tax: 1,144 est. tokens
Slim index: 309 est. tokens
Potential savings: 835 est. tokens (73.0%)
```

## Why

Agents keep getting more tools. MCP servers, browser tools, GitHub tools,
database tools, and internal APIs all ship long schemas. If every schema is
loaded up front, your agent pays a context tax before it starts working.

`tool-tax` gives that tax a number.

## What It Does

- Finds tool definitions in JSON, YAML, and OpenAPI files.
- Estimates token cost for each tool schema.
- Ranks the most expensive tools.
- Diffs base/head catalogs for PR budget checks.
- Generates a slim `tool-index.json` plus separate schema files.
- Fails CI when the tool catalog grows past a budget.
- Posts or updates a GitHub PR report comment when configured.

## Install

From GitHub:

```bash
pipx install git+https://github.com/SihyeonJeon/tool-tax.git
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

Use it as a GitHub Action:

```yaml
- uses: SihyeonJeon/tool-tax@main
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

- MCP-style JSON/YAML tool arrays
- Agent tool manifests with `name`, `description`, and `inputSchema`
- OpenAPI `paths` operations
- Nested JSON catalogs
- GitHub Step Summary and PR comment reports

## Repo Shape

```text
src/tool_tax/   # library + CLI
tests/          # unittest smoke coverage
examples/       # sample MCP/OpenAPI catalogs and reports
docs/           # trend scan and repo structure notes
```

## Claim

This tool does not compress prompts by itself. It measures the up-front schema
tax and creates a smaller index so your agent can load full schemas later.

It is the measuring tape and CI gate, not a runtime MCP proxy. Use it before or
alongside proxy/search tools such as MCP compressors, CLI adapters, and
progressive-disclosure gateways.

## More

- [Roadmap](ROADMAP.md)
- [Public scan gallery](docs/scans/README.md)
- [Star forecast and comparison set](docs/star-forecast-2026-05-17.md)
- [Launch kit](docs/launch-kit.md)
- [Trend scan](docs/trend-scan-2026-05-17.md)
- [Repo shape scan](docs/repo-shape-scan.md)

## License

MIT
