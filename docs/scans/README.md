# Public Scan Gallery

These reports scan large public OpenAPI catalogs without vendoring the source
files into this repository.

| Catalog | Source | Tools | Full tool tax | Slim index | Potential savings |
| --- | --- | ---: | ---: | ---: | ---: |
| GitHub REST API | https://github.com/github/rest-api-description | 1,184 | 366,962 | 70,996 | 80.7% |
| Stripe OpenAPI | https://github.com/stripe/openapi | 587 | 649,797 | 28,047 | 95.7% |
| Kubernetes OpenAPI | https://github.com/kubernetes/kubernetes | 1,123 | 250,603 | 40,031 | 84.0% |

## Reproduce

```bash
mkdir -p /tmp/tool-tax-public-scans

curl -L https://raw.githubusercontent.com/github/rest-api-description/main/descriptions/api.github.com/api.github.com.json \
  -o /tmp/tool-tax-public-scans/github-rest-api.json
tool-tax scan /tmp/tool-tax-public-scans/github-rest-api.json --out docs/scans/github-rest-api.md

curl -L https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json \
  -o /tmp/tool-tax-public-scans/stripe-openapi.json
tool-tax scan /tmp/tool-tax-public-scans/stripe-openapi.json --out docs/scans/stripe-openapi.md

curl -L https://raw.githubusercontent.com/kubernetes/kubernetes/master/api/openapi-spec/swagger.json \
  -o /tmp/tool-tax-public-scans/kubernetes-openapi.json
tool-tax scan /tmp/tool-tax-public-scans/kubernetes-openapi.json --out docs/scans/kubernetes-openapi.md
```

The estimator is local and approximate. Use these reports to find relative
schema bloat and PR budget regressions, not to claim provider billing totals.
