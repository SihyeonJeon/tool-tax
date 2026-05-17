# tool-tax

**See how many tokens your agent tools burn before the user even asks a question.**

`tool-tax` scans MCP-style tool catalogs, JSON/YAML tool manifests, and OpenAPI files.
It shows the full schema cost, ranks the heaviest tools, and writes a slim
tool index for progressive loading.

```bash
pipx install git+https://github.com/SihyeonJeon/tool-tax.git

tool-tax scan examples
tool-tax pack examples --out .tool-tax
```

Example result:

```text
Tools: 5
Full tool tax: 956 est. tokens
Slim index: 236 est. tokens
Potential savings: 720 est. tokens (75.3%)
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
- Generates a slim `tool-index.json` plus separate schema files.
- Fails CI when the tool catalog grows past a budget.

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

No runtime dependencies.

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

## Output

```md
# Tool Tax Report

Grade: **lean**

| Metric | Value |
| --- | ---: |
| Tools | 5 |
| Full tool tax | 956 est. tokens |
| Slim index | 236 est. tokens |
| Potential savings | 720 est. tokens (75.3%) |
| Worst tool | 255 est. tokens |
```

## Supports

- MCP-style JSON and YAML tool arrays
- Agent tool manifests with `name`, `description`, and `inputSchema`
- OpenAPI `paths` operations
- Nested JSON catalogs

YAML support covers common dependency-free MCP-style mappings and lists.

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

It is the measuring tape, not the compressor.

## More

- [Roadmap](ROADMAP.md)
- [Star forecast and comparison set](docs/star-forecast-2026-05-17.md)
- [Launch kit](docs/launch-kit.md)
- [Trend scan](docs/trend-scan-2026-05-17.md)
- [Repo shape scan](docs/repo-shape-scan.md)

## License

MIT
