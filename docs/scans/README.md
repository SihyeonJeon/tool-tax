# Public Scan Gallery

These reports scan live MCP stdio servers and large public OpenAPI catalogs
without vendoring third-party source files into this repository.

Aggregate benchmark:
[10 catalogs, 3,429 tools, 1,442,056 estimated schema tokens](../benchmarks/public-catalogs-2026-05-25.md).
Regenerate it with:

```bash
tool-tax benchmark docs/benchmarks/public-catalogs.yml --out docs/benchmarks/public-catalogs-2026-05-25.md
tool-tax benchmark docs/benchmarks/public-catalogs.yml --format json --out docs/benchmarks/public-catalogs-2026-05-25.json
```

| Catalog | Source | Tools | Full tool tax | Slim index | Slim-index savings |
| --- | --- | ---: | ---: | ---: | ---: |
| MCP Filesystem stdio | https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem | 14 | 2,102 | 647 | 69.2% |
| MCP Filesystem through `tool-tax proxy` | https://www.npmjs.com/package/@modelcontextprotocol/server-filesystem | 3 | 260 | 136 | 47.7% |
| MCP Memory stdio | https://www.npmjs.com/package/@modelcontextprotocol/server-memory | 9 | 1,324 | 340 | 74.3% |
| MCP Sequential Thinking stdio | https://www.npmjs.com/package/@modelcontextprotocol/server-sequential-thinking | 1 | 858 | 46 | 94.6% |
| MCP Sequential Thinking through `tool-tax proxy` | https://www.npmjs.com/package/@modelcontextprotocol/server-sequential-thinking | 3 | 260 | 136 | 47.7% |
| MCP Everything stdio | https://www.npmjs.com/package/@modelcontextprotocol/server-everything | 13 | 1,499 | 598 | 60.1% |
| GitHub REST API | https://github.com/github/rest-api-description | 1,184 | 366,962 | 70,996 | 80.7% |
| GitHub REST API `/repos/` slice | https://github.com/github/rest-api-description | 492 | 168,391 | 28,446 | 83.1% |
| Stripe OpenAPI | https://github.com/stripe/openapi | 587 | 649,797 | 28,047 | 95.7% |
| Kubernetes OpenAPI | https://github.com/kubernetes/kubernetes | 1,123 | 250,603 | 40,031 | 84.0% |

## Reproduce

```bash
mkdir -p /tmp/tool-tax-public-scans

tool-tax mcp \
  --out docs/scans/mcp-filesystem-stdio.md \
  -- npx -y @modelcontextprotocol/server-filesystem /tmp

tool-tax mcp \
  --out docs/scans/mcp-filesystem-proxy.md \
  -- tool-tax proxy -- npx -y @modelcontextprotocol/server-filesystem /tmp

tool-tax mcp \
  --out docs/scans/mcp-memory-stdio.md \
  -- npx -y @modelcontextprotocol/server-memory

tool-tax mcp \
  --out docs/scans/mcp-sequential-thinking-stdio.md \
  -- npx -y @modelcontextprotocol/server-sequential-thinking

tool-tax mcp \
  --out docs/scans/mcp-sequential-thinking-proxy.md \
  -- tool-tax proxy -- npx -y @modelcontextprotocol/server-sequential-thinking

tool-tax mcp \
  --out docs/scans/mcp-everything-stdio.md \
  -- npx -y @modelcontextprotocol/server-everything

curl -L https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json \
  -o /tmp/tool-tax-public-scans/github-rest-api.json
tool-tax scan /tmp/tool-tax-public-scans/github-rest-api.json --out docs/scans/github-rest-api.md
tool-tax scan /tmp/tool-tax-public-scans/github-rest-api.json \
  --path /repos/ \
  --out docs/scans/github-rest-repos-slice.md

curl -L https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json \
  -o /tmp/tool-tax-public-scans/stripe-openapi.json
tool-tax scan /tmp/tool-tax-public-scans/stripe-openapi.json --out docs/scans/stripe-openapi.md

curl -L https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json \
  -o /tmp/tool-tax-public-scans/kubernetes-openapi.json
tool-tax scan /tmp/tool-tax-public-scans/kubernetes-openapi.json --out docs/scans/kubernetes-openapi.md
```

The estimator is local and approximate. Use these reports to find relative
schema bloat and PR budget regressions, not to claim provider billing totals.
