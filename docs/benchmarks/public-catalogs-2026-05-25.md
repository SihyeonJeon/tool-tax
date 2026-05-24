# Public Catalog Benchmark

Public MCP/OpenAPI catalog scan benchmark; local estimator only, not provider billing or runtime savings

| Metric | Value |
| --- | ---: |
| Catalogs | 10 |
| Tools | 3,429 |
| Full tool tax | 1,442,056 est. tokens |
| Slim index | 169,423 est. tokens |
| Slim-index savings | 1,272,633 est. tokens (88.3%) |
| Brutal catalogs | 4 |

## Catalogs

| Catalog | Kind | Tools | Full tool tax | Slim index | Savings | Worst tool | Grade |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| MCP Filesystem stdio | mcp | 14 | 2,102 | 647 | 69.2% | 242 | lean |
| MCP Filesystem proxy | mcp-proxy | 3 | 260 | 136 | 47.7% | 103 | lean |
| MCP Memory stdio | mcp | 9 | 1,324 | 340 | 74.3% | 208 | lean |
| MCP Sequential Thinking stdio | mcp | 1 | 858 | 46 | 94.6% | 858 | lean |
| MCP Sequential Thinking proxy | mcp-proxy | 3 | 260 | 136 | 47.7% | 103 | lean |
| MCP Everything stdio | mcp | 13 | 1,499 | 598 | 60.1% | 278 | lean |
| GitHub REST API | openapi | 1,184 | 366,962 | 70,996 | 80.7% | 3,054 | brutal |
| GitHub REST API /repos/ slice | openapi-slice | 492 | 168,391 | 28,446 | 83.1% | 3,054 | brutal |
| Stripe OpenAPI | openapi | 587 | 649,797 | 28,047 | 95.7% | 18,712 | brutal |
| Kubernetes OpenAPI | openapi | 1,123 | 250,603 | 40,031 | 84.0% | 436 | brutal |

## Direct vs Proxy

| Direct catalog | Proxy catalog | Direct tax | Proxy tax | Reduction |
| --- | --- | ---: | ---: | ---: |
| MCP Filesystem stdio | MCP Filesystem proxy | 2,102 | 260 | 87.6% |
| MCP Sequential Thinking stdio | MCP Sequential Thinking proxy | 858 | 260 | 69.7% |

## Notes

- 10 catalogs expose 3,429 tools and 1,442,056 estimated schema tokens.
- A slim index would reduce the benchmark corpus by 88.3% before exact schemas are fetched.
- Stripe OpenAPI is the heaviest catalog in this benchmark.
- 4 catalogs are graded brutal; these need slicing, lazy loading, or CI budgets.
- The largest single-tool schema appears in Stripe OpenAPI at 18,712 estimated tokens.
